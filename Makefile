# List all subdirectories that contain a Makefile
SUBDIRS := engine

# Define a target for each subdirectory
.PHONY: all $(SUBDIRS)

# Default target: build all subdirectories
all: $(SUBDIRS)

# Target to recursively call make in each subdirectory
$(SUBDIRS):
	@echo "Entering directory $@"
	$(MAKE) -C $@
	@echo "Leaving directory $@"

