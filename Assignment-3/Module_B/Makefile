SHELL := /bin/bash

HOST ?= http://127.0.0.1:8000
MAX_USERS := 200

CONCURRENT_USERS ?= 120
CONCURRENT_SPAWN ?= 20
CONCURRENT_TIME ?= 3m

RACE_USERS ?= 120
RACE_SPAWN ?= 30
RACE_TIME ?= 2m

FAILURE_USERS ?= 120
FAILURE_SPAWN ?= 30
FAILURE_TIME ?= 2m

STRESS_USERS ?= 200
STRESS_SPAWN ?= 40
STRESS_TIME ?= 5m

PYTHON_BIN ?= python
LOCUST_BIN ?= locust
BACKEND_ENV ?= ../../Assignment-2/Module_B/backend/.env
RESET_DB ?= 1
RESET_DB_CMD ?= ../../Assignment-2/Module_B/clean_database.sh

check-users = @$(PYTHON_BIN) -c "import sys; value=int(sys.argv[1]); max_users=int(sys.argv[2]); label=sys.argv[3];\
import builtins;\
builtins.print(f'ERROR: {label}={value} exceeds cap {max_users}.\\nThis implementation supports up to {max_users} concurrent users for makefile commands.') if value > max_users else None;\
sys.exit(2 if value > max_users else 0)" "$(1)" "$(MAX_USERS)" "$(2)"

.PHONY: help concurrent race failure stress acid-b acid-c acid-d acid-f acid-s pipeline pipeline-extended pipeline-durability

help:
	@echo "Targets:"
	@echo "  make concurrent            # Run concurrent stage (<= $(MAX_USERS) users)"
	@echo "  make race                  # Run race stage (<= $(MAX_USERS) users)"
	@echo "  make failure               # Run failure-simulation stage (<= $(MAX_USERS) users)"
	@echo "  make stress                # Run stress stage (<= $(MAX_USERS) users)"
	@echo "  make acid-b                # ACID snapshot for concurrent stage"
	@echo "  make acid-c                # ACID snapshot for race stage"
	@echo "  make acid-d                # ACID snapshot for post-restart stage"
	@echo "  make acid-f                # ACID snapshot for failure stage"
	@echo "  make acid-s                # ACID snapshot for stress stage"
	@echo "  make pipeline              # Run concurrent + race + ACID snapshots"
	@echo "  make pipeline-extended     # Pipeline + failure + stress stages"
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

failure:
	$(call check-users,$(FAILURE_USERS),FAILURE_USERS)
	$(LOCUST_BIN) -f locustfile.py --host $(HOST) --tags failure \
		-u $(FAILURE_USERS) -r $(FAILURE_SPAWN) -t $(FAILURE_TIME) --csv failure_stage

stress:
	$(call check-users,$(STRESS_USERS),STRESS_USERS)
	$(LOCUST_BIN) -f locustfile.py --host $(HOST) --tags stress \
		-u $(STRESS_USERS) -r $(STRESS_SPAWN) -t $(STRESS_TIME) --csv stress_stage

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

acid-f:
	@set +e; \
	$(PYTHON_BIN) run_acid_checks.py --env-file $(BACKEND_ENV) --stage stage_f_failure --output acid_stage_f.json; \
	rc=$$?; \
	set -e; \
	if [ $$rc -eq 0 ]; then \
		echo "acid-f: no violations"; \
	elif [ $$rc -eq 1 ]; then \
		echo "acid-f: violations found (see acid_stage_f.json)"; \
	else \
		exit $$rc; \
	fi

acid-s:
	@set +e; \
	$(PYTHON_BIN) run_acid_checks.py --env-file $(BACKEND_ENV) --stage stage_s_stress --output acid_stage_s.json; \
	rc=$$?; \
	set -e; \
	if [ $$rc -eq 0 ]; then \
		echo "acid-s: no violations"; \
	elif [ $$rc -eq 1 ]; then \
		echo "acid-s: violations found (see acid_stage_s.json)"; \
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
	WITH_FAILURE=0 WITH_STRESS=0 \
	WITH_DURABILITY=0 ./run_module_b_pipeline.sh

pipeline-extended:
	$(call check-users,$(CONCURRENT_USERS),CONCURRENT_USERS)
	$(call check-users,$(RACE_USERS),RACE_USERS)
	$(call check-users,$(FAILURE_USERS),FAILURE_USERS)
	$(call check-users,$(STRESS_USERS),STRESS_USERS)
	PYTHON_BIN=$(PYTHON_BIN) LOCUST_BIN=$(LOCUST_BIN) HOST=$(HOST) \
	BACKEND_ENV=$(BACKEND_ENV) \
	RESET_DB=$(RESET_DB) RESET_DB_CMD=$(RESET_DB_CMD) \
	CONCURRENT_USERS=$(CONCURRENT_USERS) CONCURRENT_SPAWN=$(CONCURRENT_SPAWN) CONCURRENT_TIME=$(CONCURRENT_TIME) \
	RACE_USERS=$(RACE_USERS) RACE_SPAWN=$(RACE_SPAWN) RACE_TIME=$(RACE_TIME) \
	FAILURE_USERS=$(FAILURE_USERS) FAILURE_SPAWN=$(FAILURE_SPAWN) FAILURE_TIME=$(FAILURE_TIME) \
	STRESS_USERS=$(STRESS_USERS) STRESS_SPAWN=$(STRESS_SPAWN) STRESS_TIME=$(STRESS_TIME) \
	WITH_FAILURE=1 WITH_STRESS=1 WITH_DURABILITY=0 ./run_module_b_pipeline.sh

pipeline-durability:
	$(call check-users,$(CONCURRENT_USERS),CONCURRENT_USERS)
	$(call check-users,$(RACE_USERS),RACE_USERS)
	$(call check-users,$(FAILURE_USERS),FAILURE_USERS)
	$(call check-users,$(STRESS_USERS),STRESS_USERS)
	PYTHON_BIN=$(PYTHON_BIN) LOCUST_BIN=$(LOCUST_BIN) HOST=$(HOST) \
	BACKEND_ENV=$(BACKEND_ENV) \
	RESET_DB=$(RESET_DB) RESET_DB_CMD=$(RESET_DB_CMD) \
	CONCURRENT_USERS=$(CONCURRENT_USERS) CONCURRENT_SPAWN=$(CONCURRENT_SPAWN) CONCURRENT_TIME=$(CONCURRENT_TIME) \
	RACE_USERS=$(RACE_USERS) RACE_SPAWN=$(RACE_SPAWN) RACE_TIME=$(RACE_TIME) \
	FAILURE_USERS=$(FAILURE_USERS) FAILURE_SPAWN=$(FAILURE_SPAWN) FAILURE_TIME=$(FAILURE_TIME) \
	STRESS_USERS=$(STRESS_USERS) STRESS_SPAWN=$(STRESS_SPAWN) STRESS_TIME=$(STRESS_TIME) \
	WITH_FAILURE=1 WITH_STRESS=1 WITH_DURABILITY=1 ./run_module_b_pipeline.sh
