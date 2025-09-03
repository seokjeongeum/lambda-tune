# Initialiize SQLite DB

import sqlite3
import os
import json

from collections import defaultdict


class QueryMetadataHandler:
    handler = None
    class ExecutedQueryMeta:
        def __init__(self, query_id, query_name, exec_time, ts, query_text, plan, tag, settings, meta):
            self.query_id = query_id
            self.query_name = query_name
            self.exec_time = exec_time
            self.ts = ts
            self.query_text = query_text
            self.plan = plan
            self.tag = tag
            self.settings = settings
            self.meta = json.loads(meta)
            self.failed = self.meta["timeout_fail"] if "timeout_fail" in self.meta else False

    def __init__(self, db_location="lambda_pi.db", reset=False):
        if reset:
            os.remove(db_location)

        # Create a new SQLite DB
        self.conn = sqlite3.connect(db_location)

        # Create a new cursor
        self.cursor = self.conn.cursor()

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY,
                query_name TEXT,
                query_text TEXT,
                tag TEXT
            )
        ''')

        # Executed queries table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS executed_queries (
                id INTEGER PRIMARY KEY,
                query_id INTEGER,
                query_plan TEXT,
                execution_time REAL,
                settings TEXT DEFAULT NULL,
                ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                meta TEXT DEFAULT NULL,
                FOREIGN KEY (query_id) REFERENCES queries(id)
            )
        ''')

        # Init queries if empty
        self.cursor.execute("SELECT COUNT(*) FROM queries")
        rows = self.cursor.fetchall()

        if rows[0][0] == 0:
            self.init_tpch_queries()
            self.init_job_queries()

    @staticmethod
    def get_handler():
        if not QueryMetadataHandler.handler:
            QueryMetadataHandler.handler = QueryMetadataHandler(reset=False)

        return QueryMetadataHandler.handler

    def insert_query(self, query_name, query_text, tag):
        self.cursor.execute('''
            INSERT INTO queries (query_name, query_text, tag)
            VALUES (?, ?, ?)
        ''', (query_name, query_text, tag))
        self.conn.commit()

    def insert_executed_query(self, query_id, query_plan, execution_time, settings=None, meta=json.dumps(dict())):
        self.cursor.execute('''
            INSERT INTO executed_queries (query_id, query_plan, execution_time, settings, meta)
            VALUES (?, ?, ?, ?, ?)
        ''', (query_id, query_plan, execution_time, settings, meta))
        self.conn.commit()

    def get_all_executed_queries(self):
        self.cursor.execute("SELECT query_id, query_name, execution_time, ts, settings, tag, query_text, query_plan, "
                            "settings, meta "
                            "FROM executed_queries "
                            "JOIN queries ON queries.id = executed_queries.query_id")

        rows = self.cursor.fetchall()

        grouped = defaultdict(list)

        for row in rows:
            query = self.ExecutedQueryMeta(query_id=row[0], query_name=row[1], exec_time=row[2], ts=row[3],
                                           query_text=row[6], plan=row[7], tag=row[5], settings=row[8], meta=row[9])
            grouped[query.query_id].append(query)

        return grouped

    def get_all_tags(self):
        self.cursor.execute("SELECT DISTINCT tag FROM queries")
        rows = self.cursor.fetchall()

        return [row[0] for row in rows]

    def get_queries_by_tag(self, tag):
        self.cursor.execute("SELECT * FROM queries WHERE tag=?", (tag,))
        rows = self.cursor.fetchall()
        return rows

    def init_tpch_queries(self):
        from lambdatune.benchmarks import get_tpch_queries

        tpch_queries = get_tpch_queries()
        for query_name, query_text in tpch_queries:
            self.insert_query(query_name, query_text, "TPCH")
        self.conn.commit()

    def init_job_queries(self):
        from lambdatune.benchmarks import get_job_queries

        job_queries = get_job_queries()

        for query_name, query_text in job_queries:
            self.insert_query(query_name, query_text, "JOB")

        self.conn.commit()

# handler = QueryMetadataHandler(db_location="/Users/victorgiannakouris/Dev/lambda-tune/lambdatune/dbgpt/lambda_pi.db")
#
# queries = handler.get_all_executed_queries()
#
# print()