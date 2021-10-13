# quarterly-travel-data-processing
Tool for processing the quarterly travel data, importing it into MySQL (or MariaDB) and then processing it and then exporting it such that it can be made into a LaTeX report.

Run as `./run.sh <quarter> <year>`. This is to be used in a Windows environment (i.e. via WSL), so it expects files to be saved at `C:\Users\<username>\TravelData`. Input ORCA csv files should have the name `orca_data_q<quarter>_<year>`

Icons from https://github.com/iconic/open-iconic

Todo:
 - Hotel CO2 for aggregate files
