#!/bin/bash

git config --global user.email "jeseok@dblab.postech.ac.kr"
git config --global user.name "Jeongeum Seok"

# Start PostgreSQL as the postgres user and log output
su postgres -c "/usr/local/pgsql/bin/pg_ctl -D /usr/local/pgsql/data -l logfile start"

# Start MySQL in the background
mysqld_safe

cd DSGen-software-code-4.0.0_final/tools
./dsdgen -scale 1 -force
cd ..
cd ..

# PostgreSQL Loading Script
/usr/local/pgsql/bin/psql -U postgres -c "DROP DATABASE tpcds;"
/usr/local/pgsql/bin/psql -U postgres -c "CREATE DATABASE tpcds;"
/usr/local/pgsql/bin/psql -U postgres -d tpcds -f DSGen-software-code-4.0.0_final/tools/tpcds.sql
/usr/local/pgsql/bin/psql -U postgres -d tpcds -f DSGen-software-code-4.0.0_final/tools/tpcds_source.sql
/usr/local/pgsql/bin/psql -U postgres -d tpcds -f DSGen-software-code-4.0.0_final/tools/tpcds_ri.sql
# Create a temporary SQL file for the bulk load operations
bulk_script="bulk_load.sql"
echo "SET session_replication_role = 'replica';" > $bulk_script

# Loop over each .dat file in the TPC-DS data folder
for dat_file in DSGen-software-code-4.0.0_final/tools/*.dat; do
    table_name=$(basename "$dat_file" .dat)
    echo "Processing table: $table_name"
    
    # Create a temporary copy to modify (preserving the original file)
    tmp_file="${table_name}_copy.dat"
    cp "$dat_file" "$tmp_file"
    
    # Remove any trailing pipe characters from each line in the temporary file
    sed -i 's/|$//' "$tmp_file"
    
    # Append the \copy command for the current table to the bulk script
    echo "\\copy $table_name FROM '$tmp_file' WITH (FORMAT csv, DELIMITER '|');" >> $bulk_script
    
    # Remove the temporary file
    rm "$tmp_file"
done

# Re-enable foreign key triggers by switching the replication role back to origin
echo "SET session_replication_role = 'origin';" >> $bulk_script

# Execute the bulk load script in a single psql session
/usr/local/pgsql/bin/psql -U postgres -d tpcds -f $bulk_script

# Optionally, remove the bulk load script if no longer needed
rm $bulk_script


# MySQL Loading Script
mysql -u root -e "CREATE DATABASE IF NOT EXISTS tpcds;"
mysql -u root tpcds < DSGen-software-code-4.0.0_final/tools/tpcds.sql
mysql -u root tpcds < DSGen-software-code-4.0.0_final/tools/tpcds_source.sql
mysql -u root tpcds < DSGen-software-code-4.0.0_final/tools/tpcds_ri.sql
mysql -u root -e "SET GLOBAL local_infile = 1;"
for dat_file in DSGen-software-code-4.0.0_final/tools/*.dat; do
    table_name=$(basename "$dat_file" .dat)
    echo "Loading table: $table_name"
    mysql --local-infile=1 -uroot -e "USE tpcds; LOAD DATA LOCAL INFILE '$dat_file' INTO TABLE $table_name FIELDS TERMINATED BY '|' LINES TERMINATED BY '\n';"
done

# Keep container running by tailing PostgreSQL logfile
tail -f logfile
