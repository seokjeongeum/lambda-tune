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

echo "Checking for PostgreSQL database 'job'..."
if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='job'" | grep -q 1; then
  echo "Creating PostgreSQL database 'job'..."
  sudo -u postgres psql -c "CREATE DATABASE job;"
else
  echo "PostgreSQL database 'job' already exists. Skipping creation..."
fi

# Check if schema is already loaded (using table 'name' as an indicator)
schema_loaded=$(sudo -u postgres psql -d job -tAc "SELECT 1 FROM pg_tables WHERE tablename='name'")
if [ "$schema_loaded" != "1" ]; then
  echo "Loading schema into PostgreSQL database 'job'..."
  sudo -u postgres psql -d job -f job/schema.sql
else
  echo "PostgreSQL schema already loaded. Skipping schema load..."
fi

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
  echo "Checking if PostgreSQL table ${table} has data..."
  data_exists=$(sudo -u postgres psql -d job -tAc "SELECT 1 FROM ${table} LIMIT 1")
  if [ "$data_exists" != "1" ]; then
    echo "Loading csv_files/${table}.csv into PostgreSQL table ${table}..."
    sudo -u postgres psql -d job -c "\copy ${table} FROM 'csv_files/${table}.csv' CSV ESCAPE '\\'"
  else
    echo "Table ${table} already has data. Skipping CSV load for ${table}..."
  fi
done

echo "PostgreSQL JOB data load complete."

#############################
##     MySQL Loading       ##
#############################

# Create the MySQL database 'job' if it doesn't exist.
echo "Ensuring MySQL database 'job' exists..."
mysql -u root -pyour_new_password -e"CREATE DATABASE IF NOT EXISTS job;"

# Check if schema is loaded in MySQL by testing for a known table (e.g. 'name')
schema_exists=$(mysql -u root -D job -sse "SHOW TABLES LIKE 'name'")
if [ -z "$schema_exists" ]; then
  echo "Loading schema into MySQL database 'job'..."
  mysql -u root -pyour_new_password job < job/schema.sql
else
  echo "MySQL schema already loaded. Skipping schema load..."
fi

CSV_DIR="csv_files"

# Load CSV data into MySQL tables only if they are empty
tables=(
  "aka_name" "aka_title" "cast_info" "char_name" "comp_cast_type"
  "company_name" "company_type" "complete_cast" "info_type" "keyword"
  "kind_type" "link_type" "movie_companies" "movie_info" "movie_info_idx"
  "movie_keyword" "movie_link" "name" "person_info" "role_type" "title"
)

for table in "${tables[@]}"; do
  echo "Checking if MySQL table ${table} has data..."
  count=$(mysql -u root -pyour_new_password -N -s -e "SELECT COUNT(*) FROM ${table};" job)
  if [ "$count" -eq 0 ]; then
    echo "Table ${table} is empty. Loading data from ${CSV_DIR}/${table}.csv..."
    mysql --local-infile=1 -u root -pyour_new_password job -e "LOAD DATA LOCAL INFILE '${CSV_DIR}/${table}.csv' INTO TABLE ${table} FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '\"';"
  else
    echo "Table ${table} already has data. Skipping CSV load for ${table}..."
  fi
done

echo "MySQL JOB data load complete."


# Cleanup temporary files
echo "Removing temporary files: load-data.sql and table_list.txt..."
rm -f load-data.sql table_list.txt
