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
# 1. Run this make target  ※このMakeをそのままmake実行しても途中でコケるので、手動実施する必要あり
# 2. Run `pip install flake8`
# 3. Run `nvim` -> `:UpdateRemotePlugin`
#
# "pyenv virtualenv -f VER neovimN" した後の "pyenv shell neovimN" が重要。これを実施することでpyenv versionsした時に仮想環境もリストアップされるようになる
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
upgrade-python:
	@export _checkpyenv=$(call assert-command,pyenv,)
	@echo '>>>>>>>>>> Start python upgrade for neovim'
	@read -p 'Input python3 version?: ' ver3; read -p 'Input python2 version?: ' ver2; \
		pyenv global $$ver3 $$ver2 && \
		pyenv rehash && \
		pyenv virtualenv -f $$ver3 neovim3 && \
		pyenv shell neovim3 && \
		pip install pynvim && \
		pip install neovim && \
		pyenv virtualenv -f $$ver2 neovim2 && \
		pyenv shell neovim2 && \
		pip install pynvim && \
		pip install neovim 
