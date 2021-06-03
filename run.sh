#!/usr/bin/bash

git pull

rm -r Reports Collated Input

mkdir Input

cp /mnt/Input/* Input
dos2unix Input/*

./teams_csv_to_json.py
./import_csv.py
./process_sql_data.py
./generate_latex.py
./collate_reports.py

rm /mnt/Output/*
cp Collated/* /mnt/Output
