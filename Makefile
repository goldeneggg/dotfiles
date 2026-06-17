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

# ----------
# install tools and libraries without package managers
# ----------
# 1Password CLI
USEVER_OP_CLI := 2.32.1
# GPG key for 1Password CLI signature verification
OP_CLI_GPG_KEY := 3FEF9748469ADBE15DA7CA80AC2D62742012EA22

# Install 1Password CLI with GPG signature verification
install-op-cli:
	@echo "Installing 1Password CLI v$(USEVER_OP_CLI)..."
	@TEMP_DIR=$$(mktemp -d) && \
	trap 'rm -rf "$$TEMP_DIR"' EXIT && \
	curl -sSfL "https://cache.agilebits.com/dist/1P/op2/pkg/v$(USEVER_OP_CLI)/op_darwin_arm64_v$(USEVER_OP_CLI).zip" -o "$$TEMP_DIR/op.zip" && \
	unzip -q "$$TEMP_DIR/op.zip" -d "$$TEMP_DIR" && \
	gpg --keyserver hkps://keyserver.ubuntu.com --receive-keys $(OP_CLI_GPG_KEY) && \
	gpg --verify "$$TEMP_DIR/op.sig" "$$TEMP_DIR/op" && \
	mkdir -p $(HOME)/bin && \
	mv "$$TEMP_DIR/op" $(HOME)/bin/op && \
	test -x $(HOME)/bin/op || chmod 755 $(HOME)/bin/op && \
	echo "1Password CLI v$(USEVER_OP_CLI) installed successfully at $(HOME)/bin/op"
endif

# ----------
# repository watching
# ----------
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
# if REPO_DIR is ".", it means the skill is located at the root of the repo
EXTERNAL_SKILL_REPOS := \
	1Password/SCAM|skills|security-awareness

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

# Batch add all skills in EXTERNAL_SKILL_REPOS (skips already-added skills, no auto-commit)
skill-repo-add-all:
	@$(foreach item,$(EXTERNAL_SKILL_REPOS), \
		if [ -d "$(AI_SKILLS_DIR)/$(call skill-name-of,$(item))" ]; then \
			echo "SKIP: $(call skill-name-of,$(item)) already exists"; \
		else \
			echo "ADD: $(call skill-name-of,$(item)) from $(call skill-repo-of,$(item))..." && \
			$(call skill-sparse-checkout,$(call skill-repo-of,$(item)),$(call skill-dir-of,$(item)),$(call skill-name-of,$(item))); \
		fi ;)

# Batch update all skills in EXTERNAL_SKILL_REPOS
skill-repo-update-all:
	@$(foreach item,$(EXTERNAL_SKILL_REPOS), \
		echo "UPDATE: $(call skill-name-of,$(item)) from $(call skill-repo-of,$(item))..." && \
		rm -rf $(AI_SKILLS_DIR)/$(call skill-name-of,$(item)) && \
		$(call skill-sparse-checkout,$(call skill-repo-of,$(item)),$(call skill-dir-of,$(item)),$(call skill-name-of,$(item))) ;)

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

.PHONY: sync-claudemd-to-agentsmd
sync-claudemd-to-agentsmd: ## CLAUDE.md を再帰的に探索し、同ディレクトリに AGENTS.md symlink を作成する
	@find . -name "CLAUDE.md" -not -path "*/.git/*" -not -path "*/node_modules/*" | while read f; do \
		dir=$$(dirname "$$f"); \
		ln -sf CLAUDE.md "$$dir/AGENTS.md"; \
		echo "Created: $$dir/AGENTS.md -> CLAUDE.md"; \
	done

# ----------
# AI tools MCP configuration sync
# ----------
CLAUDE_MCP_JSON := ./.mcp.json
CODEX_CONFIG_DIR := ./.codex
CODEX_CONFIG_FILE := $(CODEX_CONFIG_DIR)/config.toml

define SYNC_MCP_TO_CODEX_SCRIPT
import json, os, re

src = "$(CLAUDE_MCP_JSON)"
dst = "$(CODEX_CONFIG_FILE)"

with open(src) as f:
    cfg = json.load(f)

servers = cfg.get("mcpServers", {})
lines = []
for name, srv in servers.items():
    lines.append("[mcp_servers.{}]".format(name))
    cmd_expanded = os.path.expandvars(srv.get("command", ""))
    cmd = os.path.basename(cmd_expanded) if cmd_expanded else srv.get("command", "")
    lines.append('command = "{}"'.format(cmd))
    args = srv.get("args", [])
    if args:
        args_toml = ", ".join('"{}"'.format(a) for a in args)
        lines.append("args = [{}]".format(args_toml))
    lines.append('env_vars = ["PATH"]')
    env = srv.get("env", {})
    if env:
        lines.append("[mcp_servers.{}.env]".format(name))
        for k, v in env.items():
            lines.append('{} = "{}"'.format(k, v))
    lines.append("")

new_section = "\n".join(lines)
marker_begin = "# sync-mcp-begin\n"
marker_end = "# sync-mcp-end\n"

existing = open(dst).read() if os.path.exists(dst) else ""
cleaned = re.sub(r"\n*# sync-mcp-begin\n.*?# sync-mcp-end\n?", "", existing, flags=re.DOTALL).strip()
content = (cleaned + "\n\n" if cleaned else "") + marker_begin + new_section + marker_end

