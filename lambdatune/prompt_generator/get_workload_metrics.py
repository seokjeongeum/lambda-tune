#!/usr/bin/env python3
import argparse
import json
import psycopg2
from tqdm import tqdm  # For progress reporting

from lambdatune.benchmarks.job import get_job_queries
from lambdatune.benchmarks.tpcds import get_tpcds_queries
from lambdatune.benchmarks.tpch import get_tpch_queries
from lambdatune.utils import get_dbms_driver
import decimal

def run_workload(benchmark):
    """
    Connects to the PostgreSQL database and executes a list of predefined queries
    to simulate a workload and reports progress.
    """
    driver = get_dbms_driver("POSTGRES", db=benchmark)
    driver.reset_configuration()

    if benchmark == "tpch":
        queries = get_tpch_queries()
    elif benchmark == "tpcds":
        queries = get_tpcds_queries()
    elif benchmark == "job":
        queries = get_job_queries()
    else:
        raise ValueError("Unsupported benchmark type.")

    # Transform queries list assuming each query is contained in a tuple,
    # and the second element ([1]) is the SQL query string.
    query_list = [query[1] for query in queries]

    # Use tqdm to wrap the queries iterator for a progress bar.
    for query in tqdm(query_list, desc="Executing Queries", unit="query"):
        driver.explain(query)


def get_workload_metrics(dbname, user, password, host="localhost", port=5432):
    """
    Connects to the PostgreSQL database and retrieves cumulative workload metrics.
    Metrics are taken from pg_stat_database and pg_stat_bgwriter.
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


def subtract_metrics(post_metrics, baseline_metrics):
    """
    Compute delta values for each metric by subtracting the baseline from post-workload values.
    """
    delta = {}
    for key in post_metrics:
        # Converting to float to handle Decimal types correctly
        delta[key] = float(post_metrics[key]) - float(baseline_metrics.get(key, 0))
    return delta


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script to run benchmarks.")
    parser.add_argument(
        "--benchmark",
        type=str,
        required=True,
        help="Benchmark type (tpch, tpcds, or job)"
    )
    args = parser.parse_args()
    benchmark = args.benchmark.lower()

    # Replace with your actual PostgreSQL connection details.
    dbname = benchmark  # Here the database name is assumed to match the benchmark type.
    user = "postgres"
    password = "your_new_password"  # Update with your PostgreSQL password.
    host = "localhost"
    port = 5432

    # Optionally reset PostgreSQL statistics if you want to start fresh:
    # For example, as a privileged user, you can execute: SELECT pg_stat_reset();

    # 1. Collect baseline metrics before running the workload.
    baseline_metrics = get_workload_metrics(dbname, user, password, host, port)

    # 2. Run the workload.
    run_workload(benchmark)

    # 3. Collect metrics after running the workload.
    post_metrics = get_workload_metrics(dbname, user, password, host, port)

    # 4. Compute the difference (delta) between post-workload and baseline metrics.
    delta_metrics = subtract_metrics(post_metrics, baseline_metrics)

    filename = f"{benchmark}_metrics_baseline.json"
    with open(filename, "w") as f:
        json.dump(baseline_metrics, f, indent=2, default=str)
    # Save the delta metrics to a JSON file named after the benchmark.
    filename = f"{benchmark}_metrics_delta.json"
    with open(filename, "w") as f:
        json.dump(delta_metrics, f, indent=2, default=str)

    print("Workload Delta Metrics:")
    for key, value in delta_metrics.items():
        print(f"{key}: {value}")

    print(f"\nMetrics have been saved to {filename}")
