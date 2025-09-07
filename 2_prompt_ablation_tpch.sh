export PYTHONPATH=.
    
# Automatically export all variables defined in the .env file
set -o allexport
source .env
set +o allexport

rm -r ./lambdatune/configs/2_prompt_ablation/tpch
rm -r ./test/2_prompt_ablation/tpch
    
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark tpch\
    --system POSTGRES \
    --configs ./lambdatune/configs/2_prompt_ablation/tpch/query_weight_ablated \
    --out ./test/2_prompt_ablation/tpch/query_weight_ablated \
    --config_gen config_gen \
    --core 16 \
    --memory 62 \
    --token_budget 786\
    --exploit_index exploit_index\
    --order_query order_query\
    --workload_statistics workload_statistics\
    --data_definition_language data_definition_language\
    
    
    
# .venv/bin/python lambdatune/run_lambdatune.py \
#     --benchmark tpch\
#     --system POSTGRES \
#     --configs ./lambdatune/configs/2_prompt_ablation/tpch/workload_statistics_ablated \
#     --out ./test/2_prompt_ablation/tpch/workload_statistics_ablated \
#     --config_gen config_gen \
#     --core 16 \
#     --memory 62 \
#     --token_budget 786\
#     --exploit_index exploit_index\
#     --order_query order_query\
#     --query_weight query_weight\
#     --data_definition_language data_definition_language\
    
    
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark tpch\
    --system POSTGRES \
    --configs ./lambdatune/configs/2_prompt_ablation/tpch/data_definition_language_ablated \
    --out ./test/2_prompt_ablation/tpch/data_definition_language_ablated \
    --config_gen config_gen \
    --core 16 \
    --memory 62 \
    --token_budget 786\
    --exploit_index exploit_index\
    --order_query order_query\
    --query_weight query_weight\
    --workload_statistics workload_statistics\
    
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark tpch\
    --system POSTGRES \
    --configs ./lambdatune/configs/2_prompt_ablation/tpch/ws_ddl_ablated \
    --out ./test/2_prompt_ablation/tpch/ws_ddl_ablated \
    --config_gen config_gen \
    --core 16 \
    --memory 62 \
    --token_budget 786\
    --exploit_index exploit_index\
    --order_query order_query\
    --query_weight query_weight\
    
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark tpch\
    --system POSTGRES \
    --configs ./lambdatune/configs/2_prompt_ablation/tpch/qw_ddl_ablated \
    --out ./test/2_prompt_ablation/tpch/qw_ddl_ablated \
    --config_gen config_gen \
    --core 16 \
    --memory 62 \
    --token_budget 786\
    --exploit_index exploit_index\
    --order_query order_query\
    --workload_statistics workload_statistics\
    
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark tpch\
    --system POSTGRES \
    --configs ./lambdatune/configs/2_prompt_ablation/tpch/qw_ws_ablated \
    --out ./test/2_prompt_ablation/tpch/qw_ws_ablated \
    --config_gen config_gen \
    --core 16 \
    --memory 62 \
    --token_budget 786\
    --exploit_index exploit_index\
    --order_query order_query\
    --data_definition_language data_definition_language\
    