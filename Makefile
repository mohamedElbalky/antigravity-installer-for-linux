.PHONY: all install update check status test uninstall clean

all: install

install:
	@./install.sh

update:
	@./update.sh

check:
	@./update.sh check

status:
	@./update.sh status

test:
	@python3 -m unittest discover -s tests -p "test_*.py"

uninstall:
	@./update.sh uninstall

clean:
	@rm -rf ~/.cache/antigravity-installer/downloads/*.part
	@find . -type d -name "__pycache__" -exec rm -rf {} +
