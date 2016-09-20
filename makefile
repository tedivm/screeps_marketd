
SHELL:=/bin/bash
ROOT_DIR:=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

.PHONY: all fresh dependencies install fulluninstall uninstall removedeps


all: dependencies

fresh: fulluninstall dependencies

fulluninstall: uninstall cleancode

install:
	# Create link in /usr/local/bin to screeps marketd program.
	ln -s -f $(ROOT_DIR)/bin/screepsmarketd.sh /usr/local/bin/screepsmarketd

	# Create link in /usr/local/bin to standalone service controller.
	ln -s -f $(ROOT_DIR)/bin/screepsmarketdctl.sh /usr/local/bin/screepsmarketdctl

	# Create screepsmarketd user- including home directory- for daemon
	id -u screepsmarketd &>/dev/null || useradd screepsmarketd --create-home --shell /bin/false -U

	# Move service file into place- note that symlinks will not work (bug 955379)
	if [ -d /etc/systemd/system ]; then \
		cp $(ROOT_DIR)/provisioning/etc/systemd/system/screepsmarketd.service /etc/systemd/system/screepsmarketd.service; \
		systemctl enable screepsmarketd.service; \
		systemctl start screepsmarketd.service; \
	fi;

dependencies:
	if [ ! -d $(ROOT_DIR)/env ]; then virtualenv $(ROOT_DIR)/env; fi
	source $(ROOT_DIR)/env/bin/activate; yes w | pip install -r $(ROOT_DIR)/requirements.txt

uninstall:
	# Remove user and home.
	if getent passwd screepsmarketd > /dev/null 2>&1; then \
		pkill -9 -u `id -u screepsmarketd`; \
		deluser --remove-home screepsmarketd; \
	fi
	# Remove screepsmarketd link in /user/local/bin
	if [ -L /usr/local/bin/screepsmarketd.sh ]; then \
		rm /usr/local/bin/screepsmarketd; \
	fi;
	# Remove screepsmarketdctl in /user/local/bin
	if [ -L /usr/local/bin/screepsmarketdctl.sh ]; then \
		rm /usr/local/bin/screepsmarketdctl; \
	fi;
	# Shut down, disbale, and remove all services.
	if [ -L /etc/systemd/system/screepsmarketd.service ]; then \
		systemctl disable screepsmarketd.service; \
		systemctl stop screepsmarketd.service; \
		rm /etc/systemd/system/screepsmarketd.service; \
	fi;

cleancode:
	# Remove existing environment
	if [ -d $(ROOT_DIR)/env ]; then \
		rm -rf $(ROOT_DIR)/env; \
	fi;
	# Remove compiled python files
	if [ -d $(ROOT_DIR)/screeps_marketd ]; then \
		rm -f $(ROOT_DIR)/screeps_marketd/*.pyc; \
	fi;
