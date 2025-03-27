export PYTHONPATH=.
    
# Automatically export all variables defined in the .env file
set -o allexport
source .env
set +o allexport

rm -r ./lambdatune/configs/e10
rm -r ./test/e10
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark tpcds\
    --system POSTGRES \
    --configs ./lambdatune/configs/e10/tpcds/lambdatune \
    --out ./test/e10/tpcds/lambdatune \
    --config_gen config_gen \
    --core 64 \
    --memory 128 \
    --token_budget 786\
    --exploit_index exploit_index\
    --order_query order_query\
    
    