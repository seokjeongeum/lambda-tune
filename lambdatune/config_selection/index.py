class Index:
    def __init__(self, index_name, table_name, column_name):
        self.__index_name = index_name
        self.__table_name = table_name
        self.__column_name = column_name

    def get_index_name(self):
        return self.__index_name

    def get_table_name(self):
        return self.__table_name

    def get_column_name(self):
        return self.__column_name

    def get_create_index_statement(self):
        return f"CREATE INDEX {self.__index_name} ON {self.__table_name} ({self.__column_name});"

    def get_drop_index_statement(self):
        return f"DROP INDEX {self.__index_name};"

    def __eq__(self, other):
        return self.__index_name == other.__index_name and self.__table_name == other.__table_name and self.__column_name == other.__column_name

    def __hash__(self):
        return hash((self.__index_name, self.__table_name, self.__column_name))

    def __str__(self):
        return f"Index({self.__index_name}, {self.__table_name}, {self.__column_name})"