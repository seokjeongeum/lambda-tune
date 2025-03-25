export PYTHONPATH=.
    
# Automatically export all variables defined in the .env file
set -o allexport
source .env
set +o allexport

# rm -r ./lambdatune/configs/e5
# rm -r ./test/e5
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark job\
    --system POSTGRES \
    --configs ./lambdatune/configs/e5/1572 \
    --out ./test/e5/1572 \
    --config_gen true \
    --core 16 \
    --memory 62 \
    --token_budget 1572\
    --method lambdatune
    
# .venv/bin/python lambdatune/run_lambdatune.py \
#     --benchmark job\
#     --system POSTGRES \
#     --configs ./lambdatune/configs/e5/1572 \
#     --out ./test/e5/1572 \
#     --config_gen true \
#     --core 16 \
#     --memory 62 \
#     --token_budget 1572\
#     --method naive
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark job\
    --system POSTGRES \
    --configs ./lambdatune/configs/e5/9223372036854775807 \
    --out ./test/e5/9223372036854775807 \
    --config_gen true \
    --core 16 \
    --memory 62 \
    --token_budget 9223372036854775807\
    --method lambdatune
    
# .venv/bin/python lambdatune/run_lambdatune.py \
#     --benchmark job\
#     --system POSTGRES \
#     --configs ./lambdatune/configs/e5/9223372036854775807 \
#     --out ./test/e5/9223372036854775807 \
#     --config_gen true \
#     --core 16 \
#     --memory 62 \
#     --token_budget 9223372036854775807\
#     --method naive
    