import os
import json

def load_plan_files(path):
    plans = os.listdir(path)
    plans = filter(lambda x: x.endswith(".json"), plans)
    plans = map(lambda x: (x.split(".json")[0].split("_")[0], x), plans)
    plans = map(lambda x: (x[0], json.load(open(os.path.join(path, x[1])))), plans)
    return dict(plans)