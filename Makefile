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

# bashes
setup-bash = ./setup.bash -$1 --github-user goldeneggg --github-mail jpshadowapps@gmail.com $2

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

rust-upgrade:
	@rustup update

work: asdf-upgrade rust-upgrade init-gems init-pips init-npms
	@brew update

# ----------
# homebrew
# ----------
install-brew-pkgs:
	@export _checkbrew=$(call assert-command,brew,See https://brew.sh/index_ja)
	@./brew_packages.bash install

# TODO: `gh extension upgrade gh-copilot` も実行したい
upgrade-brew-pkgs:
	@export _checkbrew=$(call assert-command,brew,See https://brew.sh/index_ja)
	@./brew_packages.bash

# ----------
# asdf
# ----------
USEVER_NODEJS := 26
USEVER_PYTHON := 3.14
USEVER_RUBY := 4.0
USEVER_TERRAFORM := 1.15

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

asdf-uninstall-all:
	@./scripts/asdf_uninstall_old_versions.bash nodejs python ruby terraform
	@asdf reshim

asdf-uninstall-selected:
	@./scripts/asdf_uninstall_selected_versions.bash nodejs python ruby terraform
	@asdf reshim

# ----------
# install tools and libraries without package managers
# ----------
# 1Password CLI
USEVER_OP_CLI := 2.32.1
# GPG key for 1Password CLI signature verification
OP_CLI_GPG_KEY := 3FEF9748469ADBE15DA7CA80AC2D62742012EA22

# Install 1Password CLI with GPG signature verification
install-op-cli:
	@./scripts/install_op_cli.bash $(USEVER_OP_CLI) $(OP_CLI_GPG_KEY)
endif

# ----------
# repository watching
# ----------
# watch repos control
WATCH_REPO_ORG_DIR := $(HOME)/github/practice-goldeneggg
WATCHES := ai aws browser docker go react ruby wasm zig

watches-sync:
	@./scripts/watch_repos_exec.bash $(WATCH_REPO_ORG_DIR) "make sync" $(WATCHES)

watches-update-and-sync:
	@./scripts/watch_repos_exec.bash $(WATCH_REPO_ORG_DIR) "make update-and-sync" $(WATCHES)

watches-git-diff-check:
	@./scripts/watch_repos_exec.bash $(WATCH_REPO_ORG_DIR) "git diff --exit-code --quiet" $(WATCHES)

# ----------
# for AI skills management
# ----------
AI_SKILLS_DIR := ./ai-linux/.claude/skills

# Skill list: REPO|REPO_DIR|SKILL_NAME (pipe-separated tuples)
# Add new skills by appending entries to this list
# if REPO_DIR is ".", it means the skill is located at the root of the repo
EXTERNAL_SKILL_REPOS := \
	1Password/SCAM|skills|security-awareness

# Batch add all skills in EXTERNAL_SKILL_REPOS (skips already-added skills, no auto-commit)
skill-repo-add-all:
	@./scripts/skill_repo_manage.bash add-all $(AI_SKILLS_DIR) $(EXTERNAL_SKILL_REPOS)

# Batch update all skills in EXTERNAL_SKILL_REPOS
skill-repo-update-all:
	@./scripts/skill_repo_manage.bash update-all $(AI_SKILLS_DIR) $(EXTERNAL_SKILL_REPOS)

#------------------------------
# for AI coding
#------------------------------
copilot-cli:
	@copilot --additional-mcp-config @.copilot/mcp-config.json \
		--allow-tool 'shell(cat)' \
		--allow-tool 'shell(head)' \
		--allow-tool 'shell(tail)' \
		--allow-tool 'shell(sort)' \
		--allow-tool 'shell(uniq)' \
		--allow-tool 'shell(grep)' \
		--allow-tool 'shell(rg)' \
		--allow-tool 'shell(find)' \
		--allow-tool 'shell(pwd)' \
		--allow-tool 'shell(ls)' \
		--allow-tool 'shell(tree)' \
		--allow-tool 'shell(wc)' \
		--allow-tool 'shell(stat)' \
		--allow-tool 'shell(file)' \
		--allow-tool 'shell(cd)' \
		--allow-tool 'shell(date)' \
		--allow-tool 'shell(whoami)' \
		--allow-tool 'shell(uname)' \
		--allow-tool 'shell(id)' \
		--allow-tool 'shell(gh issue list)' \
		--allow-tool 'shell(gh issue status)' \
		--allow-tool 'shell(gh issue view)' \
		--allow-tool 'shell(gh pr diff)' \
		--allow-tool 'shell(gh pr list)' \
		--allow-tool 'shell(gh pr status)' \
		--allow-tool 'shell(gh pr view)' \
		--allow-tool 'shell(git branch)' \
		--allow-tool 'shell(git diff)' \
		--allow-tool 'shell(git show)' \
		--allow-tool 'shell(git log)' \
		--allow-tool 'shell(git status)' \
		--allow-tool 'shell(git add)' \
		--deny-tool 'shell(sudo)' \
		--deny-tool 'shell(git commit)' \
		--deny-tool 'shell(git push)' \
		--allow-url github.com

# ----------
#
# Sync settings from Claude to Codex
#
# ----------

# ----------
# sync Contexts
# ----------
.PHONY: sync-claudemd-to-agentsmd
sync-claudemd-to-agentsmd: ## CLAUDE.md を再帰的に探索し、同ディレクトリに AGENTS.md symlink を作成する
	@./scripts/sync_claudemd_to_agentsmd.bash "$(or $(DIR),.)"

# ----------
# sync MCP configurations
# ----------
ifdef DIR
CLAUDE_MCP_JSON  := $(DIR)/.mcp.json
CODEX_CONFIG_DIR := $(DIR)/.codex
else
CLAUDE_MCP_JSON  := ./.mcp.json
CODEX_CONFIG_DIR := ./.codex
endif
CODEX_CONFIG_FILE := $(CODEX_CONFIG_DIR)/config.toml

.PHONY: sync-claude-mcpconf-to-codex
sync-claude-mcpconf-to-codex: ## Claude Code の .mcp.json を Codex の config.toml の mcp_servers セクションに同期する
	@[ -f "$(CLAUDE_MCP_JSON)" ] || { echo "Error: $(CLAUDE_MCP_JSON) not found"; exit 1; }
	@mkdir -p "$(CODEX_CONFIG_DIR)"
	@python3 ./scripts/sync_mcp_to_codex.py "$(CLAUDE_MCP_JSON)" "$(CODEX_CONFIG_FILE)"

# ----------
# sync Permissions
# ----------
ifdef DIR
CLAUDE_PERMISSIONS_SETTINGS_JSON := $(DIR)/.claude/settings.json
CODEX_PERMISSIONS_DIR           := $(DIR)/.codex
else
CLAUDE_PERMISSIONS_SETTINGS_JSON := ./ai-linux/.claude/settings.json
CODEX_PERMISSIONS_DIR           := ./ai-linux/.codex
endif
CODEX_PERMISSIONS_CONFIG_FILE := $(CODEX_PERMISSIONS_DIR)/config.toml
CODEX_PERMISSIONS_RULES_FILE  := $(CODEX_PERMISSIONS_DIR)/rules/default.rules

.PHONY: sync-claude-permissions-to-codex
sync-claude-permissions-to-codex: ## Claude Code の permissions を Codex の config.toml と rules/default.rules に同期する
	@[ -f "$(CLAUDE_PERMISSIONS_SETTINGS_JSON)" ] || { echo "Error: $(CLAUDE_PERMISSIONS_SETTINGS_JSON) not found"; exit 1; }
	@mkdir -p "$(CODEX_PERMISSIONS_DIR)" "$(CODEX_PERMISSIONS_DIR)/rules"
	@python3 ./scripts/sync_claude_permissions_to_codex.py "$(CLAUDE_PERMISSIONS_SETTINGS_JSON)" "$(CODEX_PERMISSIONS_CONFIG_FILE)" "$(CODEX_PERMISSIONS_RULES_FILE)"

# ----------
# sync Subagents
# ----------
ifdef DIR
CLAUDE_AGENTS_DIR := $(DIR)/.claude/agents
CODEX_AGENTS_DIR  := $(DIR)/.codex/agents
else
CLAUDE_AGENTS_DIR := ./ai-linux/.claude/agents
CODEX_AGENTS_DIR  := ./ai-linux/.codex/agents
endif

.PHONY: sync-claude-subagents-to-codex
sync-claude-subagents-to-codex: ## Claude Code の .claude/agents/*.md を Codex の .codex/agents/*.toml に変換同期する
	@[ -d "$(CLAUDE_AGENTS_DIR)" ] || { echo "Error: $(CLAUDE_AGENTS_DIR) not found"; exit 1; }
	@mkdir -p "$(CODEX_AGENTS_DIR)"
	@python3 ./scripts/sync_subagents_to_codex.py "$(CLAUDE_AGENTS_DIR)" "$(CODEX_AGENTS_DIR)"
