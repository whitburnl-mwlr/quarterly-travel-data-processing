#!/usr/bin/env python3

import json
import mysql.connector
import os
import csv

#Formats the query, by adding the where clause
def run_query(cursor, query, where):
    cursor.execute(query.format(where_clause=where))

#Takes a list of queries, and a list of project codes, and retrieves the data for the codes
def gen_queries(queries_dict, folder_save_path, cursor, prj_codes=None):
    os.makedirs(folder_save_path, exist_ok=True)
    for query in queries_dict:
        #The part of the where clause to make sure we only get the data for the project codes we want
        prj_restrict = ("(" + " OR ".join(['OrigPurchaseOrderNo = "' + x + '"' for x in prj_codes]) + ")") if prj_codes is not None else ""
        
        #Default case - we don't care about fees etc.
        where_clause = "((RoomOrIncidental = \"\" OR RoomOrIncidental = \"ROM\")" + ((" AND " + prj_restrict) if prj_codes is not None else "") + ")"

        if "flags" in query:
            if query["flags"] == "yes_fees":
                #If we *do* care about fees, then generate the query without the RoomOrIncidental stuff
                #Note that if we aren't restricting on project code or fees then we need a always true (1=1) clause
                #Since the query format expects a non null where clause
                where_clause = "(" + prj_restrict + ")" if prj_codes is not None else "(1=1)"

        #Run the query
        run_query(cursor, query["query"], where_clause)
        
        #Save the query results
        with open(folder_save_path + "/" + query["name"].replace(" ", "-") + ".csv", 'w', newline='') as csv_write_file:
            csvwriter = csv.writer(csv_write_file)
            
            headings = query["headings"]
            
            csvwriter.writerow(headings)
            for tup in cursor:
                lst = []
                for (i, elem) in enumerate(tup):
                    #Handle the case where there is no data
                    #If we don't do this then the report will say we spend $None which looks wrong. $0 is better
                    elem = str(elem)
                    if elem == "None":
                        elem = "0"
                    
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
                csvwriter.writerow(lst)

#Creates the report csv files from the queries and teams list
def gen_report(cursor, queries_dict, team, output_folder):
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
            gen_queries(queries_dict, output_folder + "/" + team["name"] + "/" + prj_code + " (" + code["name"] + ")", cursor, [prj_code])

    #Run the whole team queries
    gen_queries(queries_dict, output_folder + "/" + team["name"], cursor, cumulative_codes)

#Takes the list of teams and codes and the queries and runs them, outputting them to a folder
def main(json_filename, queries_filename, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    with open(json_filename) as json_file:
        team_dict = json.load(json_file)
        
        with open(queries_filename) as queries_file:
            queries_dict = json.load(queries_file)
        
            with mysql.connector.connect(user='travel', host='127.0.0.1', database='travel_data') as cnx:
                with cnx.cursor() as cursor:
                    #Create the reports for each team
                    for team in team_dict:
                        gen_report(cursor, queries_dict, team, output_folder)
                        
                    #Generate the whole company report
                    gen_queries(queries_dict, output_folder, cursor)
    
if __name__ == "__main__":
    main("Input/team_prj_rcpt_to.json", "queries.json", "Reports")
