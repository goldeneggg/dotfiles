SHELL := /bin/bash

# required command detection
assert-command = $(if $(shell hash $1 2>&1),$(error '$1' command is missing. $2),)
$(call assert-command,curl,)
$(call assert-command,git,)

assert-var = $(if $($1),,$(error $1 variable is not assigned))

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

USEVER_NODEJS := 24
USEVER_PYTHON := 3.14
USEVER_RUBY := 3.4
USEVER_TERRAFORM := 1.14

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
WATCHES := ai aws browser docker go react ruby wasm zig
watch-repos-recursive = $(foreach wr,$(WATCHES),cd $(WATCH_REPO_ORG_DIR)/watch-$(wr) && echo "---------- $(wr)" && $1 || { echo "NG!"; true; };)

watches-sync:
	@$(call watch-repos-recursive,make sync)

watches-update-and-sync:
	@$(call watch-repos-recursive,make update-and-sync)

watches-git-diff-check:
	@$(call watch-repos-recursive,git diff --exit-code --quiet)

# ----------
# for AI skills management
# ----------
AI_SKILLS_DIR := ./ai-linux/.claude/skills

cc-skill-subtree-add:
	@$(call assert-var,REPO)
	@$(call assert-var,GH_REMOTE)
	@$(call assert-var,NAME)
	@$(call assert-var,REPO_DIR)
	@TEMP_DIR=$$(mktemp -d) && \
		git clone --depth 1 --filter=blob:none --sparse https://github.com/${REPO}.git "$$TEMP_DIR" && \
		cd "$$TEMP_DIR" && \
		git sparse-checkout set $(REPO_DIR)/$(NAME) && \
		cd - > /dev/null && \
		mkdir -p $(AI_SKILLS_DIR) && \
		cp -r "$$TEMP_DIR/$(REPO_DIR)/$(NAME)" $(AI_SKILLS_DIR)/ && \
		rm -rf "$$TEMP_DIR" && \
		git add $(AI_SKILLS_DIR)/$(NAME) && \
		git commit -m "Add $(NAME) skill from $(REPO)"

cc-official-skill-subtree-add: REPO := anthropics/skills
cc-official-skill-subtree-add: GH_REMOTE := anthropics-skills
cc-official-skill-subtree-add: REPO_DIR := skills
cc-official-skill-subtree-add: cc-skill-subtree-add

cc-skill-subtree-update:
	@$(call assert-var,REPO)
	@$(call assert-var,GH_REMOTE)
	@$(call assert-var,NAME)
	@$(call assert-var,REPO_DIR)
	@TEMP_DIR=$$(mktemp -d) && \
		git clone --depth 1 --filter=blob:none --sparse https://github.com/${REPO}.git "$$TEMP_DIR" && \
		cd "$$TEMP_DIR" && \
		git sparse-checkout set $(REPO_DIR)/$(NAME) && \
		cd - > /dev/null && \
		rm -rf $(AI_SKILLS_DIR)/$(NAME) && \
		mkdir -p $(AI_SKILLS_DIR) && \
		cp -r "$$TEMP_DIR/$(REPO_DIR)/$(NAME)" $(AI_SKILLS_DIR)/ && \
		rm -rf "$$TEMP_DIR"

cc-official-skill-subtree-update: REPO := anthropics/skills
cc-official-skill-subtree-update: GH_REMOTE := anthropics-skills
cc-official-skill-subtree-update: REPO_DIR := skills
cc-official-skill-subtree-update: cc-skill-subtree-update
