#!/bin/bash
export DEBIAN_FRONTEND=noninteractive

# Update and install basic prerequisites
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

# Add the PostgreSQL repository
echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list

# Add the deadsnakes PPA for newer Python versions
add-apt-repository -y ppa:deadsnakes/ppa

# Update package lists
apt-get update

# Install required packages
apt-get install -y \
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
    sudo \
    libmysqlclient-dev \
    mysql-server-8.0 mysql-client 

# Fix locale issues
echo "en_US.UTF-8 UTF-8" > /etc/locale.gen
locale-gen en_US.UTF-8 || true
update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 || true

export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

dpkg-reconfigure --frontend=noninteractive locales || true

#------------------------------------------------------------------------------
# Configure PostgreSQL authentication for psycopg2:
#------------------------------------------------------------------------------
echo "Configuring PostgreSQL authentication..."

# Ensure PostgreSQL cluster is initialized (if not already)
if ! pg_lsclusters | grep -q "12 main"; then
  pg_createcluster 12 main || true
fi

pg_ctlcluster 12 main start || true

# Set the postgres password (replace 'your_new_password' with your desired password)
su - postgres -c "psql -c \"ALTER USER postgres WITH PASSWORD 'your_new_password';\""

# Stop the PostgreSQL cluster
pg_ctlcluster 12 main stop

# Switch authentication to md5 for the postgres user in pg_hba.conf
sed -ri 's/^(local\s+all\s+postgres\s+)peer/\1md5/' /etc/postgresql/12/main/pg_hba.conf 

# Restart PostgreSQL service to apply changes
service postgresql restart || true

#------------------------------------------------------------------------------
# Handle MySQL installation issues:
#------------------------------------------------------------------------------
echo "Configuring MySQL..."

# Bypass policy-rc.d restrictions for service management in containers
cat <<EOF > /usr/sbin/policy-rc.d
#!/bin/sh
exit 0
EOF
chmod +x /usr/sbin/policy-rc.d

# Attempt to configure pending packages.
if ! dpkg --configure -a; then
    echo "dpkg configuration failed. Removing problematic MySQL pre- and post-installation scripts."
    rm -f /var/lib/dpkg/info/mysql-server-8.0.preinst
    rm -f /var/lib/dpkg/info/mysql-server-8.0.postinst
    dpkg --configure -a || true
fi

# Start MySQL service (ignoring errors that may occur due to container restrictions)
service mysql start || true

# Set up a root password for MySQL (replace 'your_mysql_password' with your desired password)
mysql -u root <<EOF || true
ALTER USER 'root'@'localhost' IDENTIFIED WITH 'mysql_native_password' BY 'your_mysql_password';
FLUSH PRIVILEGES;
EOF

rm /usr/sbin/policy-rc.d  # Remove policy override after configuration is complete

#------------------------------------------------------------------------------
# Configure Git settings:
#------------------------------------------------------------------------------
echo "Configuring Git..."
git config --global --add safe.directory /workspaces/lambda-tune
git config --global user.email "jeseok@dblab.postech.ac.kr"
git config --global user.name "Jeongeum Seok"

#------------------------------------------------------------------------------
# Run additional scripts:
#------------------------------------------------------------------------------
echo "Running TPC-DS loading script..."
bash .devcontainer/tpcds.sh || echo "TPC-DS script failed."

echo "Running JOB loading script..."
bash .devcontainer/job.sh || echo "JOB script failed."

echo "Running TPCH loading script..."
bash .devcontainer/tpch.sh || echo "TPCH script failed."
