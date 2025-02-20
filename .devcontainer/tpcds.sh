#!/bin/bash

# Generate TPC-DS data with dsdgen
echo "Generating TPC-DS data..."
pushd DSGen-software-code-4.0.0_final/tools > /dev/null
./dsdgen -scale 1
popd > /dev/null

#########################
## PostgreSQL Loading  ##
#########################
# Check if the database 'tpcds' exists; if not, create it.
echo "Checking for PostgreSQL database 'tpcds'..."
if ! psql -U postgres -tAc "SELECT 1 FROM pg_database WHERE datname='tpcds'" | grep -q 1; then
  echo "Creating PostgreSQL database 'tpcds'..."
  psql -U postgres -c "CREATE DATABASE tpcds;"
fi

# Load schema and constraints into PostgreSQL
echo "Loading schema and constraints into PostgreSQL..."
psql -U postgres -d tpcds -f DSGen-software-code-4.0.0_final/tools/tpcds.sql
psql -U postgres -d tpcds -f DSGen-software-code-4.0.0_final/tools/tpcds_source.sql
psql -U postgres -d tpcds -f DSGen-software-code-4.0.0_final/tools/tpcds_ri.sql

# Create a temporary SQL file for bulk load operations and a temporary directory for processed .dat files
bulk_script="bulk_load.sql"
echo "SET session_replication_role = 'replica';" > "$bulk_script"
tmp_dir=$(mktemp -d)

# Process each .dat file for PostgreSQL loading
for dat_file in DSGen-software-code-4.0.0_final/tools/*.dat; do
    table_name=$(basename "$dat_file" .dat)
    echo "Processing PostgreSQL table: $table_name"
    
    # Copy the .dat file to a temporary file in tmp_dir and remove any trailing pipe characters
    tmp_file="${tmp_dir}/${table_name}_copy.dat"
    cp "$dat_file" "$tmp_file"
    sed -i 's/|$//' "$tmp_file"
    
    # Append the \copy command for this table to the bulk script
    abs_tmp_file=$(realpath "$tmp_file")
    echo "\\copy $table_name FROM '$abs_tmp_file' WITH (FORMAT csv, DELIMITER '|');" >> "$bulk_script"
done

# Re-enable foreign key triggers
echo "SET session_replication_role = 'origin';" >> "$bulk_script"

# Execute the bulk loading operations via psql
echo "Executing bulk load script for PostgreSQL..."
psql -U postgres -d tpcds -f "$bulk_script"

# Clean up temporary files
rm "$bulk_script"
rm -rf "$tmp_dir"

echo "PostgreSQL TPC-DS data load complete."

#########################
##     MySQL Loading   ##
#########################

# Create the MySQL database 'tpcds' if it doesn't exist.
echo "Creating MySQL database 'tpcds'..."
mysql -u root -e "CREATE DATABASE IF NOT EXISTS tpcds;"

# Load schema and constraints into MySQL
echo "Loading schema and constraints into MySQL..."
mysql -u root tpcds < DSGen-software-code-4.0.0_final/tools/tpcds.sql
mysql -u root tpcds < DSGen-software-code-4.0.0_final/tools/tpcds_source.sql
mysql -u root tpcds < DSGen-software-code-4.0.0_final/tools/tpcds_ri.sql

# Enable local infile capability (ensure your MySQL server allows this)
echo "Enabling LOCAL INFILE for MySQL..."
mysql -u root -e "SET GLOBAL local_infile = 1;"

# Load data into MySQL tables from each .dat file
for dat_file in DSGen-software-code-4.0.0_final/tools/*.dat; do
    table_name=$(basename "$dat_file" .dat)
    abs_dat_file=$(realpath "$dat_file")
    echo "Loading MySQL table: $table_name"
    mysql --local-infile=1 -u root tpcds \
        -e "LOAD DATA LOCAL INFILE '$abs_dat_file' INTO TABLE $table_name FIELDS TERMINATED BY '|' LINES TERMINATED BY '\n';"
done

echo "MySQL TPC-DS data load complete."
