#!/bin/bash
set -e  # Exit immediately if a command fails

# Check if an argument is passed for dbgen scale; if not, default to 1
SCALE=${1:-1}
echo "Using TPC-H scale factor: ${SCALE}"

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
pushd "TPC-H V3.0.1/dbgen" > /dev/null
cp makefile.postgres makefile
make
./dbgen -scale ${SCALE} -f
popd > /dev/null

echo "Ensuring PostgreSQL database '${DB_NAME}' exists..."
if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1; then
  echo "Creating PostgreSQL database '${DB_NAME}'..."
  sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME};"
else
  echo "PostgreSQL database '${DB_NAME}' already exists. Skipping creation..."
fi

sudo -u postgres psql -d ${DB_NAME} -c "CREATE TABLE IF NOT EXISTS NATION  (
  N_NATIONKEY  INTEGER NOT NULL,
  N_NAME       CHAR(25) NOT NULL,
  N_REGIONKEY  INTEGER NOT NULL,
  N_COMMENT    VARCHAR(152)
);

CREATE TABLE IF NOT EXISTS REGION  (
  R_REGIONKEY  INTEGER NOT NULL,
  R_NAME       CHAR(25) NOT NULL,
  R_COMMENT    VARCHAR(152)
);

CREATE TABLE IF NOT EXISTS PART  (
  P_PARTKEY     INTEGER NOT NULL,
  P_NAME        VARCHAR(55) NOT NULL,
  P_MFGR        CHAR(25) NOT NULL,
  P_BRAND       CHAR(10) NOT NULL,
  P_TYPE        VARCHAR(25) NOT NULL,
  P_SIZE        INTEGER NOT NULL,
  P_CONTAINER   CHAR(10) NOT NULL,
  P_RETAILPRICE DECIMAL(15,2) NOT NULL,
  P_COMMENT     VARCHAR(23) NOT NULL
);

CREATE TABLE IF NOT EXISTS SUPPLIER (
  S_SUPPKEY     INTEGER NOT NULL,
  S_NAME        CHAR(25) NOT NULL,
  S_ADDRESS     VARCHAR(40) NOT NULL,
  S_NATIONKEY   INTEGER NOT NULL,
  S_PHONE       CHAR(15) NOT NULL,
  S_ACCTBAL     DECIMAL(15,2) NOT NULL,
  S_COMMENT     VARCHAR(101) NOT NULL
);

CREATE TABLE IF NOT EXISTS PARTSUPP (
  PS_PARTKEY     INTEGER NOT NULL,
  PS_SUPPKEY     INTEGER NOT NULL,
  PS_AVAILQTY    INTEGER NOT NULL,
  PS_SUPPLYCOST  DECIMAL(15,2)  NOT NULL,
  PS_COMMENT     VARCHAR(199) NOT NULL
);

CREATE TABLE IF NOT EXISTS CUSTOMER (
  C_CUSTKEY     INTEGER NOT NULL,
  C_NAME        VARCHAR(25) NOT NULL,
  C_ADDRESS     VARCHAR(40) NOT NULL,
  C_NATIONKEY   INTEGER NOT NULL,
  C_PHONE       CHAR(15) NOT NULL,
  C_ACCTBAL     DECIMAL(15,2)   NOT NULL,
  C_MKTSEGMENT  CHAR(10) NOT NULL,
  C_COMMENT     VARCHAR(117) NOT NULL
);

CREATE TABLE IF NOT EXISTS ORDERS  (
  O_ORDERKEY       INTEGER NOT NULL,
  O_CUSTKEY        INTEGER NOT NULL,
  O_ORDERSTATUS    CHAR(1) NOT NULL,
  O_TOTALPRICE     DECIMAL(15,2) NOT NULL,
  O_ORDERDATE      DATE NOT NULL,
  O_ORDERPRIORITY  CHAR(15) NOT NULL,  
  O_CLERK          CHAR(15) NOT NULL, 
  O_SHIPPRIORITY   INTEGER NOT NULL,
  O_COMMENT        VARCHAR(79) NOT NULL
);

