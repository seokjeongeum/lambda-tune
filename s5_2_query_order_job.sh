export PYTHONPATH=.
    
# Automatically export all variables defined in the .env file
set -o allexport
source .env
set +o allexport

rm -r ./lambdatune/configs/s52
rm -r ./test/s52
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark job\
    --system POSTGRES \
    --configs ./lambdatune/configs/s52/job \
    --out ./test/s52/job/lambdatune \
    --config_gen config_gen \
    --core 64 \
    --memory 128 \
    --token_budget 786\
    
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark job\
    --system POSTGRES \
    --configs ./lambdatune/configs/s52/job \
    --out ./test/s52/job/ours \
    --core 64 \
    --memory 128 \
    --token_budget 786\
    --order_query order_query\
    --exploit_index exploit_index
    
