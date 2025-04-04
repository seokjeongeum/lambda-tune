export PYTHONPATH=.
    
# Automatically export all variables defined in the .env file
set -o allexport
source .env
set +o allexport

rm -r ./lambdatune/configs/s51
rm -r ./test/s51
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark job\
    --system POSTGRES \
    --configs ./lambdatune/configs/s51/job/lambdatune \
    --out ./test/s51/job/lambdatune \
    --config_gen config_gen \
    --core 16 \
    --memory 62 \
    --token_budget 786
    
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark job\
    --system POSTGRES \
    --configs ./lambdatune/configs/s51/job/ours \
    --out ./test/s51/job/ours \
    --config_gen config_gen \
    --core 16 \
    --memory 62 \
    --token_budget 786\
    --exploit_index exploit_index\
    --order_query order_query\
    --query_weight query_weight\
    --workload_statistics workload_statistics\
    --data_definition_language data_definition_language\
    
    
# .venv/bin/python lambdatune/run_lambdatune.py \
#     --benchmark tpch\
#     --system POSTGRES \
#     --configs ./lambdatune/configs/s51/tpch/lambdatune \
#     --out ./test/s51/tpch/lambdatune \
#     --config_gen config_gen \
#     --core 16 \
#     --memory 62 \
#     --token_budget 786

    
# .venv/bin/python lambdatune/run_lambdatune.py \
#     --benchmark tpch\
#     --system POSTGRES \
#     --configs ./lambdatune/configs/s51/tpch/ours \
#     --out ./test/s51/tpch/ours \
#     --config_gen config_gen \
#     --core 16 \
#     --memory 62 \
#     --token_budget 786\
#     --exploit_index exploit_index\
#     --order_query order_query\
#     --query_weight query_weight\
#     --workload_statistics workload_statistics\
#     --data_definition_language data_definition_language\

    