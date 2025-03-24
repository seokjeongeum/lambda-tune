rm e1_ilp_time.txt
export PYTHONPATH=.

bash .devcontainer/tpch.sh 1
.venv/bin/python lambdatune/run_lambdatune.py \
    --config_gen true \
    --configs ./lambdatune/configs \
    --out ./test \
    --core 64 \
    --memory 128 \
    --system POSTGRES \
    --benchmark tpch

bash .devcontainer/tpch.sh 10
.venv/bin/python lambdatune/run_lambdatune.py \
    --config_gen true \
    --configs ./lambdatune/configs \
    --out ./test \
    --core 64 \
    --memory 128 \
    --system POSTGRES \
    --benchmark tpch
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --config_gen true \
    --configs ./lambdatune/configs \
    --out ./test \
    --core 64 \
    --memory 128 \
    --system POSTGRES \
    --benchmark tpcds
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --config_gen true \
    --configs ./lambdatune/configs \
    --out ./test \
    --core 64 \
    --memory 128 \
    --system POSTGRES \
    --benchmark job
    