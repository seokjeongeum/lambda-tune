#!/bin/bash

git config --global user.email "jeseok@dblab.postech.ac.kr"
git config --global user.name "Jeongeum Seok"

# Start PostgreSQL as the postgres user and log output
su postgres -c "/usr/local/pgsql/bin/pg_ctl -D /usr/local/pgsql/data -l logfile start"

# Start MySQL in the background
mysqld_safe

# Keep container running by tailing PostgreSQL logfile
tail -f logfile