#!/usr/bin/env python3

import os
import json

#Write a latex file which incorporates the csv data
def do_csv(title, basedir, queries):
    with open(basedir + "/report.tex", 'w') as latex_file:
        #Header to include packages and set the author etc.
        latex_file.write(r"""
        \documentclass[a4paper]{article}
        \usepackage[margin=1.5cm]{geometry}
        \usepackage[T1]{fontenc}
        \usepackage{graphicx}
        \usepackage{pgfplotstable}
        \usepackage{longtable}
        \usepackage{tabu}
        \newcolumntype{R}{>{\rightline\arraybackslash}p{0.12\textwidth}}
        \newcolumntype{L}{>{\arraybackslash}p{0.12\textwidth}}
        \usepackage[space]{grffile}
        \renewcommand{\familydefault}{\sfdefault}
        \author{Trudi Sunitsch & Brian Kueh}
        """)
        
        #Generate the title
        latex_file.write(r"\title{\includegraphics[width=0.5\textwidth]{" + os.getcwd() + r"/mwlr_logo}~\\[1cm] {\Large Team Travel Report for} \\" + title.replace("&", "\&") + "}\n")
        latex_file.write(r"""
        \begin{document}
        \maketitle
        """)
        
        for query in queries:
            heading_name = query["name"]
            
            #Determine the csv filename from the query name
            filename = heading_name.replace(" ", "-") + ".csv"
            
            headings = query["headings"]
            
            #Create a new heading
            latex_file.write(r"\section*{" + heading_name + "}\n")
            
            with open(basedir + "/" + filename) as csv_file:
                csv_file_lines = csv_file.readlines()
                
                #If we have data...
                if len(csv_file_lines) > 1:
                    #Special case for the total CO2, total travel, total spend etc.
                    if len(headings) == 1:
                        if headings[0] == "Total Kilometers Travelled":
                            heading_icon = "travel_icon"
                        elif headings[0] == "Total Expenditure":
                            heading_icon = "money_icon"
                        elif headings[0] == "Total CO2 Emissions":
                            headings[0] = headings[0].replace("CO2", r"CO\textsubscript{2}")
                            heading_icon = "co2_icon"
                        else:
                            #Use default icon to make pdflatex not complain
                            heading_icon = "mwlr_logo"

                        #Trim the newline character
                        data = csv_file_lines[-1]
                        
                        #Write the graphics and text
                        latex_file.write(r"\begin{center}" + "\n" + r"\includegraphics[width=0.1\textwidth]{" + os.getcwd() + "/" + heading_icon + "}" + "\n"r"\end{center}" + "\n")
                        latex_file.write(r"\begingroup" + "\n" + r"\LARGE" + "\n")
                        latex_file.write(r"\centerline{" + data[:-1] + "}\n")
                        latex_file.write(r"\endgroup" + "\n")
                    else:
                        #Include the table as a fairly unpleasant LaTeX command
                        display_column_style = ""
                        
                        #Attempt to set the column style
                        for (i, heading) in enumerate(headings):
                            if i == 0:
                                col_type = r"|r|"
                            elif i == len(headings) - 1:
                              col_type = r"l|"
                            else:
                             col_type = r"l"
                            
                            if heading.startswith("Number") or heading.startswith("Percent"):
                                col_type = col_type.replace("l", "L").replace("r", "R")
                            
                            display_column_style += r"display columns/" + str(i) + r"/.style={column type={" + col_type + "}},"
                        
                        base_table_incl = r"\pgfplotstabletypeset[col sep=comma, string type, begin table=\begin{longtabu} to \linewidth, end table=\end{longtabu}, every head row/.style={before row=\hline,after row=\hline}, every last row/.style={after row=\hline}, " + display_column_style + "]{" + filename + "}"
                        latex_file.write(base_table_incl + "\n")
                else:
                    #If there is no data then write that
                    latex_file.write(r"\begingroup" + "\n" + r"\LARGE" + "\n")
                    latex_file.write(r"\centerline{No data this quarter}" + "\n")
                    latex_file.write(r"\endgroup" + "\n")

        latex_file.write(r"\end{document}" + "\n")
        
    #Print what we are doign
    print(basedir)
    
    #Run pdflatex in batch mode to make it quiet
    os.system("cd \"" + basedir + "\"; pdflatex -interaction=batchmode report.tex; rm report.tex; rm report.aux; rm report.log; cd -")
            
#Takes a reports directory, and the filename of the queries file, and generates some LaTeX
def main(basedir, queries_filename):
    with open(queries_filename) as queries_file:
        queries = json.load(queries_file)
    
    #Generate the latex for the whole company report
    do_csv("All of MWLR", basedir, queries)

    #Go through each team...
    for folder in next(os.walk(basedir))[1]:
        #And generate the team report
        do_csv(folder, basedir + "/" + folder, queries)
        
        #And then go through each project and generate the project report
        for folder_next in next(os.walk(basedir + "/" + folder), queries)[1]:
            do_csv(folder + ": " + folder_next, basedir + "/" + folder + "/" + folder_next, queries)
            
    print("Done!")


if __name__ == "__main__":
    main("Reports", "queries.json")
