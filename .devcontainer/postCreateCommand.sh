#!/bin/bash
set -e  # Exit if any command fails

export DEBIAN_FRONTEND=noninteractive

# Update and install basic prerequisites (including curl, gnupg, apt-transport-https, lsb-release, debconf-utils, and software-properties-common)
apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    apt-transport-https \
    lsb-release \
    debconf-utils \
    software-properties-common

# Import the PostgreSQL repository signing key
curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg

# Add the PostgreSQL repository; $(lsb_release -cs) dynamically inserts your Ubuntu codename (e.g., focal)
echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list

# Add the deadsnakes PPA to install newer Python versions (suppress prompts)
add-apt-repository -y ppa:deadsnakes/ppa

# Update package lists and install required packages
apt-get update && apt-get install -y \
    build-essential \
    libreadline-dev \
    zlib1g-dev \
    flex \
    bison \
    libxml2-dev \
    libxslt1-dev \
    libssl-dev \
    libcurl4-openssl-dev \
    libjson-c-dev \
    git \
    pkg-config \
    libpq-dev \
    postgresql-12=12.2-4 \
    postgresql-client-12=12.2-4 \
    python3.9 \
    python3.9-distutils \
    python3.9-dev \
    locales \
    sudo\
    libmysqlclient-dev \
    mysql-server \
    mysql-client 

# Uncomment the en_US.UTF-8 locale in /etc/locale.gen and generate it
sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && locale-gen en_US.UTF-8

#------------------------------------------------------------------------------
# Fix PostgreSQL authentication for psycopg2:
# 1. Patch pg_hba.conf to use md5 (password) instead of peer for the postgres user.
# 2. Start the cluster briefly to run an ALTER USER command to set a password.
# Note:
# - The default file for PostgreSQL 12 is located in /etc/postgresql/12/main/pg_hba.conf.
#------------------------------------------------------------------------------
echo "Configuring PostgreSQL authentication..."

# Ensure PostgreSQL cluster is initialized (if not already).
pg_ctlcluster 12 main start || pg_createcluster 12 main --start

# Set the postgres password (adjust 'your_new_password' to your desired password).
su - postgres -c "psql -c \"ALTER USER postgres WITH PASSWORD 'your_new_password';\""

# Stop the PostgreSQL cluster.
pg_ctlcluster 12 main stop

# Switch authentication to md5 for the postgres user in pg_hba.conf.
sed -ri 's/^(local\s+all\s+postgres\s+)peer/\1md5/' /etc/postgresql/12/main/pg_hba.conf 

# Restart PostgreSQL service to apply changes.
service postgresql restart
#------------------------------------------------------------------------------

# Configure git user settings
echo "Configuring git user settings..."
git config --global --add safe.directory /workspaces/lambda-tune
git config --global --add safe.directory /workspaces/lambda-tune/job
git config --global user.email "jeseok@dblab.postech.ac.kr"
git config --global user.name "Jeongeum Seok"
git submodule update --init --recursive

# Start PostgreSQL
echo "Starting PostgreSQL..."
service postgresql start

echo "Running TPC-DS loading script..."
bash .devcontainer/tpcds.sh || echo "TPC-DS script failed."

echo "Running JOB loading script..."
bash .devcontainer/job.sh || echo "JOB script failed."

echo "Running TPCH loading script..."
bash .devcontainer/tpch.sh || echo "TPCH script failed."
