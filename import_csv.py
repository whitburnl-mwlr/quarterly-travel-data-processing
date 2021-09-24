#!/usr/bin/env python3

import csv
import math
import sys
import json

import mysql.connector

#The column names and data types of all the columns we want to import into MySQL (probably MariaDB) from the CSV file from excel
SQL_DATA = {"UniqueRowID": "INT(10) PRIMARY KEY", "OrigPurchaseOrderNo": "VARCHAR(10)","TravellerName": "VARCHAR(50)", "VendorType": "VARCHAR(30)", "FareType": "VARCHAR(20)", "Market": "VARCHAR(20)", "SupplierName": "VARCHAR(100)", "TicketOrigin": "VARCHAR(10)", "TicketDestination": "VARCHAR(10)", "FolderDestination": "VARCHAR(10)", "GrossExclGST": "DECIMAL(10, 2)", "GST": "DECIMAL(10, 2)", "TotalPayable": "DECIMAL(10, 2)", "CityPair": "VARCHAR(20)", "Quantity": "INT(2)", "IncidentalType": "VARCHAR(50)", "DaysInAdvance": "VARCHAR(10)", "RoomOrIncidental": "VARCHAR(10)"}

EARTH_RADIUS = 6378 #km

#lan, long
def distance(tup_lhs, tup_rhs):
    delta_lambda = abs(tup_lhs[1] - tup_rhs[1])
    delta_sigma = math.acos(math.sin(tup_lhs[0]) * math.sin(tup_rhs[0]) + math.cos(tup_lhs[0]) * math.cos(tup_rhs[0]) * math.cos(delta_lambda))

    return EARTH_RADIUS * delta_sigma

#Take a filename for the csv and city pairs and load it into MySQL.
def main(orca_src_folder, qtr, year, airports_filename, bookingtype_filename, faretype_filename, co2_filename, teams_filename, filter_refunds=True):
    orca_filename = f"{orca_src_folder}/orca_data_q{qtr}_{year}.csv"
    table_name = f"QuarterlyDataQ{qtr}{year}"

    with mysql.connector.connect(user='travel', host='127.0.0.1', database='travel_data') as cnx:
        with cnx.cursor() as cursor:
            cursor.execute("USE travel_data;")
            cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
            cursor.execute("DROP TABLE IF EXISTS CityPairs;")
            cursor.execute("DROP TABLE IF EXISTS BookingTypes;")
            cursor.execute("DROP TABLE IF EXISTS FareTypes;")
            cursor.execute("DROP TABLE IF EXISTS CO2Factor;")
            cursor.execute("DROP TABLE IF EXISTS TeamCodes;")

            #Use a loop to generate the CREATE TABLE query from the SQL_DATA dictionary
            cursor.execute(f"CREATE TABLE {table_name} (" + ", ".join([x + " " + SQL_DATA[x] for x in SQL_DATA]) + ");\n");
            cursor.execute("CREATE TABLE CityPairs (Pair VARCHAR(20) PRIMARY KEY, Distance INT(5));")
            cursor.execute("CREATE TABLE BookingTypes (Incidental VARCHAR(50) PRIMARY KEY, Type VARCHAR(20));")
            cursor.execute("CREATE TABLE FareTypes (Code VARCHAR(20) PRIMARY KEY, Type VARCHAR(50));")
            cursor.execute("CREATE TABLE CO2Factor (Type VARCHAR(20) PRIMARY KEY, Factor DECIMAL(10,6));")
            cursor.execute("CREATE TABLE TeamCodes (Code VARCHAR(20) PRIMARY KEY, NAME VARCHAR(100));")

            airports_dict = {}

            #Load the city pairs and insert it into the TB
            with open(airports_filename, newline='') as csv_airports_file:
                csvreader = csv.reader(csv_airports_file)

                for row in csvreader:
                    iata = row[4]
                    lat = float(row[6])
                    lon = float(row[7])

                    airports_dict[iata] = (lat * math.pi / 180, lon * math.pi / 180)

            city_pairs = []

            with open(orca_filename, newline='') as csv_orca_file:
                csvreader = csv.reader(csv_orca_file)

                #A dictionary that maps column names to the index into the row
                #This ensures that the DB columns have the same order as in the SQL_DATA dictionary
                index_dict = {}
                for row in csvreader:
                    if not index_dict:
                        for (i, el) in enumerate(row):
                            #Remove any spaces from the column names
                            index_dict[el.replace(' ', '')] = i

                        continue

                    #We want to filter out the refunds since we don't care about them yet.
                    #We take a paramater since we *might* want to include them occasionally
                    if filter_refunds:
                        total_payable = float(row[index_dict["TotalPayable"]])
                        if total_payable < 0:
                            continue

                    city_pair = row[index_dict["CityPair"]]

                    if city_pair:
                        if city_pair not in city_pairs:
                            cities = city_pair.split(' ')

                            try:
                                dist = distance(airports_dict[cities[0]], airports_dict[cities[1]])
                                cursor.execute(f'INSERT INTO CityPairs (Pair, Distance) VALUES ("{city_pair}", "{dist}")');
                                city_pairs += [city_pair]
                            except KeyError:
                                print("Below not a valid city pair")
                                print(city_pair)

                    #Form a row to go into the DB
                    data_row = ['"' + row[y] + '"'  for y in [index_dict[x] for x in SQL_DATA.keys()]]
                    cursor.execute(f"INSERT INTO {table_name} (" + ", ".join(SQL_DATA.keys()) + ") VALUES (" + ", ".join(data_row) + ");\n");

            with open(bookingtype_filename, newline='') as csv_bookingtype_file:
                csvreader = csv.reader(csv_bookingtype_file)

                for row in csvreader:
                    key = row[0]
                    booking_type = row[1]
                    cursor.execute(f'INSERT INTO BookingTypes (Incidental, Type) VALUES ("{key}", "{booking_type}")');

            with open(faretype_filename, newline='') as csv_faretype_file:
                csvreader = csv.reader(csv_faretype_file)

                for row in csvreader:
                    key = row[0]
                    fare_type = row[1]
                    cursor.execute(f'INSERT INTO FareTypes (Code, Type) VALUES ("{key}", "{fare_type}")');

            with open(co2_filename, newline='') as csv_co2_file:
                csvreader = csv.reader(csv_co2_file)

                for row in csvreader:
                    key = row[0]
                    factor = float(row[1])
                    cursor.execute(f'INSERT INTO CO2Factor (Type, Factor) VALUES ("{key}", "{factor}")');

            with open(teams_filename, newline='') as teams_file:
                teams = json.load(teams_file)

                for team in teams:
                    for code in team["codes"]:
                        team_code = code["code"]
                        team_name = code["name"]
                        cursor.execute(f'INSERT INTO TeamCodes (Code, Name) VALUES ("{team_code}", "{team_name}");')


        #Commit the transactions
        cnx.commit()

if __name__ == "__main__":
    main(f"Input", int(sys.argv[1]), int(sys.argv[2]), "Input/airports.csv", "Input/booking_types.csv", "Input/fare_types.csv", "Input/co2.csv", "Input/team_prj_rcpt_to.json")
