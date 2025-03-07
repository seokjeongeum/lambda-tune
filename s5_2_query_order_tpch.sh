export PYTHONPATH=.
    
# Automatically export all variables defined in the .env file
set -o allexport
source .env
set +o allexport

rm -r ./lambdatune/configs/s52
rm -r ./test/s52
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark tpch\
    --system POSTGRES \
    --configs ./lambdatune/configs/s52/tpch \
    --out ./test/s52/tpch/lambdatune \
    --config_gen config_gen \
    --core 16 \
    --memory 62 \
    --token_budget 786\
    --method lambdatune\
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark tpch\
    --system POSTGRES \
    --configs ./lambdatune/configs/s52/tpch \
    --out ./test/s52/tpch/ours \
    --core 16 \
    --memory 62 \
    --token_budget 786\
    --method lambdatune\
    --order_query order_query\
    --exploit_index exploit_index
    