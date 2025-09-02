from collections import defaultdict
import logging

import platform
import os

import subprocess
import time
import json

import mysql.connector


class MySQLDriver:
    def __init__(self, conf):
        for i in range(0, 20):
            try:
                self.conf = conf
                self.conn = mysql.connector.connect(user=conf['user'],
                                                    password=conf['password'],
                                                    database=conf['db'])
                self.cursor = self.conn.cursor()
                return
            except Exception as e:
                logging.error(e)
                time.sleep(2)

        self.cursor = None

    @staticmethod
    def restart_system():
        if platform.system() == "Darwin":
            restart_cmd = "brew services restart mysql"
        elif platform.system() == "Linux":
            restart_cmd = "echo dbbert | sudo -S service mysql restart"
        else:
            raise Exception(f"System {platform.system()} is not supported.")
        logging.info("Restarting MySQL")
        p = os.popen(restart_cmd).read()
        logging.info("Done!")

    def reset_configuration(self, configs=None, restart_system=False):
        if configs:
            config_str = ""
            for config in configs:
                config_str += f"SET GLOBAL {config} = DEFAULT\n"

            self.cursor.execute(config_str)

        MySQLDriver.restart_system()
        self.__init__(self.conf)

    def set_configuration(self, config_commands, reset=True, restart=False):
        if reset:
            MySQLDriver.restart_system()
            self.__init__(self.conf)

        self.conn.autocommit = True

        for cmd in config_commands:
            try:
                print(cmd)
                self.get_cursor().execute(cmd)
            except Exception as e:
                print(e)

        # Reset connection for the configs to take effect
        self.cursor.close()
        self.conn.close()
        self.__init__(self.conf)


    def get_configuration(self, configuration_name):
        self.cursor.execute(f"SHOW VARIABLES LIKE '{configuration_name}'")

        return self.cursor.fetchall()[0]

    def get_cursor(self):
        if self.cursor:
            self.cursor.close()

        self.cursor = self.conn.cursor(buffered=True)

        return self.cursor

    def explain(self, query, execute=True, explain_json=False, timeout=None, results_path=None):
        # Optionally modify the query to force a timeout (using a MAX_EXECUTION_TIME hint).
        if timeout:
            # This example shows how you might apply MySQL's MAX_EXECUTION_TIME hint.
            # Adjust the replacement if your query structure is different.
            query = query.replace("select", "select\n\t/*+ MAX_EXECUTION_TIME({}) */".format(int(timeout)), 1)
            
        cursor = self.get_cursor()
        # Build the EXPLAIN command depending on whether JSON format is requested.
        explain_cmd = "EXPLAIN"
        if explain_json:
            explain_cmd += " (FORMAT JSON)"
        explain_cmd = f"{explain_cmd} {query}"
        cursor.execute(explain_cmd)
        rows = cursor.fetchall()

        # Parse the plan based on the expected format.
        if explain_json:
            try:
                # For JSON, it is common for MySQL to return a single row containing a JSON string.
                # Adjust the following indexing based on your MySQL version.
                plan = rows
            except Exception as e:
                logging.warning(f"Failed to parse JSON plan: {e}")
                plan = None
        else:
            try:
                # For non-JSON, join all rows (assuming each row has a first column with part of the plan)
                plan = "\n".join(row for row in rows)
            except Exception as e:
                logging.warning(f"Failed to parse plan: {e}")
                plan = None

        # Optionally execute the query (and time its execution) if execute is True.
        duration = None
        if execute:
            logging.info("Executing query...")
            start = time.time()
            try:
                cursor.execute(query)
                duration = time.time() - start
            except Exception as e:
                logging.warning(f"Execution error: {e}")
                duration = "TIMEOUT"

            logging.info(f"Query execution took: {duration}")

        out = {
            "plan": plan,
            "execTime": duration
        }

        # Optionally write the output to a file.
        if results_path:
            with open(results_path, "w+") as f:
                json.dump(out, f, indent=2)                

        cursor.close()
        return out


    def explain_json(self, query, analyze=False, verbose=False, config=None, dump_path=None):
        if config:
            for conf in config:
                print("Setting {} to {}".format(conf, config[conf]))
                self.cursor.execute("SET {} = {}".format(conf, config[conf]))

        explain_cmd = "EXPLAIN FORMAT=JSON"

        if analyze:
            explain_cmd += ", ANALYZE"

        if verbose:
            explain_cmd += ", VERBOSE"

        explain_cmd += " ) "

        self.cursor.execute("{} {}".format(explain_cmd, query))

        plan = self.cursor.fetchall()[0][0][0]["Plan"]

        if config:
            print("Resetting config")
            for conf in config:
                print("Setting {} to {}".format(conf, "ON"))
                self.cursor.execute("SET {} = {}".format(conf, "ON"))

        out = {
            "config": config,
            "plan": plan
        }

        if dump_path:
            json.dump(out, open(dump_path, "w+"), indent=2)

        return out

    def get_table_cardinalities(self) -> dict:
        self.cursor.execute(f"SELECT table_name, table_rows FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{self.conf['db']}'")
        cardinalities = self.cursor.fetchall()

        return dict(cardinalities)

    def get_all_indexes_full(self) -> list:
        self.get_cursor().execute(f"SELECT index_name, table_name FROM INFORMATION_SCHEMA.STATISTICS WHERE TABLE_SCHEMA = '{self.conf['db']}'")
        indexes = self.cursor.fetchall()

        return [index for index in indexes]

    def get_all_non_pk_indexes_full(self) -> list:
        indexes = self.get_all_indexes_full()
        indexes = [index for index in indexes if "PRIMARY" not in str(index)]

        return indexes

    def drop_all_non_pk_indexes(self):
        indexes = self.get_all_non_pk_indexes_full()
        for index in indexes:
            logging.info(f"Dropping index {index[0]} on table {index[1]}")
            try:
                self.get_cursor().execute(f"DROP INDEX {index[0]} ON {index[1]}")
            except Exception as e:
                logging.error(e)

    def drop_all_fk_constraints(self):
        self.get_cursor().execute(f"SELECT TABLE_NAME, CONSTRAINT_NAME FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS "
                            f"WHERE CONSTRAINT_TYPE = 'FOREIGN KEY' AND TABLE_SCHEMA = '{self.conf['db']}'")
        constraints = self.cursor.fetchall()

        for constraint in constraints:
            logging.info(f"Dropping constraint {constraint[1]} on table {constraint[0]}")
            try:
                self.cursor.execute(f"ALTER TABLE {constraint[0]} DROP FOREIGN KEY {constraint[1]}")
            except Exception as e:
                logging.error(e)

    def reset_session(self):
        self.cursor.close()
        self.__init__(self.conf)

    def get_db_schema(self) -> dict:
        cursor = self.get_cursor()

        # Query the information_schema to fetch table and column names
        query = f"""
        SELECT 
            table_name,
            column_name
        FROM 
            information_schema.columns
        ORDER BY 
            table_name, ordinal_position;
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        # Group the column names by table name using a defaultdict of lists
        schema = defaultdict(list)
        for table, col in rows:
            schema[table].append(col)
        return schema