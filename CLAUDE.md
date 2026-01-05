# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a dotfiles repository using **GNU Stow** for symlink-based configuration management. Supports macOS (`-mac` suffix) and Linux (`-linux` suffix) with platform-specific directories.

## Commands

### Initial Setup (new machine)

```sh
# macOS only - requires Homebrew pre-installed
make install-brew-pkgs

# Main setup (prompts for GitHub credentials)
make setup
```

### Regular Updates

```sh
make reset              # Update dotfiles (skip go install)
make reset-with-goget   # Update dotfiles with go install
```

### Package Installation

```sh
make init-npms      # npm global packages (see _npm_global_pkgs)
make init-pips      # pip global packages (see _pip_global_pkgs)
make init-gems      # gem global packages (see _gem_global_pkgs)
make init-projects  # Clone personal GitHub projects
```

### Version Management (asdf)

```sh
make asdf-upgrade           # Upgrade Node.js, Python, Ruby, Terraform
make asdf-uninstall-all     # Remove old versions
make asdf-uninstall-selected  # Interactive removal via fzf
```

### Homebrew (macOS)

```sh
make install-brew-pkgs   # Initial install
make upgrade-brew-pkgs   # Upgrade packages
```

## Architecture

### Directory Convention

- `<tool>-linux/` and `<tool>-mac/` directories mirror home directory structure
- GNU Stow creates symlinks: `stow -R --verbose=2 <directory-name>`
- Mac configs may symlink to Linux versions for shared components (e.g., `git-mac/.gitconfig -> ../git-linux/.gitconfig`)

### Configuration Structure

- **zsh**: Modular configs (`.zshrc.prompt`, `.zshrc.fzf`, `.zshrc.aliases`, etc.)
- **tmux**: Split into `.tmux.conf.basic`, `.tmux.conf.keybind`, `.tmux.conf.plugins`, etc.
- **neovim**: Modern setup in `nvim-linux/.config/nvim/` with vim-plug
- **vim**: Legacy setup with neobundle (deprecated)
- **git**: Template with `%GITHUB_USER%` and `%GITHUB_MAIL%` placeholders replaced during setup

### Package Lists (source files)

- `_brew_pkgs` - Homebrew packages
- `_npm_global_pkgs` - npm global packages
- `_pip_global_pkgs` - pip packages + uv tools
- `_gem_global_pkgs` - Ruby gems

### Version Targets (in Makefile)

- Node.js: v24
- Python: v3.14
- Ruby: v3.4
- Terraform: v1.14

## Key Files

- `setup.bash` - Main installation script (handles stow, git config, TPM, base16-shell)
- `Makefile` - Command orchestration
- `brew_packages.bash` - Homebrew install/upgrade
- `init_*_packages.bash` - Language-specific package installers

## Notes

- SSH keys must be set up before `make init-projects`
- `asdf reshim <lang>` required after installing packages to update PATH
- Personal/machine-specific configs go in `~/.personal/` directory
- M1 Mac uses `/opt/homebrew`, Intel Mac uses `/usr/local`

## AI Implementation Rules

### Basic Rules

- **Language**: All communication must be in **Japanese**
- **Confirmation First**: Always use AskUserQuestion tool to clarify uncertainties before proceeding
- **Information Gathering**: Collect the latest and most accurate information when gathering from external sources
- **Persistence**: Complete tasks thoroughly and persistently to the end

### Post-Implementation Workflow

```text
Implementation Complete
        │
        ▼
┌───────────────────────────────────┐
│ Step 1: Post-Implementation Review│
│ Run /post-impl-validator          │
│ → Proceed after user approval     │
└───────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────┐
│ Step 2: Commit                    │
│ cd to the changed repository and  │
│ commit the results                │
│ → Proceed after user approval     │
└───────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────┐
│ Step 3: Documentation Update      │
│ Update task documents,            │
│ design documents, etc.            │
└───────────────────────────────────┘
```

**After completing each step, always obtain user approval before proceeding to the next.**
