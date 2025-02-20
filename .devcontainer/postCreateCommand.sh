#!/bin/bash
set -e  # Exit if any command fails

# Configure git user settings
echo "Configuring git user settings..."
git config --global user.email "jeseok@dblab.postech.ac.kr"
git config --global user.name "Jeongeum Seok"

# Start PostgreSQL
echo "Starting PostgreSQL..."
service postgresql start

# Start MySQL in the background
echo "Starting MySQL..."
mysqld_safe &   # Background mysqld_safe so the script can continue

echo "Running TPC-DS loading script..."
bash .devcontainer/tpcds.sh

echo "Running JOB loading script..."
bash .devcontainer/job.sh

echo "Running TPC-H loading script..."
bash .devcontainer/tpch.sh

# Keep the container running by tailing the PostgreSQL logfile
echo "Tailing PostgreSQL logfile..."
exec tail -f logfile
