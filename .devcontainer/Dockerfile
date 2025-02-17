FROM ubuntu:20.04

# Install necessary build tools and libraries
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
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
  libjson-c-dev\
  git\
  sudo

WORKDIR /tmp

# Download, build, and install PostgreSQL 12.0
RUN wget https://ftp.postgresql.org/pub/source/v12.0/postgresql-12.0.tar.gz \
  && tar -xzf postgresql-12.0.tar.gz \
  && cd postgresql-12.0 \
  && ./configure --prefix=/usr/local/pgsql \
  && make \
  && make install \
  && adduser --disabled-password --gecos "" postgres \
  && mkdir -p /usr/local/pgsql/data \
  && chown postgres /usr/local/pgsql/data \
  && su postgres -c "/usr/local/pgsql/bin/initdb -D /usr/local/pgsql/data" 

CMD ["su", "postgres", "-c", "/usr/local/pgsql/bin/pg_ctl", "-D" "/usr/local/pgsql/data", "start"]
