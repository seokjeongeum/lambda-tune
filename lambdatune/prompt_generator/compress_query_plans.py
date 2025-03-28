import json
import logging
import os.path
import pprint
import sys
import time
from collections import defaultdict

from lambdatune.benchmarks import *
from lambdatune.drivers import Driver
from lambdatune.plan_utils.postgres_plan_utils import PostgresPlan
from lambdatune.plan_utils import JoinCollectorVisitor
from lambdatune.utils import get_dbms_driver

from lambdatune.llm import get_config_recommendations_with_compression, get_config_recommendations_with_full_queries

from lambdatune.prompt_generator.ilp_solver import ILPSolver


def group_join_conditions(join_conditions):
    joins = defaultdict(list)
    for cond in join_conditions:
        split = cond[0].split(" = ")

        if len(split) < 2:
            continue

        left = split[0]
        right = split[1]
        joins[left].append([right, cond[2], cond[3]])

    return joins


def generate_conditions(benchmark: str, dbms: str, num_tokens: int, db:str):
    logging.info(f"Generating conditions for {benchmark} on {dbms}")
    driver = get_dbms_driver("POSTGRES", db=db)

    schema = driver.get_db_schema()

    init_queries = dict(get_job_queries() if benchmark == "job" else get_tpch_queries())

    queries = [(q[0], driver.explain(q[1], explain_json=True, execute=False)) for q in init_queries.items()]
    queries = [(q[0], PostgresPlan(q[1])) for q in queries]
    collector = JoinCollectorVisitor(schema)

    for p in list(queries):
        p[1].root.accept(collector)

    sql_queries = [init_queries[q[0]] for q in list(queries)]

    collector.resolve_aliases()

    rel_names = collector.relations
    conditions = [[d, collector.join_conditions[d], collector.join_cost_estimations[d]] for d in collector.join_conditions]
    grouped_conditions = group_join_conditions(conditions)

    num_tokens = num_tokens
    solver = ILPSolver()
    start_time = time.time()
    grouped_optimized = solver.optimize_with_dependencies(grouped_conditions, num_tokens)
    elapsed = time.time() - start_time
    logging.info(f"solver.optimize_with_dependencies ran in {elapsed:.3f} seconds")

    return grouped_optimized


def get_prompt(system: str, join_conditions: dict, temperature: float):

    print("Getting prompt with conditions: ", join_conditions)
    prompt = get_config_recommendations_with_compression(dst_system=system, join_conditions=join_conditions, relations=[],
                                                         temperature=temperature, retrieve_response=False)

    return prompt


def get_configurations(prompt: str):
    return get_config_recommendations_with_compression(prompt)


def get_queries(benchmark: str):
    queries = None
    if benchmark == "job":
        queries = dict(get_job_queries() )
    elif benchmark == "tpch":
        queries = dict(get_tpch_queries())
    elif benchmark == "tpcds":
        queries = dict(get_tpcds_queries())

    return queries


def extract_conditions(driver, queries):
    schema = driver.get_db_schema()
    plans = list()
    c = 0
    for q in queries:
        query_id = q[0]
        plan = driver.explain(q[1], explain_json=True, execute=False)

        if plan:
            plans.append((query_id, plan))
            c += 1

    postgres_plans = list()

    for plan in plans:
        query_id = plan[0]

        try:
            pg_plan = PostgresPlan(plan[1])
        except Exception as e:
            logging.warning(f"Exception thrown while processing {query_id}")
            logging.warning(f"Parsing exception: {e}")
            logging.warning(f"Plan: {plan[1]}")
            continue

        postgres_plans.append((query_id, pg_plan,plan[1]['plan']['Plan']['Total Cost']))

    collector = JoinCollectorVisitor(db_schema = schema)

    for p in list(postgres_plans):
        p[1].root.accept(collector,p[2])

    collector.resolve_aliases()

    conditions = [[d, collector.join_conditions[d], collector.join_cost_estimations[d],collector.query_costs[d]] for d in collector.join_conditions]

    for idx, condition in enumerate(conditions):
        cond = condition[0]

        left_tbl, left_col = cond.split(" = ")[0].split(".")
        right_tbl, right_col = cond.split(" = ")[1].split(".")

        left_cond = left_tbl in schema and left_col in schema[left_tbl]
        right_cond = right_tbl in schema and right_col in schema[right_tbl]

        left_operand = f"{left_tbl}.{left_col}" if left_cond else "--"
        right_operand = f"{right_tbl}.{right_col}" if right_cond else "--"

        conditions[idx] = [f"{left_operand} = {right_operand}", condition[1], condition[2], condition[3]]

    return conditions,[(x[0],x[1],'filter') for x in sorted(collector.filters.items(),key=lambda x:x[1],reverse=True)],defaultdict(lambda: float('inf'), {x[0]: x[2] for x in postgres_plans}),postgres_plans


