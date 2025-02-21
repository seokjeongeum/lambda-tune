rm e2_config_reset_time.txt
export PYTHONPATH=.

# Automatically export all variables defined in the .env file
set -o allexport
source .env
set +o allexport

rm -r ./lambdatune/configs/e2
rm -r ./test/e2

# Run the first batch of tests
bash .devcontainer/tpch.sh 1
.venv/bin/python lambdatune/run_lambdatune.py \
    --config_gen true \
    --configs ./lambdatune/configs/e3/tpch1 \
    --out ./test/e3/tpch1 \
    --core 22 \
    --memory 31 \
    --system POSTGRES \
    --benchmark tpch

# Run the next batch of tests
bash .devcontainer/tpch.sh 10
.venv/bin/python lambdatune/run_lambdatune.py \
    --config_gen true \
    --configs ./lambdatune/configs/e3/tpch10 \
    --out ./test/e3/tpch10 \
    --core 22 \
    --memory 31 \
    --system POSTGRES \
    --benchmark tpch

# Run tests for other benchmarks
.venv/bin/python lambdatune/run_lambdatune.py \
    --config_gen true \
    --configs ./lambdatune/configs/e3/tpcds \
    --out ./test/e3/tpcds \
    --core 22 \
    --memory 31 \
    --system POSTGRES \
    --benchmark tpcds

.venv/bin/python lambdatune/run_lambdatune.py \
    --config_gen true \
    --configs ./lambdatune/configs/e3/job \
    --out ./test/e3/job \
    --core 22 \
    --memory 31 \
    --system POSTGRES \
    --benchmark job
