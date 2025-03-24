rm e2_index_time.txt
rm e3_continue_loop.txt
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
    --configs ./lambdatune/configs/e2/tpch1 \
    --out ./test/e2/tpch1 \
    --core 64 \
    --memory 128 \
    --system POSTGRES \
    --benchmark tpch

# Run the next batch of tests
bash .devcontainer/tpch.sh 10
.venv/bin/python lambdatune/run_lambdatune.py \
    --config_gen true \
    --configs ./lambdatune/configs/e2/tpch10 \
    --out ./test/e2/tpch10 \
    --core 64 \
    --memory 128 \
    --system POSTGRES \
    --benchmark tpch

# Run tests for other benchmarks
.venv/bin/python lambdatune/run_lambdatune.py \
    --config_gen true \
    --configs ./lambdatune/configs/e2/tpcds \
    --out ./test/e2/tpcds \
    --core 64 \
    --memory 128 \
    --system POSTGRES \
    --benchmark tpcds

.venv/bin/python lambdatune/run_lambdatune.py \
    --config_gen true \
    --configs ./lambdatune/configs/e2/job \
    --out ./test/e2/job \
    --core 64 \
    --memory 128 \
    --system POSTGRES \
    --benchmark job