def hide_table_column_names(compressed_columns):
    # Hide table/cols
    columns = dict()
    tables = dict()
    fake_compressed = dict()
    idx = 0

    result = dict()

    for left_tbl_col in compressed_columns:
        left_table = left_tbl_col.split(".")[0]
        left_col = left_tbl_col.split(".")[1]

        if left_table not in tables:
            tbl_fake_name = f"tbl_{idx}"
            idx += 1
            tables[tbl_fake_name] = left_table

        if left_col not in columns:
            col_fake_name = f"col_{idx}"
            idx += 1
            columns[col_fake_name] = left_col

        left_key = f"{tbl_fake_name}.{col_fake_name}"

        if left_key not in fake_compressed:
            fake_compressed[left_key] = list()

        for right_tbl_col in compressed_columns[left_tbl_col]:
            right_table = right_tbl_col.split(".")[0]
            right_col = right_tbl_col.split(".")[1]

            if right_table not in tables:
                tbl_fake_name = f"tbl_{idx}"
                idx += 1
                tables[tbl_fake_name] = right_table

            if right_col not in columns:
                col_fake_name = f"col_{idx}"
                idx += 1
                columns[col_fake_name] = right_col

            right_key = f"{tbl_fake_name}.{col_fake_name}"

            fake_compressed[left_key].append(right_key)

    return fake_compressed, tables, columns


def get_configurations_with_full_queries():
    # queries = queries
    q = list(queries.values())
    num_rounds = 3

    for i in range(0, num_rounds):
        for j in range(0, 5):
            dir = f"../configs/{benchmark}_{system}_full_queries_{i+1}/"
            if not os.path.exists(dir):
                os.mkdir(dir)

            temperature = 0.35
            if j == 0:
                temperature = 0

            doc = get_config_recommendations_with_full_queries(dst_system="postgres", queries=q,
                                                         temperature=temperature,
                                                         retrieve_response=True,
                                                         system_specs={"memory": "61GiB", "cores": 8})

            path = f"../configs/{dir}/config_{benchmark}_FULL_QUERIES_indexes_temp_{temperature}_{int(time.time())}.json"
            json.dump(doc, open(path, "w+"), indent=2)


def get_configurations_with_compression_hidden_columns():
    token_budget = 2000

    conditions = extract_conditions(driver, queries.items())
    grouped_conditions = group_join_conditions(conditions)

    indexes = True
    solver = ILPSolver()
    start_time = time.time()
    optimized_with_dependencies = solver.optimize_with_dependencies(grouped_conditions, token_budget)
    elapsed = time.time() - start_time
    logging.info(f"solver.optimize_with_dependencies ran in {elapsed:.3f} seconds")
    hidden_cols, tables, columns = hide_table_column_names(optimized_with_dependencies)

    for i in range(0, 1):
        for j in range(0, 1):
            dir = f"../configs/{benchmark}_{system}_hidden_compression_tokens_{token_budget}_{i+1}"

            if not os.path.exists(dir):
                os.mkdir(dir)

            for i in range(0, 5):
                temp = 0 if i == 0 else 0.35
                doc = get_config_recommendations_with_compression(dst_system="postgres",
                                                                  relations=None,
                                                                  temperature=temp,
                                                                  retrieve_response=True,
                                                                  join_conditions=hidden_cols,
                                                                  system_specs={"memory": "61GiB", "cores": 8},
                                                                  indexes=True)
                doc["hidden_table_cols"] = {
                    "tables": tables,
                    "columns": columns
                }

                path = f"../configs/{dir}/config_{benchmark}_tokens_{token_budget}_COMPRESSED_JOIN_CONDITIONS_indexes_temp_{temp}_{int(time.time())}.json"
                json.dump(doc, open(path, "w+"), indent=2)

                print("Done: " + path)

