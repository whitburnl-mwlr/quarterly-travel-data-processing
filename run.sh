#!/usr/bin/bash

git pull

rm -r Reports Collated Input

mkdir Input

cp  /mnt/c/Users/$(whoami)/TravelData/Input/* Input
dos2unix Input/*

./teams_csv_to_json.py
./import_csv.py $1 $2
./process_sql_data.py $1 $2
./generate_latex.py
./collate_reports.py

rm  /mnt/c/Users/$(whoami)/TravelData/Output/*
mkdir  /mnt/c/Users/$(whoami)/TravelData/Output/
cp Collated/* /mnt/c/Users/$(whoami)/TravelData/Output
