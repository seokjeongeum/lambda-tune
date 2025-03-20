import argparse
import json
import logging
import os
import platform
import time
import psycopg2
from tqdm import tqdm  # Import the tqdm module for progress reporting

from lambdatune.benchmarks.job import get_job_queries
from lambdatune.benchmarks.tpcds import get_tpcds_queries
from lambdatune.benchmarks.tpch import get_tpch_queries
from lambdatune.drivers.postgres import PostgresDriver


def run_workload(dbname, user, password, host="localhost", port=5432, queries=None):
    """
    Connects to the PostgreSQL database and executes a list of predefined queries
    to simulate a workload and reports progress.

    Parameters:
      dbname (str): The name of the database.
      user (str): The username.
      password (str): The password.
      host (str): Database host address (default 'localhost').
      port (int): Database port (default 5432).
      queries (list of str): A list of SQL queries to execute.

    Returns:
      None
    """
    conn = psycopg2.connect(
        dbname=dbname, user=user, password=password, host=host, port=port
    )
    cur = conn.cursor()
    conn.autocommit = True
    cur.execute("ALTER SYSTEM RESET ALL;")
    if platform.system() == "Darwin":
        restart_cmd = "brew services restart postgresql"
    elif platform.system() == "Linux":
        restart_cmd = "echo dbbert | sudo -S service postgresql restart"
    else:
        raise Exception(f"System {platform.system()} is not supported.")
    print("Restarting Postgres")
    os.popen(restart_cmd).read()
    print("Done!")
    while True:
        try:
            conn = psycopg2.connect(
                dbname=dbname, user=user, password=password, host=host, port=port
            )
            break
        except Exception as e:
            c += 1
            if c > 6:
                raise e
            time.sleep(10)

    cur = conn.cursor()
    cur.connection.autocommit = True

    # Use tqdm to wrap the queries iterator for a progress bar.
    for query in tqdm(queries, desc="Executing Queries", unit="query"):
        cur.execute(query)
        conn.commit()

    cur.close()
    conn.close()


def get_workload_metrics(dbname, user, password, host="localhost", port=5432):
    """
    Connects to the PostgreSQL database and retrieves key workload-derived metrics.

    Metrics include:
      - xact_commit, xact_rollback: Transaction commit/rollback counts.
      - blks_read, blks_hit: Disk block I/O statistics.
      - tup_returned, tup_fetched, tup_inserted, conflicts, tup_updated, tup_deleted: Tuple counts.
      - Disk I/O metrics derived from the above values.

    Returns:
      dict: The aggregated metrics.
    """
    block_size = 8192  # Default PostgreSQL block size in bytes

    conn = psycopg2.connect(
        dbname=dbname, user=user, password=password, host=host, port=port
    )
    cur = conn.cursor()

    query = f"""
    SELECT
      sum(xact_commit) AS xact_commit,
      sum(xact_rollback) AS xact_rollback,
      sum(blks_read) AS blks_read,
      sum(blks_hit) AS blks_hit,
      sum(tup_returned) AS tup_returned,
      sum(tup_fetched) AS tup_fetched,
      sum(tup_inserted) AS tup_inserted,
      sum(conflicts) AS conflicts,
      sum(tup_updated) AS tup_updated,
      sum(tup_deleted) AS tup_deleted,
      sum(blks_read) AS disk_read_count,
      sum(blks_read) * {block_size} AS disk_read_bytes,
      COALESCE(
         (SELECT sum(buffers_checkpoint + buffers_clean + buffers_backend) FROM pg_stat_bgwriter),
         0
      ) AS disk_write_count,
      COALESCE(
         (SELECT sum(buffers_checkpoint + buffers_clean + buffers_backend) FROM pg_stat_bgwriter),
         0
      ) * {block_size} AS disk_write_bytes
    FROM pg_stat_database;
    """
    cur.execute(query)
    row = cur.fetchone()
    cur.close()
    conn.close()

    metrics = {
        "xact_commit": row[0],
        "xact_rollback": row[1],
        "blks_read": row[2],
        "blks_hit": row[3],
        "tup_returned": row[4],
        "tup_fetched": row[5],
        "tup_inserted": row[6],
        "conflicts": row[7],
        "tup_updated": row[8],
        "tup_deleted": row[9],
        "disk_read_count": row[10],
        "disk_read_bytes": row[11],
        "disk_write_count": row[12],
        "disk_write_bytes": row[13],
    }
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script to run benchmarks.")
    parser.add_argument(
        "--benchmark",
        type=str,
        required=True,
        help="Benchmark type (tpch, tpcds, or job)",
    )
    args = parser.parse_args()
    benchmark = args.benchmark.lower()
    queries = None

    if benchmark == "tpch":
        queries = get_tpch_queries()
    elif benchmark == "tpcds":
        queries = get_tpcds_queries()
    elif benchmark == "job":
        queries = get_job_queries()
    else:
        raise ValueError("Unsupported benchmark type. Choose from tpch, tpcds, or job.")

    # Replace with your actual PostgreSQL connection details.
    dbname = benchmark
    user = "postgres"
    password = "your_new_password"
    host = "localhost"
    port = 5432

    # Transform queries list assuming each query is contained in a tuple,
    # and the second element ([1]) is the SQL query string.
    query_list = [query[1] for query in queries]

    # Run the workload and display a progress bar while executing the queries.
    run_workload(dbname, user, password, host, port, query_list)

    # Retrieve metrics after running the workload.
    metrics = get_workload_metrics(dbname, user, password, host, port)

    # Save the metrics to a JSON file with the benchmark name.
    filename = f"{benchmark}_metrics.json"
    with open(filename, "w") as f:
        json.dump(metrics, f, indent=2)

    print("Workload Metrics:")
    for key, value in metrics.items():
        print(f"{key}: {value}")

    print(f"\nMetrics have been saved to {filename}")
