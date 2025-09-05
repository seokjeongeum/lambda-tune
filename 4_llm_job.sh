export PYTHONPATH=.
    
# Automatically export all variables defined in the .env file
set -o allexport
source .env
set +o allexport

rm -r ./lambdatune/configs/4_llm/job
rm -r ./test/4_llm/job

.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark job\
    --system POSTGRES \
    --configs ./lambdatune/configs/4_llm/job \
    --out ./test/4_llm/job \
    --config_gen config_gen \
    --core 16 \
    --memory 62 \
    --token_budget 786\
    --exploit_index exploit_index\
    --order_query order_query\
    --query_weight query_weight\
    --workload_statistics workload_statistics\
    --data_definition_language data_definition_language\
    --model gemini-2.5-flash\
    