FROM ubuntu:20.04
ENV DEBIAN_FRONTEND=noninteractive

# Update and install basic prerequisites (including curl, gnupg, apt-transport-https, lsb-release, debconf-utils, and software-properties-common)
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    apt-transport-https \
    lsb-release \
    debconf-utils \
    software-properties-common

# Import the PostgreSQL repository signing key
RUN curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg

# Add the PostgreSQL repository; $(lsb_release -cs) dynamically inserts your Ubuntu codename (e.g., focal)
RUN echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list

# Configure the MySQL APT repository for MySQL 8.0.
RUN wget https://dev.mysql.com/get/mysql-apt-config_0.8.32-1_all.deb && \
    echo "mysql-apt-config mysql-apt-config/select-server select mysql-8.0" | debconf-set-selections && \
    dpkg -i mysql-apt-config_0.8.32-1_all.deb && \
    rm mysql-apt-config_0.8.32-1_all.deb

# Add the deadsnakes PPA to install newer Python versions
RUN add-apt-repository ppa:deadsnakes/ppa

# Update package lists and install required packages
RUN apt-get update && apt-get install -y \
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
    libmysqlclient-dev \
    libpq-dev \
    postgresql-12=12.2-4 \
    postgresql-client-12=12.2-4 \
    python3.9 \
    python3.9-distutils \
    python3.9-dev \
    mysql-server \
    mysql-client

# Expose PostgreSQL (5432) and MySQL (3306) default ports.
EXPOSE 5432 3306

# Copy an entrypoint/start script and make it executable.
# Ensure you have a local file named "start.sh" (adjust as needed).
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Use the JSON (exec) form so that OS signals are handled correctly.
CMD ["/start.sh"]
