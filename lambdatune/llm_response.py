import json
import re


class LLMResponse:
    def __init__(self, path):
        with open(path) as f:
            data = json.load(f)

            self.prompt = data["prompt"]
            self.response = data["response"]
            self.config = self.response["choices"][0]["message"]["content"]
            self.config = re.sub(r'^```(python|json)\s+|```', '', self.config)

            self.columns_dict = None
            self.tables_dict = None
            self.hidden_table_cols = False

            if "hidden_table_cols" in data:
                self.columns_dict = data["hidden_table_cols"]["columns"]
                self.tables_dict = data["hidden_table_cols"]["tables"]
                self.hidden_table_cols = True

    def has_hidden_table_cols(self):
        return self.hidden_table_cols

    def get_config(self, hide=False):
        config = json.loads(self.config)["commands"]

        if self.has_hidden_table_cols() and not hide:
            for idx, cfg in enumerate(config):
                if "CREATE INDEX" in cfg:
                    tmp = cfg.split("ON")[1]

                    tbl = tmp.split("(")[0].strip()
                    column = tmp.split("(")[1].split(")")[0].strip()

                    real_tbl = self.tables_dict[tbl]
                    real_col = self.columns_dict[column]

                    cfg = cfg.split(" ON ")[0] + f" ON {real_tbl}({real_col});"
                    config[idx] = cfg

        return config
