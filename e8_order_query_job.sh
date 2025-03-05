export PYTHONPATH=.
    
# Automatically export all variables defined in the .env file
set -o allexport
source .env
set +o allexport

# rm -r ./lambdatune/configs/e8
# rm -r ./test/e8
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark job\
    --system POSTGRES \
    --configs ./lambdatune/configs/e8/job \
    --out ./test/e8/job/lambdatune \
    --config_gen config_gen \
    --core 22 \
    --memory 31 \
    --token_budget 786\
    --method lambdatune\
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark job\
    --system POSTGRES \
    --configs ./lambdatune/configs/e8/job \
    --out ./test/e8/job/order_query \
    --core 22 \
    --memory 31 \
    --token_budget 786\
    --method lambdatune\
    --order_query order_query
    