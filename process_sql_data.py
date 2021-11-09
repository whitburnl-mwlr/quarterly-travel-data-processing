#!/usr/bin/env python3

import json
import mysql.connector
import os
import sys
import csv

#Formats the query, by adding the where clause
def run_query(cursor, qtr, year, query, where):
    table = f"QuarterlyDataQ{qtr}{year}"
    cursor.execute(query.format(where_clause=where, table_name=table))

#
def process_csv_element(tup, headings):
    lst = []
    for (i, elem) in enumerate(tup):
        #Handle the case where there is no data
        elem = str(elem).replace('&', "\&")
        if elem == "None":
            lst += [elem]
        else:
            #Add units. Use startswith as it is quicker than contains()
            if headings[i].startswith("Percentage"):
                lst += [elem + "\%"]
            elif headings[i].startswith("Average per"):
                lst += ["\$" + elem]
            elif headings[i].startswith("Total Spend") or headings[i].startswith("Total Expenditure") or headings[i].endswith("Fee") or headings[i].endswith("Spend") or headings[i] == "Fare":
                lst += ["\$" + elem]
            elif headings[i].startswith("Total Kilometers"):
                lst += [elem + "km"]
            elif headings[i].startswith("Total CO2"):
                lst += [elem + "kg"]
            else:
                lst += [elem]
    return lst

#
def handle_query(cursor, qtr, year, name, query, where_clause, folder_save_path):
    #Run the query
    run_query(cursor, qtr, year, query["query"], where_clause)

    #Save the query results
    with open(folder_save_path + "/" + query["name"].replace(" ", "-") + (f"-{name}" if name else "") + ".csv", 'w', newline='') as csv_write_file:
        csvwriter = csv.writer(csv_write_file)

        headings = query["headings"]
        csvwriter.writerow(headings)
        for tup in cursor:
            csvwriter.writerow(process_csv_element(tup, headings))

#Generates the aggregate reports
def gen_queries_aggregate(cursor, qtr, year, queries_dict, folder_save_path, prj_codes=None):
    os.makedirs(folder_save_path, exist_ok=True)

    prj_restrict = (("(" + " OR ".join(['OrigPurchaseOrderNo = "' + x + '"' for x in prj_codes]) + ")") if prj_codes is not None else "(1=1)") + " AND (RoomOrIncidental = \"\" OR RoomOrIncidental = \"ROM\")"

    for query in queries_dict:
        table = f"QuarterlyDataQ{qtr}{year}"
        cursor.execute(query["query"].format(table_name=table, where_clause=prj_restrict))

        headings = query["headings"]

        with open(folder_save_path + "/" + query["name"].replace(" ", "-") + ".csv", 'w', newline='') as csv_write_file:
            csvwriter = csv.writer(csv_write_file)
            csvwriter.writerow(headings)
            for tup in cursor:
                csvwriter.writerow(process_csv_element(tup, headings))

#Takes a list of queries, and a list of project codes, and retrieves the data for the codes
def gen_queries(cursor, qtr, year, queries_dict, folder_save_path, prj_codes=None):
    os.makedirs(folder_save_path, exist_ok=True)
    for query in queries_dict:
        #The part of the where clause to make sure we only get the data for the project codes we want
        prj_restrict = ("(" + " OR ".join(['OrigPurchaseOrderNo = "' + x + '"' for x in prj_codes]) + ")") if prj_codes is not None else ""

        #Default case - we don't care about fees etc.
        where_clause = "((RoomOrIncidental = \"\" OR RoomOrIncidental = \"ROM\")" + ((" AND " + prj_restrict) if prj_codes is not None else "") + ")"

        if "fees" in query:
            if query["fees"]:
                #If we *do* care about fees, then generate the query without the RoomOrIncidental stuff
                #Note that if we aren't restricting on project code or fees then we need a always true (1=1) clause
                #Since the query format expects a non null where clause
                where_clause = "(" + prj_restrict + ")" if prj_codes is not None else "(1=1)"

        times = [(qtr, year, None)]

        if "last_qtr" in query:
            if query["last_qtr"]:
                new_year = year - 1 if qtr == 1 else year
                new_qtr = 4 if qtr == 1 else qtr - 1
                times += [(new_qtr, new_year, "LQ")]

        if "last_year" in query:
            if query["last_year"]:
                times += [(qtr, year - 1, "LY")]

        for time in times:
            try:
                handle_query(cursor, time[0], time[1], time[2], query, where_clause, folder_save_path)
            except mysql.connector.errors.ProgrammingError as e:
                print(e)

#Creates the report csv files from the queries and teams list
def gen_report(cursor, qtr, year, queries_dict, queries_aggregate_dict, team, output_folder):
    os.makedirs(output_folder + "/" + team["name"], exist_ok=True)

    #We want to generate a report for the whole team, so we add all of the project codes to this list
    cumulative_codes = []

    #If we only have one project code, then we don't want to bother with a breakdown by project code
    #Since the data will just be the same
    if len(team["codes"]) == 1:
        cumulative_codes = [team["codes"][0]["code"]]
    else:
        for code in team["codes"]:
            prj_code = code["code"]
            cumulative_codes += [prj_code]
            #Run the single project queries
            gen_queries(cursor, qtr, year, queries_dict, output_folder + "/" + team["name"] + "/" + prj_code + " (" + code["name"] + ")", [prj_code])

    #Run the whole team queries
    gen_queries(cursor, qtr, year, queries_dict, output_folder + "/" + team["name"] + "/Extra/All-Team", cumulative_codes)

    #Run the aggregate queries
    gen_queries_aggregate(cursor, qtr, year, queries_aggregate_dict, output_folder + "/" + team["name"] + "/Extra/Aggregate", cumulative_codes)


#Takes the list of teams and codes and the queries and runs them, outputting them to a folder
def main(qtr, year, json_filename, queries_filename, queries_aggregate_filename, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    with mysql.connector.connect(user='travel', host='127.0.0.1', database='travel_data') as cnx:
        with cnx.cursor() as cursor:
            with open(queries_filename) as queries_file:
                queries_dict = json.load(queries_file)
                with open(json_filename) as json_file:
                    team_dict = json.load(json_file)
                    with open(queries_aggregate_filename) as queries_aggregate_file:
                        queries_aggregate_dict = json.load(queries_aggregate_file)

                        #Create the reports for each team
                        for team in team_dict:
                            gen_report(cursor, qtr, year, queries_dict, queries_aggregate_dict, team, output_folder)

                        #Generate the whole company report
                        gen_queries(cursor, qtr, year, queries_dict, output_folder + "/Extra/All-Company")
                        gen_queries_aggregate(cursor, qtr, year, queries_aggregate_dict, output_folder + "/Extra/Aggregate")

if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]), "Input/team_prj_rcpt_to.json", "queries.json", "queries_aggregate.json", "Reports")