import re

def analyze_sql_queries(queries):
    """
    Analyze a list of SQL query strings to compute several metrics.

    Metrics computed:
      - Table access frequency: counts the occurrences of each table in FROM, JOIN, and INTO clauses.
      - Total number of SQL statements.
      - Read and write operation counts and read/write ratio:
          Read operations are assumed to be queries starting with 'SELECT'
          Write operations are assumed to be queries starting with 'INSERT', 'UPDATE', 'DELETE', or 'MERGE'.
      - Average number of predicates per SQL query (for queries with a WHERE clause).
      - Proportion (percentage) of queries using key operators:
          ORDER BY, GROUP BY, and common aggregation functions (COUNT, SUM, AVG, MIN, MAX).

    Parameters:
      queries (list of str): A list of SQL query strings.
    
    Returns:
      dict: A dictionary containing the computed metrics.
    """
    
    # Initialize counters and accumulators
    table_freq = {}
    read_count = 0
    write_count = 0
    total_predicates = 0
    predicate_query_count = 0  # Count of queries that have a WHERE clause
    order_by_count = 0
    group_by_count = 0
    agg_func_count = 0

    # Precompiled regex patterns for performance and clarity.
    table_pattern = re.compile(r'\b(?:FROM|JOIN|INTO)\s+([\w\.\[\]]+)', re.IGNORECASE)
    # The WHERE pattern captures the clause till GROUP BY, ORDER BY, HAVING or end-of-string.
    where_pattern = re.compile(r'\bWHERE\s+(.*?)(?:\bGROUP\s+BY\b|\bORDER\s+BY\b|\bHAVING\b|$)', re.IGNORECASE)
    agg_pattern = re.compile(r'\b(COUNT|SUM|AVG|MIN|MAX)\s*\(', re.IGNORECASE)
    orderby_pattern = re.compile(r'\bORDER\s+BY\b', re.IGNORECASE)
    groupby_pattern = re.compile(r'\bGROUP\s+BY\b', re.IGNORECASE)

    # Process each query
    for query in queries:
        # Count table accesses (FROM, JOIN, INTO)
        tables = table_pattern.findall(query)
        for table in tables:
            table = table.strip()
            table_freq[table] = table_freq.get(table, 0) + 1

        # Determine if the query is a read or write operation
        query_strip = query.lstrip().upper()
        if query_strip.startswith("SELECT"):
            read_count += 1
        elif any(query_strip.startswith(keyword) for keyword in ["INSERT", "UPDATE", "DELETE", "MERGE"]):
            write_count += 1

        # Count predicate conditions in the WHERE clause, if present
        where_match = where_pattern.search(query)
        if where_match:
            where_clause = where_match.group(1).strip()
            if where_clause:
                # Each occurrence of AND/OR (plus one initial condition) represents a predicate.
                preds = re.findall(r'\bAND\b|\bOR\b', where_clause, flags=re.IGNORECASE)
                num_preds = len(preds) + 1
                total_predicates += num_preds
                predicate_query_count += 1

        # Check for usage of key SQL operators and aggregation functions.
        if orderby_pattern.search(query):
            order_by_count += 1
        if groupby_pattern.search(query):
            group_by_count += 1
        if agg_pattern.search(query):
            agg_func_count += 1

    # Count of total SQL queries
    total_queries = len(queries)

    # Compute read/write ratio (reads/writes)
    read_write_ratio = (read_count / write_count) if write_count else None

    # Compute average number of predicates per query (considering only queries with a WHERE clause)
    average_predicates = (total_predicates / predicate_query_count) if predicate_query_count else 0

    # Compute the proportion (percentage) of queries using key operators relative to total queries
    order_by_prop = (order_by_count / total_queries) * 100 if total_queries else 0
    group_by_prop = (group_by_count / total_queries) * 100 if total_queries else 0
    agg_func_prop = (agg_func_count / total_queries) * 100 if total_queries else 0

    # Return all computed metrics in a dictionary
    return {
        "total_sql_statements": total_queries,
        "read_operations": read_count,
        "write_operations": write_count,
        "read_write_ratio": read_write_ratio,
        "table_access_frequency": table_freq,
        "average_predicates": average_predicates,
        "order_by_proportion": order_by_prop,
        "group_by_proportion": group_by_prop,
        "aggregation_function_proportion": agg_func_prop,
    }

