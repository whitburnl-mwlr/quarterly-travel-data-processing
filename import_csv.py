#!/usr/bin/env python3

import csv

import mysql.connector

#The column names and data types of all the columns we want to import into MySQL (probably MariaDB) from the CSV file from excel
SQL_DATA = {"UniqueRowID": "INT(10) PRIMARY KEY", "OrigPurchaseOrderNo": "VARCHAR(10)","TravellerName": "VARCHAR(50)", "VendorType": "VARCHAR(30)", "Market": "VARCHAR(20)", "TicketOrigin": "VARCHAR(10)", "TicketDestination": "VARCHAR(10)", "FolderDestination": "VARCHAR(10)", "GrossExclGST": "DECIMAL(10, 2)", "GST": "DECIMAL(10, 2)", "TotalPayable": "DECIMAL(10, 2)", "CityPair": "VARCHAR(20)", "Quantity": "INT(2)", "IncidentalType": "VARCHAR(50)", "DaysInAdvance": "VARCHAR(10)", "RoomOrIncidental": "VARCHAR(10)"}

#Take a filename for the csv and city pairs and load it into MySQL.
def main(orca_filename, pairs_filename, filter_refunds=True):
    with mysql.connector.connect(user='travel', host='127.0.0.1', database='travel_data') as cnx:           
        with cnx.cursor() as cursor:
            cursor.execute("USE travel_data;")
            cursor.execute("DROP TABLE IF EXISTS QuarterlyData;")
            cursor.execute("DROP TABLE IF EXISTS CityPairs;")
            cursor.execute("DROP TABLE IF EXISTS BookingType;")

            #Use a loop to generate the CREATE TABLE query from the SQL_DATA dictionary
            cursor.execute("CREATE TABLE QuarterlyData (" + ", ".join([x + " " + SQL_DATA[x] for x in SQL_DATA]) + ");\n");
            cursor.execute("CREATE TABLE CityPairs (Pair VARCHAR(20) PRIMARY KEY, Distance INT(5));")
            cursor.execute("CREATE TABLE BookingType (Incidental VARCHAR(50) PRIMARY KEY, Type VARCHAR(20));")
            
            #Add the booking type tables
            cursor.execute('INSERT INTO BookingType (Incidental, Type) VALUES ("Fee - Online Domestic Hotel", "Online")');
            cursor.execute('INSERT INTO BookingType (Incidental, Type) VALUES ("Fee - Online Assisted Domestic Hotel", "Online Assisted")');
            cursor.execute('INSERT INTO BookingType (Incidental, Type) VALUES ("Fee - Offline Domestic Hotel", "Offline")');
            
            cursor.execute('INSERT INTO BookingType (Incidental, Type) VALUES ("Fee - Online Domestic", "Online")');
            cursor.execute('INSERT INTO BookingType (Incidental, Type) VALUES ("Fee - Online Assisted Domestic", "Online Assisted")');
            cursor.execute('INSERT INTO BookingType (Incidental, Type) VALUES ("Fee - Offline Domestic", "Offline")');
            
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
                    
                    #Form a row to go into the DB
                    data_row = ['"' + row[y] + '"'  for y in [index_dict[x] for x in SQL_DATA.keys()]]
                    cursor.execute("INSERT INTO QuarterlyData (" + ", ".join(SQL_DATA.keys()) + ") VALUES (" + ", ".join(data_row) + ");\n");
        
            #Load the city pairs and insert it into the TB
            with open(pairs_filename, newline='') as csv_pairs_file:
                csvreader = csv.reader(csv_pairs_file)
                
                for row in csvreader:
                    key = row[0]
                    dist = int(row[1])
                    cursor.execute(f'INSERT INTO CityPairs (Pair, Distance) VALUES ("{key}", "{dist}")');
        
        #Commit the transactions
        cnx.commit()

if __name__ == "__main__":
    main("Input/orca_data.csv", "Input/city_pairs.csv")#, False)
