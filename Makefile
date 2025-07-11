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
	@./brew_packages.bash install

# TODO: `gh extension upgrade gh-copilot` も実行したい
upgrade-brew-pkgs:
	@export _checkbrew=$(call assert-command,brew,See https://brew.sh/index_ja)
	@./brew_packages.bash
endif

# bashes
setup-bash = ./setup.bash -$1 --github-user goldeneggg --github-mail jpshadowapps@gmail.com $2

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

init-npms:
	@./init_npm_global_packages.bash && asdf reshim nodejs

init-pips:
	@./init_pip_global_packages.bash && asdf reshim python

init-gems:
	@./init_gem_global_packages.bash && asdf reshim ruby

init-projects:
	@./init_my_github_projects.bash

# DEPRECATED: これ以降のpyenv前提メモは全てDEPRECATED
# --- re-activate for neovim
# 1. Run this make target  ※このMakeをそのままmake実行しても途中でコケるので、手動実施する必要あり
# 2. Run `pip install flake8`
# 3. Run `nvim` -> `:UpdateRemotePlugin`
#
# "pyenv virtualenv -f VER neovimN" した後の "pyenv shell neovimN" が重要
# これを実施することでpyenv versionsした時に仮想環境もリストアップされるようになる
# => これにより、PYENV_ROOT/versions/neovimN というシムリンクが作成される（はず）
# neovimのconfigではこのシムリンクを参照してpythonの具体的なバージョン番号を指定しなくても良い形にしたい
#
# Note: ;UpdateRemotePlugin が Failed to load python3 host. You can try to see what happened by starting nvim with $NVIM_PYTHON_LOG_FILE set and opening the generated log file.
# 等のエラーになる場合は、neovimのconfigで "let g:python3_host_prog" で設定しているパスが誤っている可能性があるので見直す
#
# Note: Vim8の場合だと "Vim(pythonx):ModuleNotFoundError: No module named 'neovim'" というエラーになる
# pipで導入したpythonが無視されシステム？のpython3を使っている為、そのpython3でpynvimとneovimをpip installしないとダメ
# - Vim8を開いて :pyx print(sys.version); print(sys.path) を実行して、Vim8が使ってるpython3のバージョンとパスを確認
# - 確認したパスと関連しているフォルダの bin/python3.x を利用して "python3.x -m pip install {pynvim,neovim}" する
# - Vim8を開き直してエラーが解消されたか確認
# upgrade-python:
# 	@export _checkpyenv=$(call assert-command,pyenv,)
# 	@echo '>>>>>>>>>> Start python upgrade for neovim'
# 	@pyenv global $(ver3) $(ver2) && pyenv rehash
# 	@pyenv virtualenv -f $(ver3) neovim3
# 	@pyenv shell neovim3
# 	@pip install pynvim
# 	@pip install neovim
# 	@pyenv virtualenv -f $(ver2) neovim2
# 	@pyenv shell neovim2
# 	@pip install pynvim
# 	@pip install neovim

USEVER_NODEJS := 22
USEVER_PYTHON := 3.12
USEVER_RUBY := 3.4
USEVER_TERRAFORM := 1.12

asdf-latest = $(shell asdf latest $1 $2)

asdf-upgrade:
	@asdf plugin update --all
	@asdf install nodejs $(call asdf-latest,nodejs,$(USEVER_NODEJS).)
	@asdf set --home nodejs $(call asdf-latest,nodejs,$(USEVER_NODEJS).)
	@asdf reshim nodejs
	@asdf install python $(call asdf-latest,python,$(USEVER_PYTHON).)
	@asdf set --home python $(call asdf-latest,python,$(USEVER_PYTHON).)
	@asdf reshim python
	@asdf install ruby $(call asdf-latest,ruby,$(USEVER_RUBY).)
	@asdf set --home ruby $(call asdf-latest,ruby,$(USEVER_RUBY).)
	@asdf reshim ruby
	@asdf install terraform $(call asdf-latest,terraform,$(USEVER_TERRAFORM).)
	@asdf set --home terraform $(call asdf-latest,terraform,$(USEVER_TERRAFORM).)
	@asdf reshim terraform

asdf-uninstall-all-old-vers = for oldver in $$(asdf list $1 | \grep -v ' \*'); do echo uninstall $1 old version $${oldver}; asdf uninstall $1 $${oldver}; done
asdf-uninstall-all:
	@$(call asdf-uninstall-all-old-vers,nodejs)
	@$(call asdf-uninstall-all-old-vers,python)
	@$(call asdf-uninstall-all-old-vers,ruby)
	@$(call asdf-uninstall-all-old-vers,terraform)
	@asdf reshim

asdf-uninstall-selected-vers = asdf list $1 | fzf -m | awk '{print $$1}' | xargs -I {} sh -c 'echo "uninstall $1 {}..." && asdf uninstall $1 {}'
asdf-uninstall-selected:
	@$(call asdf-uninstall-selected-vers,nodejs)
	@$(call asdf-uninstall-selected-vers,python)
	@$(call asdf-uninstall-selected-vers,ruby)
	@$(call asdf-uninstall-selected-vers,terraform)
	@asdf reshim

rust-upgrade:
	@rustup update

work: asdf-upgrade rust-upgrade init-gems init-pips init-npms
	@brew update

# watch repos control
WATCH_REPO_ORG_DIR := $(HOME)/github/practice-goldeneggg
WATCHES := aws docker go wasm ai zig ruby rust graphql browser react
watch-repos-recursive = $(foreach wr,$(WATCHES),cd $(WATCH_REPO_ORG_DIR)/watch-$(wr) && echo "---------- $(wr)" && $1 || { echo "NG!"; true; };)

watches-sync:
	@$(call watch-repos-recursive,make sync)

watches-update-and-sync:
	@$(call watch-repos-recursive,make update-and-sync)

watches-git-diff-check:
	@$(call watch-repos-recursive,git diff --exit-code --quiet)