with open(dst, "w") as f:
    f.write(content)

print("Synced {} MCP servers to {}".format(len(servers), dst))
for name in servers:
    print("  - " + name)
endef
export SYNC_MCP_TO_CODEX_SCRIPT

.PHONY: sync-claude-mcpconf-to-codex
sync-claude-mcpconf-to-codex: ## Claude Code の .mcp.json を Codex の ~/.codex/config.toml の mcp_servers セクションに同期する
	@[ -f "$(CLAUDE_MCP_JSON)" ] || { echo "Error: $(CLAUDE_MCP_JSON) not found"; exit 1; }
	@mkdir -p "$(CODEX_CONFIG_DIR)"
	@echo "$$SYNC_MCP_TO_CODEX_SCRIPT" | python3


# ----------
# AI tools subagents configuration sync
# ----------
CLAUDE_AGENTS_DIR := ./ai-linux/.claude/agents
CODEX_AGENTS_DIR := ./ai-linux/.codex/agents

define SYNC_SUBAGENTS_TO_CODEX_SCRIPT
import os, glob, re

src_dir = "$(CLAUDE_AGENTS_DIR)"
dst_dir = "$(CODEX_AGENTS_DIR)"

# 再生成のたびに孤児(.toml)が残らないよう、出力先の .toml を一旦すべて削除する
for old in glob.glob(os.path.join(dst_dir, "*.toml")):
    os.remove(old)


def parse_frontmatter(text):
    # 先頭の --- ... --- を frontmatter、それ以降を本文として分離する
    m = re.match(r"^---\n(.*?)\n---\n?(.*)\Z", text, re.DOTALL)
    if not m:
        return None, ""
    return m.group(1), m.group(2)


def parse_fields(fm):
    # PyYAML 非依存の簡易パーサ。トップレベルの key: value と
    # ブロックスカラー(| / >)のみを対象とする(tools 等のリストは無視)
    lines = fm.split("\n")
    data = {}
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        m = re.match(r"^([A-Za-z_]+):\s?(.*)\Z", line)
        if not m or line[:1] == " ":
            i += 1
            continue
        key = m.group(1)
        val = m.group(2).strip()
        if val in ("|", "|-", "|+", ">", ">-", ">+"):
            # ブロックスカラー: 後続のインデント行を集めて共通インデントを除去する
            i += 1
            raw = []
            while i < n:
                bl = lines[i]
                if bl.strip() == "":
                    raw.append("")
                    i += 1
                    continue
                if bl[:1] == " ":
                    raw.append(bl)
                    i += 1
                else:
                    break
            indents = [len(x) - len(x.lstrip(" ")) for x in raw if x.strip()]
            ind = min(indents) if indents else 0
            block = [(x[ind:] if len(x) >= ind else x) for x in raw]
            while block and block[-1] == "":
                block.pop()
            data[key] = "\n".join(block)
        else:
            # インラインのクオートを除去する
            if len(val) >= 2 and ((val[0] == '"' and val[-1] == '"') or (val[0] == "'" and val[-1] == "'")):
                val = val[1:-1]
            data[key] = val
            i += 1
    return data


files = sorted(glob.glob(os.path.join(src_dir, "*.md")))
count = 0
for path in files:
    fname = os.path.basename(path)
    with open(path) as f:
        text = f.read()
    fm, body = parse_frontmatter(text)
    if fm is None:
        print("  ! skip {}: frontmatter not found".format(fname))
        continue
    fields = parse_fields(fm)
    name = fields.get("name", "").strip()
    desc = fields.get("description", "").strip()
    body = body.strip()
    # Codex の必須3項目(name/description/developer_instructions)を担保する
    if not name:
        print("  ! skip {}: missing name".format(fname))
        continue
    if not body:
        print("  ! skip {}: empty body (developer_instructions)".format(fname))
        continue
    # TOML 複数行 literal string は ''' を内包できないため、含む場合は手動対応に回す
    if ("'''" in desc) or ("'''" in body):
        print("  ! skip {}: contains triple single-quote, needs manual handling".format(fname))
        continue
    out = []
    out.append('name = "{}"'.format(name))
    out.append("description = '''\n{}\n'''".format(desc))
    out.append("developer_instructions = '''\n{}\n'''".format(body))
    content = "\n".join(out) + "\n"
    dst = os.path.join(dst_dir, name + ".toml")
    with open(dst, "w") as f:
        f.write(content)
    print("  - {} -> {}".format(fname, dst))
    count += 1

print("Synced {} subagents to {}".format(count, dst_dir))
endef
export SYNC_SUBAGENTS_TO_CODEX_SCRIPT

.PHONY: sync-claude-subagents-to-codex
sync-claude-subagents-to-codex: ## Claude Code の .claude/agents/*.md を Codex の .codex/agents/*.toml に変換同期する
	@[ -d "$(CLAUDE_AGENTS_DIR)" ] || { echo "Error: $(CLAUDE_AGENTS_DIR) not found"; exit 1; }
	@mkdir -p "$(CODEX_AGENTS_DIR)"
	@echo "$$SYNC_SUBAGENTS_TO_CODEX_SCRIPT" | python3
