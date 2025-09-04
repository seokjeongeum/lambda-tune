export PYTHONPATH=.
    
# Automatically export all variables defined in the .env file
set -o allexport
source .env
set +o allexport

rm -r ./lambdatune/configs/2_prompt_ablation
rm -r ./test/2_prompt_ablation
    
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark job\
    --system POSTGRES \
    --configs ./lambdatune/configs/2_prompt_ablation/job/query_weight_ablated \
    --out ./test/2_prompt_ablation/job/query_weight_ablated \
    --config_gen config_gen \
    --core 16 \
    --memory 62 \
    --token_budget 786\
    --exploit_index exploit_index\
    --order_query order_query\
    --workload_statistics workload_statistics\
    --data_definition_language data_definition_language\
    
    
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark job\
    --system POSTGRES \
    --configs ./lambdatune/configs/2_prompt_ablation/job/workload_statistics_ablated \
    --out ./test/2_prompt_ablation/job/workload_statistics_ablated \
    --config_gen config_gen \
    --core 16 \
    --memory 62 \
    --token_budget 786\
    --exploit_index exploit_index\
    --order_query order_query\
    --query_weight query_weight\
    --data_definition_language data_definition_language\
    
    
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark job\
    --system POSTGRES \
    --configs ./lambdatune/configs/2_prompt_ablation/job/data_definition_language_ablated \
    --out ./test/2_prompt_ablation/job/data_definition_language_ablated \
    --config_gen config_gen \
    --core 16 \
    --memory 62 \
    --token_budget 786\
    --exploit_index exploit_index\
    --order_query order_query\
    --query_weight query_weight\
    --workload_statistics workload_statistics\
    
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark job\
    --system POSTGRES \
    --configs ./lambdatune/configs/2_prompt_ablation/job/ws_ddl_ablated \
    --out ./test/2_prompt_ablation/job/ws_ddl_ablated \
    --config_gen config_gen \
    --core 16 \
    --memory 62 \
    --token_budget 786\
    --exploit_index exploit_index\
    --order_query order_query\
    --query_weight query_weight\
    
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark job\
    --system POSTGRES \
    --configs ./lambdatune/configs/2_prompt_ablation/job/qw_ddl_ablated \
    --out ./test/2_prompt_ablation/job/qw_ddl_ablated \
    --config_gen config_gen \
    --core 16 \
    --memory 62 \
    --token_budget 786\
    --exploit_index exploit_index\
    --order_query order_query\
    --workload_statistics workload_statistics\
    
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark job\
    --system POSTGRES \
    --configs ./lambdatune/configs/2_prompt_ablation/job/qw_ws_ablated \
    --out ./test/2_prompt_ablation/job/qw_ws_ablated \
    --config_gen config_gen \
    --core 16 \
    --memory 62 \
    --token_budget 786\
    --exploit_index exploit_index\
    --order_query order_query\
    --data_definition_language data_definition_language\
    