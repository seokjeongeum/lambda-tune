export PYTHONPATH=.
    
# Automatically export all variables defined in the .env file
set -o allexport
source .env
set +o allexport

rm -r ./lambdatune/configs/e6
rm -r ./test/e6
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark tpcds\
    --system POSTGRES \
    --configs ./lambdatune/configs/e6/tpcds \
    --out ./test/e6/tpcds \
    --config_gen config_gen \
    --core 22 \
    --memory 31 \
    --token_budget 786\
    --method lambdatune\
    --default default
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark tpch\
    --system POSTGRES \
    --configs ./lambdatune/configs/e6/tpch \
    --out ./test/e6/tpch \
    --config_gen config_gen \
    --core 22 \
    --memory 31 \
    --token_budget 786\
    --method lambdatune\
    --default default
    