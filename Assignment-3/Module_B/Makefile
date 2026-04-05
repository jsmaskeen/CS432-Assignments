SHELL := /bin/bash

HOST ?= http://127.0.0.1:8000
MAX_USERS := 200

CONCURRENT_USERS ?= 120
CONCURRENT_SPAWN ?= 20
CONCURRENT_TIME ?= 3m

RACE_USERS ?= 120
RACE_SPAWN ?= 30
RACE_TIME ?= 2m

PYTHON_BIN ?= ../../backend/.venv/bin/python
LOCUST_BIN ?= ../../backend/.venv/bin/locust
BACKEND_ENV ?= ../../Assignment-2/Module_B/backend/.env
RESET_DB ?= 1
RESET_DB_CMD ?= ../../Assignment-2/Module_B/clean_database.sh

check-users = @if [ "$(1)" -gt "$(MAX_USERS)" ]; then \
	echo "ERROR: $(2)=$(1) exceeds cap $(MAX_USERS)."; \
	echo "This implementation supports up to $(MAX_USERS) concurrent users for makefile commands."; \
	exit 2; \
fi

.PHONY: help concurrent race acid-b acid-c acid-d pipeline pipeline-durability

help:
	@echo "Targets:"
	@echo "  make concurrent            # Run concurrent stage (<= $(MAX_USERS) users)"
	@echo "  make race                  # Run race stage (<= $(MAX_USERS) users)"
	@echo "  make acid-b                # ACID snapshot for concurrent stage"
	@echo "  make acid-c                # ACID snapshot for race stage"
	@echo "  make acid-d                # ACID snapshot for post-restart stage"
	@echo "  make pipeline              # Run concurrent + race + ACID snapshots"
	@echo "  make pipeline-durability   # Pipeline + durability stage"
	@echo "Variables:"
	@echo "  RESET_DB=1 (default), RESET_DB_CMD=$(RESET_DB_CMD)"

concurrent:
	$(call check-users,$(CONCURRENT_USERS),CONCURRENT_USERS)
	$(LOCUST_BIN) -f locustfile.py --host $(HOST) --tags concurrent \
		-u $(CONCURRENT_USERS) -r $(CONCURRENT_SPAWN) -t $(CONCURRENT_TIME) --headless --csv concurrent_stage

race:
	$(call check-users,$(RACE_USERS),RACE_USERS)
	$(LOCUST_BIN) -f locustfile.py --host $(HOST) --tags race \
		-u $(RACE_USERS) -r $(RACE_SPAWN) -t $(RACE_TIME) --headless --csv race_stage

acid-b:
	@set +e; \
	$(PYTHON_BIN) run_acid_checks.py --env-file $(BACKEND_ENV) --stage stage_b_concurrent --output acid_stage_b.json; \
	rc=$$?; \
	set -e; \
	if [ $$rc -eq 0 ]; then \
		echo "acid-b: no violations"; \
	elif [ $$rc -eq 1 ]; then \
		echo "acid-b: violations found (see acid_stage_b.json)"; \
	else \
		exit $$rc; \
	fi

acid-c:
	@set +e; \
	$(PYTHON_BIN) run_acid_checks.py --env-file $(BACKEND_ENV) --stage stage_c_race --output acid_stage_c.json; \
	rc=$$?; \
	set -e; \
	if [ $$rc -eq 0 ]; then \
		echo "acid-c: no violations"; \
	elif [ $$rc -eq 1 ]; then \
		echo "acid-c: violations found (see acid_stage_c.json)"; \
	else \
		exit $$rc; \
	fi

acid-d:
	@set +e; \
	$(PYTHON_BIN) run_acid_checks.py --env-file $(BACKEND_ENV) --stage stage_d_post_restart --output acid_stage_d.json; \
	rc=$$?; \
	set -e; \
	if [ $$rc -eq 0 ]; then \
		echo "acid-d: no violations"; \
	elif [ $$rc -eq 1 ]; then \
		echo "acid-d: violations found (see acid_stage_d.json)"; \
	else \
		exit $$rc; \
	fi

pipeline:
	$(call check-users,$(CONCURRENT_USERS),CONCURRENT_USERS)
	$(call check-users,$(RACE_USERS),RACE_USERS)
	PYTHON_BIN=$(PYTHON_BIN) LOCUST_BIN=$(LOCUST_BIN) HOST=$(HOST) \
	BACKEND_ENV=$(BACKEND_ENV) \
	RESET_DB=$(RESET_DB) RESET_DB_CMD=$(RESET_DB_CMD) \
	CONCURRENT_USERS=$(CONCURRENT_USERS) CONCURRENT_SPAWN=$(CONCURRENT_SPAWN) CONCURRENT_TIME=$(CONCURRENT_TIME) \
	RACE_USERS=$(RACE_USERS) RACE_SPAWN=$(RACE_SPAWN) RACE_TIME=$(RACE_TIME) \
	WITH_DURABILITY=0 ./run_module_b_pipeline.sh

pipeline-durability:
	$(call check-users,$(CONCURRENT_USERS),CONCURRENT_USERS)
	$(call check-users,$(RACE_USERS),RACE_USERS)
	PYTHON_BIN=$(PYTHON_BIN) LOCUST_BIN=$(LOCUST_BIN) HOST=$(HOST) \
	BACKEND_ENV=$(BACKEND_ENV) \
	RESET_DB=$(RESET_DB) RESET_DB_CMD=$(RESET_DB_CMD) \
	CONCURRENT_USERS=$(CONCURRENT_USERS) CONCURRENT_SPAWN=$(CONCURRENT_SPAWN) CONCURRENT_TIME=$(CONCURRENT_TIME) \
	RACE_USERS=$(RACE_USERS) RACE_SPAWN=$(RACE_SPAWN) RACE_TIME=$(RACE_TIME) \
	WITH_DURABILITY=1 ./run_module_b_pipeline.sh
