export PYTHONPATH=.
    
# Automatically export all variables defined in the .env file
set -o allexport
source .env
set +o allexport

# rm -r ./lambdatune/configs/e8
# rm -r ./test/e8
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark tpch\
    --system POSTGRES \
    --configs ./lambdatune/configs/e8/tpch \
    --out ./test/e8/tpch/lambdatune \
    --config_gen config_gen \
    --core 16 \
    --memory 62 \
    --token_budget 786\
    --method lambdatune\
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark tpch\
    --system POSTGRES \
    --configs ./lambdatune/configs/e8/tpch \
    --out ./test/8/tpch/order_query \
    --core 16 \
    --memory 62 \
    --token_budget 786\
    --method lambdatune\
    --order_query order_query
    