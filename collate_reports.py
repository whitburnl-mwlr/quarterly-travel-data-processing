#!/usr/bin/env python3

import json
import os
import shutil

#Take the output folder and the reports folder, and the JSON of who to send it to
def main(base_dir, reports_dir, json_filename):
    with open(json_filename) as json_file:
        teams = json.load(json_file)

        #A set - we only want one folder per recipient
        rcpts = set()

        for team in teams:
            rcpts.add(team["rcpt_to"])

            dest_dir = base_dir + "/" + team["rcpt_to"]
            os.makedirs(dest_dir, exist_ok = True)

            #Copy the team report to the team leader's directory and give it a name
            shutil.copyfile(reports_dir + "/" + team["name"] + "/Extra/All-Team/report.pdf", dest_dir + "/" + team["name"] + ".pdf")

            #Copy the team aggregate report to the team leader's directory and give it a name
            shutil.copyfile(reports_dir + "/" + team["name"] + "/Extra/Aggregate/report.pdf", dest_dir + "/" + team["name"] + " - Aggregate.pdf")

            if len(team["codes"]) > 1:
                for code in team["codes"]:
                    rcpts.add(code["rcpt_to"])

                    dest_dir = base_dir + "/" + code["rcpt_to"]
                    prj_name = code["code"] + " (" + code["name"] + ")"
                    os.makedirs(dest_dir, exist_ok = True)

                    #And copy the project report
                    #Use a - instead of a : because Windows...
                    shutil.copyfile(reports_dir + "/" + team["name"] + "/" + prj_name + "/report.pdf", dest_dir + "/" + team["name"] + " - " + prj_name + ".pdf")

        for rcpt in rcpts:
            #Run zip to zip the folders, and then delete the source folders
            os.system("cd " + base_dir + "; zip -r \"" + rcpt + ".zip\" \"" + rcpt + "\"; rm -r \"" + rcpt + "\"")

        #And copy the whole company report
        shutil.copyfile(reports_dir + "/Extra/All-Company/report.pdf", base_dir + "/Whole Company.pdf")

        #And copy the whole company aggregate report
        shutil.copyfile(reports_dir + "/Extra/Aggregate/report.pdf", base_dir + "/Whole Company - Aggregate.pdf")

if __name__ == "__main__":
    main("Collated", "Reports", "Input/team_prj_rcpt_to.json")
