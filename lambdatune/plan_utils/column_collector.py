import sqlglot

from sqlglot import exp


class ColumnCollector:
    """
    Collects the columns referenced in a SQL query.
    """

    class Table:
        """
        Represents a table in a SQL query.
        """
        def __init__(self, name: str, alias:str):
            self.name = name
            self.alias = alias

        def get_name(self):
            """
            Returns the name of the table.
            @return: The name of the table.
            """
            return self.name

        def get_alias(self):
            """
            Returns the alias of the table.
            @return: The alias of the table.
            """
            return self.alias

        def __eq__(self, other):
            return self.name == other.name and self.alias == other.alias

        def __hash__(self):
            return hash((self.name, self.alias))

        def __str__(self):
            return f"{self.name} {self.alias}"

    def __init__(self, schema: dict = None):
        self.columns = set()
        self.alias_to_table = dict()
        self.schema = schema
        self.col_to_table = dict()

        if schema:
            for table in schema:
                for col in schema[table]:
                    self.col_to_table[col] = table

    def collect_tables(self, expression: exp.Expression):
        """
        Recursively extract join expressions from the parsed SQL.
        """

        if not expression:
            return None

        if isinstance(expression, list):
            for e in expression:
                self.collect_tables(e)

        if isinstance(expression, exp.Expression):
            for subexp in expression.args.values():
                self.collect_tables(subexp)

            if isinstance(expression, exp.Table):
                # self.tables.add(self.Table(name=expression.name, alias=expression.alias_or_name))
                self.alias_to_table[expression.alias_or_name] = self.Table(name=expression.name, alias=expression.alias_or_name)

    def collect_columns(self, expression: exp.Expression):
        """
        Recursively extract columns included in join/filter expressions from the parsed SQL.
        """
        if isinstance(expression, exp.Column):
            name = str(expression).split(".")

            if len(name) > 1:
                if name[0] in self.alias_to_table:
                    self.columns.add(self.alias_to_table[name[0]].get_name() + "." + name[1])
            else:
                if name[0] in self.col_to_table:
                    self.columns.add(self.col_to_table[name[0]] + "." + name[0])
                else:
                    self.columns.add(name[0])

        for subexp in expression.args.values():
            if isinstance(subexp, exp.Expression):
                self.collect_columns(subexp)

    def collect_columns_from_query(self, query: str, db_schema: dict = None):
        plan = sqlglot.parse_one(query)

        self.collect_tables(expression=plan)
        self.collect_columns(expression=plan)

        return self.columns