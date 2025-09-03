#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

#############################
# Download and Extract CSVs #
#############################

if [ -f imdb.tgz ]; then
  echo "imdb.tgz already exists. Skipping download..."
else
  echo "Downloading imdb.tgz..."
  wget -c http://event.cwi.nl/da/job/imdb.tgz
fi

# Create csv_files directory and extract only if not already extracted
if [ -d csv_files ] && [ "$(ls -A csv_files)" ]; then
  echo "CSV files already extracted. Skipping extraction..."
else
  echo "Extracting CSV files to csv_files directory..."
  mkdir -p csv_files
  tar --skip-old-files -zxvf imdb.tgz -C csv_files
fi

#############################
##   PostgreSQL Loading    ##
#############################
sudo -u postgres psql -c "DROP DATABASE IF EXISTS job;"
sudo -u postgres psql -c "CREATE DATABASE job;"
sudo -u postgres psql -d job -f job/schema.sql

# List of JOB tables
tables=(
  "aka_name" "aka_title" "cast_info" "char_name" "comp_cast_type"
  "company_name" "company_type" "complete_cast" "info_type" "keyword"
  "kind_type" "link_type" "movie_companies" "movie_info" "movie_info_idx"
  "movie_keyword" "movie_link" "name" "person_info" "role_type" "title"
)

# Load CSV data into PostgreSQL tables only if empty
for table in "${tables[@]}"
do
  sudo -u postgres psql -d job -c "\copy ${table} FROM 'csv_files/${table}.csv' CSV ESCAPE '\\'"
done

echo "PostgreSQL JOB data load complete."