def get_configurations_with_compression(target_db: str, benchmark: str, memory_gb: int, num_cores: int, driver: Driver,
                                        queries: dict, output_dir_path: str,query_weight:bool,does_use_workload_statistics:bool,does_use_internal_metrics:bool,query_plan:bool, token_budget: int = sys.maxsize,
                                        num_configs: int=5, temperature: float=0.2):
    driver.drop_all_non_pk_indexes()
    driver.reset_configuration()
    workload_statistics=None
    if does_use_workload_statistics:
        workload_statistics=analyze_sql_queries([query[1] for query in queries])
    internal_metrics=None
    if does_use_internal_metrics:
        system='gpu'
        with open(f"{benchmark}_metrics_{system}.json", "r") as f:
            internal_metrics = json.load(f)

    conditions,filters,costs,plans = extract_conditions(driver, queries)
    grouped_conditions = group_join_conditions(conditions)

    indexes = True
    solver = ILPSolver(query_weight)

    sorted_conditions=sorted([(c[0],c[2],'join') for c in conditions]+filters,key=lambda x:x[1],reverse=True)
    # start_time = time.time()
    optimized_with_dependencies,lambda_tune_cost = solver.optimize_with_dependencies(grouped_conditions, token_budget)
    # elapsed = time.time() - start_time
#     with open('e1_ilp_time.txt','a')as f:             
#         f.write(f'''{target_db} {benchmark}:{elapsed}
# ''') 
    target=''
    for c in optimized_with_dependencies:
        target += f"{c}: {optimized_with_dependencies[c]}\n"
    cost=0
    join_conditions=defaultdict(list)
    filters=list()
    for cond in sorted_conditions:
        prompt=''
        for c in join_conditions:
            prompt += f"{c}: {join_conditions[c]}\n"
        if len(prompt)>len(target):
            break
        cost+=cond[1]
        if cond[2]=='join':
            s=cond[0].split(' = ')
            join_conditions[s[0]].append(s[1])
        if cond[2]=='filter':
            filters.append(cond[0])
        
    output_dir = os.path.join(output_dir_path)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for i in range(0, num_configs):
        t=time.time()
        doc = get_config_recommendations_with_compression(dst_system=target_db,
                                                        relations=None,
                                                        temperature=temperature,
                                                        retrieve_response=True,
                                                        join_conditions=optimized_with_dependencies,
                                                        system_specs={"memory": f"{memory_gb}GiB", "cores": num_cores},
                                                        #   indexes_only=True,
                                                        indexes=True,
                                                        workload_statistics=workload_statistics,
                                                        internal_metrics=internal_metrics,
                                                        query_plan=query_plan,
                                                        plans=plans,
                                                        )

        path = os.path.join(output_dir, f"config_{benchmark}_tokens_{token_budget}_{temperature}_{int(time.time())}.json")
        json.dump(doc, open(path, "w+"), indent=2)

        print("Done: " + output_dir)
        time.sleep(max(0,30-(time.time()-t)))#Gemini 2.5 Pro Experimental RPM is 2
    return costs