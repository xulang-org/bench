PYTHON ?= python3
ARGS ?=
.PHONY: list crosslang game stdlib opt-levels opt-full runtime compile clang-manifest test
list:
	$(PYTHON) scripts/bench_crosslang.py --list
crosslang:
	$(PYTHON) scripts/bench_crosslang.py --out reports/crosslang.txt $(ARGS)
game:
	$(PYTHON) scripts/bench_game.py --out reports/game.txt --report reports/game.md $(ARGS)
stdlib:
	./scripts/bench_stdlib.sh $(ARGS)
opt-levels:
	./scripts/bench_opt_levels.sh $(ARGS)
opt-full:
	./scripts/bench_opt_full.sh $(ARGS)
runtime:
	./scripts/bench_runtime.sh $(ARGS)
compile:
	./scripts/bench_compile.sh $(ARGS)
clang-manifest:
	$(PYTHON) scripts/bench_clang_gap_manifest.py
test:
	$(PYTHON) -m pytest tests scripts/test_bench_game.py

.PHONY: nbody-residency
nbody-residency:
	./scripts/test_nbody_residency.sh $(ARGS)
