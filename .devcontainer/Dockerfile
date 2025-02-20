FROM ubuntu:20.04
ENV DEBIAN_FRONTEND=noninteractive

# Install necessary build tools, libraries, and prerequisites.
# Added lsb-release to satisfy mysql-apt-config pre-dependencies.
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
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
    sudo \
    gnupg \
    debconf-utils \
    apt-transport-https \
    lsb-release \
    pkg-config\
    libmysqlclient-dev\
    software-properties-common\
    libpq-dev
RUN sudo add-apt-repository ppa:deadsnakes/ppa && sudo apt install python3.9\
    python3.9-distutils\
    python3.9-dev

WORKDIR /tmp

# Configure the MySQL APT repository for MySQL 8.0.
RUN wget https://dev.mysql.com/get/mysql-apt-config_0.8.32-1_all.deb && \
    echo "mysql-apt-config mysql-apt-config/select-server select mysql-8.0" | debconf-set-selections && \
    dpkg -i mysql-apt-config_0.8.32-1_all.deb && \
    rm mysql-apt-config_0.8.32-1_all.deb

# Download, compile, and install PostgreSQL 12.0 from source.
RUN wget https://ftp.postgresql.org/pub/source/v12.0/postgresql-12.0.tar.gz && \
    tar -xzf postgresql-12.0.tar.gz && \
    cd postgresql-12.0 && \
    ./configure --prefix=/usr/local/pgsql && \
    make && \
    make install && \
    adduser --disabled-password --gecos "" postgres && \
    mkdir -p /usr/local/pgsql/data && \
    chown postgres /usr/local/pgsql/data && \
    su postgres -c "/usr/local/pgsql/bin/initdb -D /usr/local/pgsql/data" && \
    mkdir -p /var/run/postgresql && \
    chown postgres /var/run/postgresql && \
    sed -i "s|#unix_socket_directories = '/tmp'|unix_socket_directories = '/var/run/postgresql'|" /usr/local/pgsql/data/postgresql.conf

# Update package lists and install MySQL server and client.
RUN apt-get update && apt-get install -y mysql-server mysql-client

# Expose PostgreSQL (5432) and MySQL (3306) default ports.
EXPOSE 5432 3306

# Use the JSON (exec) form so that OS signals are handled correctly.
CMD ["/start.sh"]
