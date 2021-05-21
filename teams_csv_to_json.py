#!/usr/bin/env python3

import csv
import json

#Take an input csv file and generate a JSON file
def main(in_filename, out_filename):
    #The list of teams
    team_list = []
    with open(in_filename) as in_file:
        csvreader = csv.reader(in_file)
        
        #A blank team is taken to be the same as the last populated team
        last_team = ""
        
        for row in csvreader:
            #Split the first column into the project number and project name
            prj = "PRJ" + row[0][:4]
            prj_name = row[0][5:]
            
            #If team is empty then use the last team
            team = row[1] if row[1] else last_team
            
            #The person to send the email to
            ctc = row[2]
            
            #Create a dictionary for this team entry
            code_dict = {"code": prj, "name": prj_name, "rcpt_to": ctc}
            
            if team == last_team:
                #If we have more project codes, just append them to the end of the codes list
                team_list[-1]["codes"] += [code_dict]
            else:
                #If this is a new team, then create a team entry, using the contact person of this first entry as the contact person for the whole team
                team_list += [{"name": team, "rcpt_to": ctc, "codes": [code_dict]}]
            last_team = team
            
    #Save the output file
    with open(out_filename, 'w') as json_file:
        json.dump(team_list, json_file)
        
if __name__ == "__main__":
    main("Input/teams.csv", "Input/team_prj_rcpt_to.json")
