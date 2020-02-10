# required command detection
assert-command = $(if $(shell hash $1 2>&1),$(error '$1' command is missing. $2),)
$(call assert-command,curl,)
$(call assert-command,git,)

# OS confirmation
OSFLG := L

ifeq ($(shell uname),Darwin)
OSFLG := M

install-brew-pkgs:
	@export _checkbrew=$(call assert-command,brew,See https://brew.sh/index_ja)
	@./init_mac_packages.bash
endif

# bashes
setup-bash = ./setup.bash -$1 --github-user goldeneggg --github-mail jpshadowapps@gmail.com $2
xxenv-bash = ./xxenv.bash $1

###
# targets
###

make-version:
	@echo $(MAKE_VERSION)

check-osflg:
	@echo $(OSFLG)

setup: init-gitsubmodule reset-with-goget

reset: update-gitsubmodule
	@$(call setup-bash,$(OSFLG),--skip-goget)

reset-with-goget: update-gitsubmodule
	@$(call setup-bash,$(OSFLG),)

init-gitsubmodule:
	@git submodule update --init --remote --recursive

update-gitsubmodule:
	@git submodule update --remote --recursive

init-xxenvs:
	@$(call xxenv-bash,)

update-xxenvs:
	@$(call xxenv-bash,update)

init-npms:
	@./init_npm_global_packages.bash

init-projects:
	@./init_my_github_projects.bash

# --- re-activate for neovim
# 1. Run this make target
# 2. Run `pip install flake8`
# 3. Run `nvim` -> `:UpdateRemotePlugin`
upgrade-python:
	@export _checkpyenv=$(call assert-command,pyenv,)
	@echo '>>>>>>>>>> Start python upgrade for neovim'
	@read -p 'Input python3 version?: ' ver3; read -p 'Input python2 version?: ' ver2; \
		pyenv global $$ver3 && \
		pyenv rehash && \
		pip3 install --user pynvim && \
		pyenv virtualenv -f $$ver3 neovim3 && \
		pyenv activate neovim3 && \
		pip install pynvim && \
		pip install neovim && \
		pyenv deactivate neovim3 && \
		pyenv global $$ver2 && \
		pyenv rehash && \
		pip2 install --user pynvim && \
		pyenv virtualenv -f $$ver2 neovim2 && \
		pyenv activate neovim2 && \
		pip install pynvim && \
		pip install neovim && \
		pyenv deactivate neovim2 && \
