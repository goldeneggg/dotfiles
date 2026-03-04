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

# Skill list: REPO|REPO_DIR|SKILL_NAME (pipe-separated tuples)
# Add new skills by appending entries to this list
SKILL_REPOS := \
	anthropics/skills|skills|skill-creator

# Helper functions to extract fields from pipe-separated tuples
skill-repo-of = $(word 1,$(subst |, ,$1))
skill-dir-of = $(word 2,$(subst |, ,$1))
skill-name-of = $(word 3,$(subst |, ,$1))

# Sparse checkout a skill from a github repo into a temp dir, then copy to AI_SKILLS_DIR
# Args: $1=repo, $2=repo_dir, $3=skill_name
define skill-sparse-checkout
	TEMP_DIR=$$(mktemp -d) && \
	git clone --depth 1 --filter=blob:none --sparse https://github.com/$1.git "$$TEMP_DIR" && \
	cd "$$TEMP_DIR" && \
	git sparse-checkout set $2/$3 && \
	cd - > /dev/null && \
	mkdir -p $(AI_SKILLS_DIR) && \
	cp -r "$$TEMP_DIR/$2/$3" $(AI_SKILLS_DIR)/ && \
	rm -rf "$$TEMP_DIR"
endef

# Batch add all skills in SKILL_REPOS (skips already-added skills, no auto-commit)
skill-repo-add-all:
	@$(foreach item,$(SKILL_REPOS), \
		if [ -d "$(AI_SKILLS_DIR)/$(call skill-name-of,$(item))" ]; then \
			echo "SKIP: $(call skill-name-of,$(item)) already exists"; \
		else \
			echo "ADD: $(call skill-name-of,$(item)) from $(call skill-repo-of,$(item))..." && \
			$(call skill-sparse-checkout,$(call skill-repo-of,$(item)),$(call skill-dir-of,$(item)),$(call skill-name-of,$(item))); \
		fi ;)

# Batch update all skills in SKILL_REPOS
skill-repo-update-all:
	@$(foreach item,$(SKILL_REPOS), \
		echo "UPDATE: $(call skill-name-of,$(item)) from $(call skill-repo-of,$(item))..." && \
		rm -rf $(AI_SKILLS_DIR)/$(call skill-name-of,$(item)) && \
		$(call skill-sparse-checkout,$(call skill-repo-of,$(item)),$(call skill-dir-of,$(item)),$(call skill-name-of,$(item))) ;)
