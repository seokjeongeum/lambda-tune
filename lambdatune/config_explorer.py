import json

from lambdatune.llm_response import LLMResponse
import os


def print_config(config_path):
    config_file = open(config_path).read()
    config = json.loads(config_file)
    config = json.loads(config["response"]["choices"][0]["message"]["content"])["commands"]

    for cmd in config:
        # if "CREATE INDEX" not in cmd:
        #     print(cmd)
        print(cmd)

system = "postgres"
all_configs = os.listdir("configs")
condition = "COMPRESSED_JOIN_CONDITIONS_indexes"

path = "configs/tpcds_postgres_compression_tokens_10000_3"
config_paths = os.listdir(path)

idx = 0
for config_path in config_paths:
    llm_response = LLMResponse(os.path.join(path, config_path))

    commands = json.loads(llm_response.config)["commands"]

    for statement in commands:
        # split = statement.split(" ON ")
        # statement = split[0] + f"_{idx} ON " + split[1]
        if "CREATE INDEX" in statement: continue
        print(statement)
        idx += 1
    print("----")
