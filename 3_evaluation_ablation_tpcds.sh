export PYTHONPATH=.
    
# Automatically export all variables defined in the .env file
set -o allexport
source .env
set +o allexport

rm -r ./lambdatune/configs/3_evaluation_ablation/tpcds
rm -r ./test/3_evaluation_ablation/tpcds
    
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark tpcds\
    --system POSTGRES \
    --configs ./lambdatune/configs/1_main/tpcds/ours \
    --out ./test/3_evaluation_ablation/tpcds/exploit_index_ablated \
    --core 16 \
    --memory 62 \
    --token_budget 786\
    --order_query order_query\
    --query_weight query_weight\
    --workload_statistics workload_statistics\
    --data_definition_language data_definition_language\
    
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark tpcds\
    --system POSTGRES \
    --configs ./lambdatune/configs/1_main/tpcds/ours \
    --out ./test/3_evaluation_ablation/tpcds/order_query_ablated \
    --core 16 \
    --memory 62 \
    --token_budget 786\
    --exploit_index exploit_index\
    --query_weight query_weight\
    --workload_statistics workload_statistics\
    --data_definition_language data_definition_language\
    
    
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark tpcds\
    --system POSTGRES \
    --configs ./lambdatune/configs/1_main/tpcds/ours \
    --out ./test/3_evaluation_ablation/tpcds/ei_oq_ablated \
    --core 16 \
    --memory 62 \
    --token_budget 786\
    --query_weight query_weight\
    --workload_statistics workload_statistics\
    --data_definition_language data_definition_language\
