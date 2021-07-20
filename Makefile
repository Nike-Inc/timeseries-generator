.PHONY: clean build

.EXPORT_ALL_VARIABLES:
CC_RED := $(shell echo '\033[0;31m')
CC_YELLOW := $(shell echo '\033[0;33m')
CC_GREEN := $(shell echo '\033[0;32m')
CC_NC := $(shell echo '\033[0;0m')

clean:
		@echo "$(CC_GREEN)cleaning build artifacts$(CC_NC)"
		rm -rf timeseries_generator.egg-info
		rm -rf dist
		rm -rf build

build: clean
		@echo "$(CC_GREEN)building python package$(CC_NC)"
		python -m build

test:
		pytest tests