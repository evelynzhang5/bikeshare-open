.PHONY: all data features train test clean model check-model

# --- The pipeline ----------------------------------------------------------
all: data features train

data:
	python -m src.ingest

features:
	python -m src.features

train:
	python -m src.train

test:
	python -m pytest tests/ -q

clean:
	rm -f data/processed/*.parquet reports/metrics.json reports/*.png

# --- The agent model (open weights, local) ----------------------------------
# Builds `bikeshare-coder`: the base model plus a 64k context window, which
# Claude Code needs and Ollama does not give you by default. Pick a larger
# BASE if your machine has the memory (see README.md).
BASE ?= qwen3.5:9b-q4_K_M

model:
	ollama pull $(BASE)
	@set -eu; \
	bikeshare_modelfile=$$(mktemp); \
	trap 'rm -f "$$bikeshare_modelfile"' EXIT; \
	sed "s|^FROM .*|FROM $(BASE)|" model/Modelfile > "$$bikeshare_modelfile"; \
	ollama create bikeshare-coder -f "$$bikeshare_modelfile"

check-model:
	bash model/check.sh
