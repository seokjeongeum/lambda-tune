rm e2_config_reset_time.txt
export PYTHONPATH=.

# Automatically export all variables defined in the .env file
set -o allexport
source .env
set +o allexport

# Run the first batch of tests
bash .devcontainer/tpch.sh 1
.venv/bin/python lambdatune/run_lambdatune.py \
    --config_gen true \
    --configs ./lambdatune/configs \
    --out ./test \
    --core 22 \
    --memory 31 \
    --system POSTGRES \
    --benchmark tpch
.venv/bin/python lambdatune/run_lambdatune.py \
    --config_gen true \
    --configs ./lambdatune/configs \
    --out ./test \
    --core 22 \
    --memory 31 \
    --system MYSQL \
    --benchmark tpch

# Run the next batch of tests
bash .devcontainer/tpch.sh 10
.venv/bin/python lambdatune/run_lambdatune.py \
    --config_gen true \
    --configs ./lambdatune/configs \
    --out ./test \
    --core 22 \
    --memory 31 \
    --system POSTGRES \
    --benchmark tpch
.venv/bin/python lambdatune/run_lambdatune.py \
    --config_gen true \
    --configs ./lambdatune/configs \
    --out ./test \
    --core 22 \
    --memory 31 \
    --system MYSQL \
    --benchmark tpch

# Run tests for other benchmarks
.venv/bin/python lambdatune/run_lambdatune.py \
    --config_gen true \
    --configs ./lambdatune/configs \
    --out ./test \
    --core 22 \
    --memory 31 \
    --system POSTGRES \
    --benchmark tpcds
.venv/bin/python lambdatune/run_lambdatune.py \
    --config_gen true \
    --configs ./lambdatune/configs \
    --out ./test \
    --core 22 \
    --memory 31 \
    --system MYSQL \
    --benchmark tpcds

.venv/bin/python lambdatune/run_lambdatune.py \
    --config_gen true \
    --configs ./lambdatune/configs \
    --out ./test \
    --core 22 \
    --memory 31 \
    --system POSTGRES \
    --benchmark job
.venv/bin/python lambdatune/run_lambdatune.py \
    --config_gen true \
    --configs ./lambdatune/configs \
    --out ./test \
    --core 22 \
    --memory 31 \
    --system MYSQL \
    --benchmark job
