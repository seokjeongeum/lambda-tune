#!/bin/bash

# Generate TPC-DS data with dsdgen
echo "Generating TPC-DS data..."
pushd DSGen-software-code-4.0.0_final/tools > /dev/null
./dsdgen -sc 10 -ve
popd > /dev/null

#########################
## PostgreSQL Loading  ##
#########################
echo "Dropping existing PostgreSQL database 'tpcds' (if it exists)..."
sudo -u postgres psql -c "DROP DATABASE IF EXISTS tpcds;" || { echo "Error dropping database"; exit 1; }
echo "Creating PostgreSQL database 'tpcds'..."
sudo -u postgres psql -c "CREATE DATABASE tpcds;" || { echo "Error creating database"; exit 1; }

# Load schema and constraints into PostgreSQL
echo "Loading schema and constraints into PostgreSQL..."
sudo -u postgres psql -d tpcds -f DSGen-software-code-4.0.0_final/tools/tpcds.sql || { echo "Error loading schema"; exit 1; }
sudo -u postgres psql -d tpcds -f DSGen-software-code-4.0.0_final/tools/tpcds_source.sql || { echo "Error loading source schema"; exit 1; }

# Create a temporary SQL file for bulk load operations and a temporary directory for processed .dat files
umask 022
bulk_script=$(mktemp)
echo "SET session_replication_role = 'replica';" > "$bulk_script"
# (Do not change ownership yet so we can keep appending to it)

tmp_dir=$(mktemp -d)
chmod 755 "$tmp_dir"

# Process each .dat file for PostgreSQL loading
for dat_file in DSGen-software-code-4.0.0_final/tools/*.dat; do
    if [ ! -f "$dat_file" ]; then
        echo "No .dat files found. Data generation may have failed."
        exit 1
    fi
    
    table_name=$(basename "$dat_file" .dat)
    echo "Processing PostgreSQL table: $table_name"
    
    tmp_file="${tmp_dir}/${table_name}_copy.dat"
    cp "$dat_file" "$tmp_file" || { echo "Error copying $dat_file"; exit 1; }
    sed -i 's/|$//' "$tmp_file"
    chmod 644 "$tmp_file"
    sudo chown postgres:postgres "$tmp_file"
    
    abs_tmp_file=$(realpath "$tmp_file")
    echo "\\copy $table_name FROM '$abs_tmp_file' WITH (FORMAT csv, DELIMITER '|');" >> "$bulk_script"
done

# Re-enable foreign key triggers
echo "SET session_replication_role = 'origin';" >> "$bulk_script"

# Now that writing is complete, adjust permissions and ownership so PostgreSQL can read the file.
chmod 644 "$bulk_script"
sudo chown postgres:postgres "$bulk_script"

# Execute the bulk loading operations via psql
echo "Executing bulk load script for PostgreSQL..."
sudo -u postgres psql -d tpcds -f "$bulk_script" || { echo "Error during bulk load"; exit 1; }

# Clean up temporary files
rm "$bulk_script"
rm -rf "$tmp_dir"

# Add foreign key constraints (ensure that DSGen-software-code-4.0.0_final/tools/tpcds_ri.sql exists and its contents are valid SQL)
sudo -u postgres psql -d tpcds -f DSGen-software-code-4.0.0_final/tools/tpcds_ri.sql || { echo "Error adding constraints"; exit 1; }
echo "PostgreSQL TPC-DS data load complete."
