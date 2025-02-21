#!/bin/bash
set -e  # Exit if any command fails

#------------------------------------------------------------------------------
# Fix PostgreSQL authentication for psycopg2:
# 1. Patch pg_hba.conf to use md5 (password) instead of peer for the postgres user.
# 2. Start the cluster briefly to run an ALTER USER command to set a password.
# Note:
# - The default file for PostgreSQL 12 is located in /etc/postgresql/12/main/pg_hba.conf.
#------------------------------------------------------------------------------
# Start the PostgreSQL cluster temporarily.
pg_ctlcluster 12 main start 

# Set the postgres password (adjust 'postgres' below to your desired password).
su - postgres -c "psql -c \"ALTER USER postgres WITH PASSWORD 'your_new_password';\"" 

# Stop the PostgreSQL cluster.
pg_ctlcluster 12 main stop

# Switch authentication to md5 for the postgres user in pg_hba.conf.
sed -ri 's/^(local\s+all\s+postgres\s+)peer/\1md5/' /etc/postgresql/12/main/pg_hba.conf 
#------------------------------------------------------------------------------

# Configure git user settings
echo "Configuring git user settings..."
git config --global user.email "jeseok@dblab.postech.ac.kr"
git config --global user.name "Jeongeum Seok"

# # Start PostgreSQL
# echo "Starting PostgreSQL..."
# service postgresql start

# # Start MySQL in the background
# echo "Starting MySQL..."
# mysqld_safe &   # Background mysqld_safe so the script can continue

mysql -u root -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'your_new_password';FLUSH PRIVILEGES;"

echo "Running TPC-DS loading script..."
bash .devcontainer/tpcds.sh

echo "Running JOB loading script..."
bash .devcontainer/job.sh

echo "Running JOB loading script..."
bash .devcontainer/tpch.sh 10
