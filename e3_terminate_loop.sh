export PYTHONPATH=.

# Automatically export all variables defined in the .env file
set -o allexport
source .env
set +o allexport

# Run the first batch of tests
bash .devcontainer/tpch.sh 1
.venv/bin/python lambdatune/run_lambdatune.py \
    --config_gen true \
    --configs ./lambdatune/configs/tpch1 \
    --out ./e3/tpch1 \
    --core 16 \
    --memory 62 \
    --system POSTGRES \
    --benchmark tpch\
    --terminate_loop false

# Run the next batch of tests
bash .devcontainer/tpch.sh 10
.venv/bin/python lambdatune/run_lambdatune.py \
    --config_gen true \
    --configs ./lambdatune/configs/tpch10 \
    --out ./e3/tpch10 \
    --core 16 \
    --memory 62 \
    --system POSTGRES \
    --benchmark tpch\
    --terminate_loop false

# Run tests for other benchmarks
.venv/bin/python lambdatune/run_lambdatune.py \
    --config_gen true \
    --configs ./lambdatune/configs/tpcds \
    --out ./e3/tpcds \
    --core 16 \
    --memory 62 \
    --system POSTGRES \
    --benchmark tpcds\
    --terminate_loop false

.venv/bin/python lambdatune/run_lambdatune.py \
    --config_gen true \
    --configs ./lambdatune/configs/job \
    --out ./e3/job \
    --core 16 \
    --memory 62 \
    --system POSTGRES \
    --benchmark job\
    --terminate_loop false
