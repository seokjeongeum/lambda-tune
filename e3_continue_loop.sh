rm e3_continue_loop.txt
export PYTHONPATH=.

# Automatically export all variables defined in the .env file
set -o allexport
source .env
set +o allexport

rm -r ./lambdatune/configs/e3
rm -r ./test/e3

# Run the first batch of tests
bash .devcontainer/tpch.sh 1
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark tpch\
    --system POSTGRES \
    --configs ./lambdatune/configs/e3/tpch1 \
    --out ./test/e3/tpch1 \
    --config_gen true \
    --core 16 \
    --memory 62 \
    --continue_loop

# Run the next batch of tests
bash .devcontainer/tpch.sh 10
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark tpch\
    --system POSTGRES \
    --configs ./lambdatune/configs/e3/tpch10 \
    --out ./test/e3/tpch10 \
    --config_gen true \
    --core 16 \
    --memory 62 \
    --continue_loop 

# Run tests for other benchmarks
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark tpcds\
    --system POSTGRES \
    --configs ./lambdatune/configs/e3/tpcds \
    --out ./test/e3/tpcds \
    --config_gen true \
    --core 16 \
    --memory 62 \
    --continue_loop 

.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark job\
    --system POSTGRES \
    --configs ./lambdatune/configs/e3/job \
    --out ./test/e3/job \
    --config_gen true \
    --core 16 \
    --memory 62 \
    --continue_loop 
