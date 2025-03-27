#!/bin/bash
set -e  # Exit immediately if a command fails

# Define the dataset directory and TPC-H table names
TPCH_DIR="TPC-H V3.0.1/dbgen"
TABLES=(
  "customer"
  "orders"
  "lineitem"
  "part"
  "partsupp"
  "supplier"
  "nation"
  "region"
)

DB_NAME="tpch"

#############################
# PostgreSQL Loading Section#
#############################
pushd "${TPCH_DIR}" > /dev/null
# Clean and rebuild to avoid potential issues
make clean
make
# Generate data with force flag
./dbgen -s 10 -vf
popd > /dev/null

# Drop and create database
echo "Dropping existing PostgreSQL database '${DB_NAME}' (if it exists)..."
sudo -u postgres psql -c "DROP DATABASE IF EXISTS ${DB_NAME};"  
echo "Creating PostgreSQL database '${DB_NAME}'..."
sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME};"

# Create tables
echo "Creating tables in PostgreSQL..."
sudo -u postgres psql -d tpch -f "TPC-H V3.0.1/dbgen/dss.ddl"


# Create temporary directory for processed files
tmp_dir=$(mktemp -d)
chmod 755 "$tmp_dir"

# Process and load each table
for table in "${TABLES[@]}"; do
  echo "Loading data for ${table} from ${TPCH_DIR}/${table}.tbl..."
  
  # Check if the file exists
  if [ ! -f "${TPCH_DIR}/${table}.tbl" ]; then
    echo "Error: ${TPCH_DIR}/${table}.tbl does not exist. Data generation may have failed."
    exit 1
  fi
  
  # Copy to temp location and process
  tmp_file="${tmp_dir}/${table}.tbl"
  cp "${TPCH_DIR}/${table}.tbl" "$tmp_file"
  sed -i 's/|$//' "$tmp_file"
  chmod 644 "$tmp_file"
  
  # Load data
  sudo -u postgres psql -d ${DB_NAME} -c "\COPY ${table} FROM '${tmp_file}' WITH DELIMITER '|' NULL ''"
done

# Clean up temporary files
rm -rf "$tmp_dir"
echo "PostgreSQL TPC-H data load complete."
