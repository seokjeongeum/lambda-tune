export PYTHONPATH=.
    
# Automatically export all variables defined in the .env file
set -o allexport
source .env
set +o allexport

rm -r ./lambdatune/configs/s52
rm -r ./test/s52
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark tpcds\
    --system POSTGRES \
    --configs ./lambdatune/configs/s52/tpcds \
    --out ./test/s52/tpcds/lambdatune \
    --config_gen config_gen \
    --core 16 \
    --memory 62 \
    --token_budget 786\
    --query_weight query_weight\
    --workload_statistics workload_statistics\
    --data_definition_language data_definition_language\
    
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark tpcds\
    --system POSTGRES \
    --configs ./lambdatune/configs/s52/tpcds \
    --out ./test/s52/tpcds/ours \
    --core 16 \
    --memory 62 \
    --token_budget 786\
    --order_query order_query\
    --exploit_index exploit_index\
    --query_weight query_weight\
    --workload_statistics workload_statistics\
    --data_definition_language data_definition_language\
    
    