CREATE TABLE IF NOT EXISTS LINEITEM (
  L_ORDERKEY    INTEGER NOT NULL,
  L_PARTKEY     INTEGER NOT NULL,
  L_SUPPKEY     INTEGER NOT NULL,
  L_LINENUMBER  INTEGER NOT NULL,
  L_QUANTITY    DECIMAL(15,2) NOT NULL,
  L_EXTENDEDPRICE  DECIMAL(15,2) NOT NULL,
  L_DISCOUNT    DECIMAL(15,2) NOT NULL,
  L_TAX         DECIMAL(15,2) NOT NULL,
  L_RETURNFLAG  CHAR(1) NOT NULL,
  L_LINESTATUS  CHAR(1) NOT NULL,
  L_SHIPDATE    DATE NOT NULL,
  L_COMMITDATE  DATE NOT NULL,
  L_RECEIPTDATE DATE NOT NULL,
  L_SHIPINSTRUCT CHAR(25) NOT NULL,
  L_SHIPMODE     CHAR(10) NOT NULL,
  L_COMMENT      VARCHAR(44) NOT NULL
);"

# Load each table only if it is empty (PostgreSQL)
for table in "${TABLES[@]}"; do
  echo "Checking if PostgreSQL table ${table} has data..."
  data_exists=$(sudo -u postgres psql -d ${DB_NAME} -tAc "SELECT 1 FROM ${table} LIMIT 1")
  if [ "$data_exists" != "1" ]; then
    echo "Loading data for ${table} from ${TPCH_DIR}/${table}.tbl..."
    # Remove trailing pipes if present
    sed -i 's/|$//' "${TPCH_DIR}/${table}.tbl"
    sudo -u postgres psql -d ${DB_NAME} -c "\COPY ${table} FROM '${TPCH_DIR}/${table}.tbl' WITH DELIMITER '|' NULL ''"
  else
    echo "Table ${table} already has data. Skipping CSV load for ${table}..."
  fi
done

echo "PostgreSQL TPC-H data load complete."

#############################
# MySQL Loading Section     #
#############################
pushd "TPC-H V3.0.1/dbgen" > /dev/null
cp makefile.mysql makefile
make
./dbgen -scale ${SCALE} -f
popd > /dev/null

echo "Ensuring MySQL database '${DB_NAME}' exists..."
mysql -u root -pyour_new_password -e "CREATE DATABASE IF NOT EXISTS ${DB_NAME};"

mysql -u root -pyour_new_password ${DB_NAME} -e "CREATE TABLE IF NOT EXISTS nation  (
  N_NATIONKEY  INTEGER NOT NULL,
  N_NAME       CHAR(25) NOT NULL,
  N_REGIONKEY  INTEGER NOT NULL,
  N_COMMENT    VARCHAR(152)
);

CREATE TABLE IF NOT EXISTS region  (
  R_REGIONKEY  INTEGER NOT NULL,
  R_NAME       CHAR(25) NOT NULL,
  R_COMMENT    VARCHAR(152)
);

CREATE TABLE IF NOT EXISTS part  (
  P_PARTKEY     INTEGER NOT NULL,
  P_NAME        VARCHAR(55) NOT NULL,
  P_MFGR        CHAR(25) NOT NULL,
  P_BRAND       CHAR(10) NOT NULL,
  P_TYPE        VARCHAR(25) NOT NULL,
  P_SIZE        INTEGER NOT NULL,
  P_CONTAINER   CHAR(10) NOT NULL,
  P_RETAILPRICE DECIMAL(15,2) NOT NULL,
  P_COMMENT     VARCHAR(23) NOT NULL
);

