import json
import re

def validate_input_format(input_data):
    # Ensure the input is a list
    if not isinstance(input_data, list):
        return False

    # Process each dictionary in the list
    for item in input_data:
        # Each item must be a dictionary with a 'command' key
        if not isinstance(item, dict) or 'command' not in item:
            return False

        # The value of 'command' must be a string
        if not isinstance(item['command'], str):
            return False

        # Define a regex pattern to match SQL commands starting with ALTER SYSTEM or CREATE INDEX
        sql_pattern = r'^(ALTER SYSTEM|CREATE INDEX)\s'
        # Split the command string into lines
        lines = item['command'].strip().split('\n')
        for line in lines:
            stripped_line = line.strip()
            # Skip empty lines
            if not stripped_line:
                continue
            # Validate the command format using the regex pattern
            if not re.match(sql_pattern, stripped_line, re.IGNORECASE):
                return False

    return True
class LLMResponse:
    def __init__(self, path):
        with open(path) as f:
            data = json.load(f)

            self.prompt = data["prompt"]
            self.response = data["response"]
            self.config = self.response["choices"][0]["message"]["content"]
            self.config = re.sub(r'^```(python|json)\s+|```', '', self.config)
            self.config = re.sub(r'^\s*#.*$', '', self.config, flags=re.MULTILINE)
            # Parse the JSON string
            parsed_json = eval(self.config)
            if validate_input_format(parsed_json):
                merged_commands = "\n".join(entry["command"].strip() for entry in parsed_json)
                # Create the resulting merged structure
                self.config = json.dumps({"commands": merged_commands}, indent=4)
            # Check if parsed_json is a list with a single element,
            # then extract that element.
            if isinstance(parsed_json, list) and len(parsed_json) == 1:
                self.config =  json.dumps(parsed_json[0], indent=4)

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
