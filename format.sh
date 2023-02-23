black oarepo_runtime tests --target-version py310
autoflake --in-place --remove-all-unused-imports --recursive oarepo_runtime tests
isort oarepo_runtime tests  --profile black
