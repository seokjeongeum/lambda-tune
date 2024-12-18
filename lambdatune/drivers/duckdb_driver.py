import time

import json

import duckdb


class DuckDBDriver():
    def __init__(self, db_file, config=None):
        self.conn = duckdb.connect(db_file)

        if config:
            for c in config.items():
                if not c[1]:
                    self.conn.execute(f"PRAGMA {c[0]}")
                else:
                    self.conn.execute(f"PRAGMA {c[0]}={c[1]}")

    def explain(self, query, analyze=False, config=None, dump_path=None):
        if config:
            for conf in config:
                print(f"Setting config: {conf}")
                self.conn.execute(conf)

        explain_cmd = "EXPLAIN ANALYZE"
        start = time.time_ns()
        self.conn.execute("{} {}".format(explain_cmd, query))
        plan = '\n'.join(self.conn.fetchall()[0])

        duration = int((time.time_ns() - start) / 1_000)

        return {
            "execTime": duration
        }