class Configuration:
    # Unique index id to separate indexes with the same name
    idx: int = 0

    def __init__(self, config_commands=set()):
        indexes = dict()
        configs = set()
        for command in config_commands:
            if "CREATE INDEX" in command:
                print(command)
                index_id = command.split("ON ")[1].strip().replace(";", "")
                index_name = command.split(" ")[2]
                indexes[index_id] = f"CREATE INDEX {index_name}_{Configuration.idx} ON {index_id};"
                Configuration.idx += 1
            else:
                configs.add(command)

        self.indexes = indexes
        self.configs = configs

    def get_indexes(self):
        return self.indexes

    def get_index_commands(self):
        return set(self.indexes.values())

    def remove_indexes(self, index_keys):
        for key in index_keys:
            if key in self.indexes:
                del self.indexes[key]

    def remove_configs(self, config_keys):
        for key in config_keys:
            if key in self.configs:
                self.configs.remove(key)

    def get_configs(self):
        return self.configs

    def add_index(self, index):
        self.indexes.add(index)

    def add_config(self, config):
        self.configs.add(config)