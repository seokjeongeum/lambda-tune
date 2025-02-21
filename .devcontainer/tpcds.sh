#!/bin/bash

# Generate TPC-DS data with dsdgen
echo "Generating TPC-DS data..."
pushd DSGen-software-code-4.0.0_final/tools > /dev/null
./dsdgen -scale 1
popd > /dev/null

#########################
## PostgreSQL Loading  ##
#########################
echo "Dropping existing PostgreSQL database 'tpcds' (if it exists)..."
sudo -u postgres psql -c "DROP DATABASE IF EXISTS tpcds;"
echo "Creating PostgreSQL database 'tpcds'..."
sudo -u postgres psql -c "CREATE DATABASE tpcds;"

# Load schema and constraints into PostgreSQL
echo "Loading schema and constraints into PostgreSQL..."
sudo -u postgres psql -d tpcds -f DSGen-software-code-4.0.0_final/tools/tpcds.sql
sudo -u postgres psql -d tpcds -f DSGen-software-code-4.0.0_final/tools/tpcds_source.sql

# Create a temporary SQL file for bulk load operations and a temporary directory for processed .dat files
bulk_script="bulk_load.sql"
echo "SET session_replication_role = 'replica';" > "$bulk_script"
tmp_dir=$(mktemp -d)
# Adjust permissions on the temporary directory so that the 'postgres' user can traverse it.
chmod 755 "$tmp_dir"

# Process each .dat file for PostgreSQL loading
for dat_file in DSGen-software-code-4.0.0_final/tools/*.dat; do
    table_name=$(basename "$dat_file" .dat)
    echo "Processing PostgreSQL table: $table_name"
    
    # Copy the .dat file to a temporary file in tmp_dir and remove any trailing pipe characters
    tmp_file="${tmp_dir}/${table_name}_copy.dat"
    cp "$dat_file" "$tmp_file"
    sed -i 's/|$//' "$tmp_file"
    # Set permissions so that the file is globally readable (at least for the postgres user)
    chmod 644 "$tmp_file"
    
    # Append the \copy command for this table to the bulk script
    abs_tmp_file=$(realpath "$tmp_file")
    echo "\\copy $table_name FROM '$abs_tmp_file' WITH (FORMAT csv, DELIMITER '|');" >> "$bulk_script"
done

# Re-enable foreign key triggers
echo "SET session_replication_role = 'origin';" >> "$bulk_script"

# Execute the bulk loading operations via psql
echo "Executing bulk load script for PostgreSQL..."
sudo -u postgres psql -d tpcds -f "$bulk_script"

# Clean up temporary files
rm "$bulk_script"
rm -rf "$tmp_dir"

sudo -u postgres psql -d tpcds -f DSGen-software-code-4.0.0_final/tools/tpcds_ri.sql
echo "PostgreSQL TPC-DS data load complete."
