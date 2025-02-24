export PYTHONPATH=.
    
# Automatically export all variables defined in the .env file
set -o allexport
source .env
set +o allexport

rm -r ./lambdatune/configs/e4
rm -r ./test/e4

.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark job\
    --system POSTGRES \
    --configs ./lambdatune/configs/e4/196 \
    --out ./test/e4/196 \
    --config_gen true \
    --core 16 \
    --memory 62 \
    --token_budget 196\
    --method lambdatune

.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark job\
    --system POSTGRES \
    --configs ./lambdatune/configs/e4/196 \
    --out ./test/e4/196 \
    --config_gen true \
    --core 16 \
    --memory 62 \
    --token_budget 196\
    --method naive
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark job\
    --system POSTGRES \
    --configs ./lambdatune/configs/e4/251 \
    --out ./test/e4/251 \
    --config_gen true \
    --core 16 \
    --memory 62 \
    --token_budget 251\
    --method lambdatune
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark job\
    --system POSTGRES \
    --configs ./lambdatune/configs/e4/251 \
    --out ./test/e4/251 \
    --config_gen true \
    --core 16 \
    --memory 62 \
    --token_budget 251\
    --method naive
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark job\
    --system POSTGRES \
    --configs ./lambdatune/configs/e4/355 \
    --out ./test/e4/355 \
    --config_gen true \
    --core 16 \
    --memory 62 \
    --token_budget 355\
    --method lambdatune
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark job\
    --system POSTGRES \
    --configs ./lambdatune/configs/e4/355 \
    --out ./test/e4/355 \
    --config_gen true \
    --core 16 \
    --memory 62 \
    --token_budget 355\
    --method naive
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark job\
    --system POSTGRES \
    --configs ./lambdatune/configs/e4/618 \
    --out ./test/e4/618 \
    --config_gen true \
    --core 16 \
    --memory 62 \
    --token_budget 618\
    --method lambdatune
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark job\
    --system POSTGRES \
    --configs ./lambdatune/configs/e4/618 \
    --out ./test/e4/618 \
    --config_gen true \
    --core 16 \
    --memory 62 \
    --token_budget 618\
    --method naive
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark job\
    --system POSTGRES \
    --configs ./lambdatune/configs/e4/786 \
    --out ./test/e4/786 \
    --config_gen true \
    --core 16 \
    --memory 62 \
    --token_budget 786\
    --method lambdatune
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark job\
    --system POSTGRES \
    --configs ./lambdatune/configs/e4/786 \
    --out ./test/e4/786 \
    --config_gen true \
    --core 16 \
    --memory 62 \
    --token_budget 786\
    --method naive
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark job\
    --system POSTGRES \
    --configs ./lambdatune/configs/e4/9223372036854775807 \
    --out ./test/e4/9223372036854775807 \
    --config_gen true \
    --core 16 \
    --memory 62 \
    --token_budget 9223372036854775807\
    --method lambdatune
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark job\
    --system POSTGRES \
    --configs ./lambdatune/configs/e4/9223372036854775807 \
    --out ./test/e4/9223372036854775807 \
    --config_gen true \
    --core 16 \
    --memory 62 \
    --token_budget 9223372036854775807\
    --method naive
    
.venv/bin/python lambdatune/run_lambdatune.py \
    --benchmark job\
    --system POSTGRES \
    --configs ./lambdatune/configs/e4/query \
    --out ./test/e4/query \
    --config_gen true \
    --core 16 \
    --memory 62 \
    --method query
    