CREATE TABLE IF NOT EXISTS supplier (
  S_SUPPKEY     INTEGER NOT NULL,
  S_NAME        CHAR(25) NOT NULL,
  S_ADDRESS     VARCHAR(40) NOT NULL,
  S_NATIONKEY   INTEGER NOT NULL,
  S_PHONE       CHAR(15) NOT NULL,
  S_ACCTBAL     DECIMAL(15,2) NOT NULL,
  S_COMMENT     VARCHAR(101) NOT NULL
);

CREATE TABLE IF NOT EXISTS partsupp (
  PS_PARTKEY     INTEGER NOT NULL,
  PS_SUPPKEY     INTEGER NOT NULL,
  PS_AVAILQTY    INTEGER NOT NULL,
  PS_SUPPLYCOST  DECIMAL(15,2)  NOT NULL,
  PS_COMMENT     VARCHAR(199) NOT NULL
);

CREATE TABLE IF NOT EXISTS customer (
  C_CUSTKEY     INTEGER NOT NULL,
  C_NAME        VARCHAR(25) NOT NULL,
  C_ADDRESS     VARCHAR(40) NOT NULL,
  C_NATIONKEY   INTEGER NOT NULL,
  C_PHONE       CHAR(15) NOT NULL,
  C_ACCTBAL     DECIMAL(15,2)   NOT NULL,
  C_MKTSEGMENT  CHAR(10) NOT NULL,
  C_COMMENT     VARCHAR(117) NOT NULL
);

CREATE TABLE IF NOT EXISTS orders  (
  O_ORDERKEY       INTEGER NOT NULL,
  O_CUSTKEY        INTEGER NOT NULL,
  O_ORDERSTATUS    CHAR(1) NOT NULL,
  O_TOTALPRICE     DECIMAL(15,2) NOT NULL,
  O_ORDERDATE      DATE NOT NULL,
  O_ORDERPRIORITY  CHAR(15) NOT NULL,  
  O_CLERK          CHAR(15) NOT NULL, 
  O_SHIPPRIORITY   INTEGER NOT NULL,
  O_COMMENT        VARCHAR(79) NOT NULL
);

CREATE TABLE IF NOT EXISTS lineitem (
  L_ORDERKEY    INTEGER NOT NULL,
  L_PARTKEY     INTEGER NOT NULL,
  L_SUPPKEY     INTEGER NOT NULL,
  L_LINENUMBER  INTEGER NOT NULL,
  L_QUANTITY    DECIMAL(15,2) NOT NULL,
  L_EXTENDEDPRICE  DECIMAL(15,2) NOT NULL,
  L_DISCOUNT    DECIMAL(15,2) NOT NULL,
  L_TAX         DECIMAL(15,2) NOT NULL,
  L_RETURNFLAG  CHAR(1) NOT NULL,
  L_LINESTATUS  CHAR(1) NOT NULL,
  L_SHIPDATE    DATE NOT NULL,
  L_COMMITDATE  DATE NOT NULL,
  L_RECEIPTDATE DATE NOT NULL,
  L_SHIPINSTRUCT CHAR(25) NOT NULL,
  L_SHIPMODE     CHAR(10) NOT NULL,
  L_COMMENT      VARCHAR(44) NOT NULL
);"

# Load data for each table only if it is empty in MySQL
for table in "${TABLES[@]}"; do
  echo "Checking if MySQL table ${table} has data..."
  count=$(mysql -u root -pyour_new_password -N -s -e "SELECT COUNT(*) FROM ${table};" ${DB_NAME})
  if [ "$count" -eq 0 ]; then
    echo "Loading data for ${table} from ${TPCH_DIR}/${table}.tbl..."
    mysql --local-infile=1 -u root -pyour_new_password ${DB_NAME} -e "LOAD DATA LOCAL INFILE '${TPCH_DIR}/${table}.tbl' INTO TABLE ${table} FIELDS TERMINATED BY '|' LINES TERMINATED BY '\n';"
  else
    echo "Table ${table} already has data. Skipping CSV load for ${table}..."
  fi
done

echo "MySQL TPC-H data load complete."
