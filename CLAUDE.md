# dotfiles(GNU Stow-based config management)

This file provides guidance for AI coding assistants when working with code in this repository.

## Overview

A dotfiles repository using GNU Stow for symlink-based configuration management. Supports macOS (`-mac` suffix) and Linux (`-linux` suffix) with platform-specific directories.

## Initial Settings

The following skills must be assumed.

- @~/.claude/skills/security-awareness/SKILL.md

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
make work               # Full upgrade: asdf + rust + gems + pips + npms + brew update
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

### AI Skills Management

```sh
make skill-repo-add-all      # Batch add all external skills (skips existing)
make skill-repo-update-all   # Batch update all external skills
```

### Other Tools

```sh
make install-op-cli          # Install 1Password CLI with GPG verification
make watches-sync            # Sync all watch repos
make watches-update-and-sync # Update and sync all watch repos
make copilot-cli             # Launch Copilot CLI with MCP config
```

## Architecture

### Directory Convention

- `<tool>-linux/` and `<tool>-mac/` directories mirror home directory structure
- GNU Stow creates symlinks: `stow -R --verbose=2 <directory-name>`
- Mac configs may symlink to Linux versions for shared components (e.g., `git-mac/.gitconfig -> ../git-linux/.gitconfig`)
- Git submodules are used for external dependencies (`git submodule update --init --remote --recursive`)

### Configuration Structure

- **zsh**: Modular configs (`.zshrc.prompt`, `.zshrc.fzf`, `.zshrc.aliases`, etc.)
- **tmux**: Split into `.tmux.conf.basic`, `.tmux.conf.keybind`, `.tmux.conf.plugins`, etc.
- **neovim**: Modern setup in `nvim-linux/.config/nvim/` with vim-plug
- **vim**: Legacy setup with neobundle (deprecated)
- **git**: Template with `%GITHUB_USER%` and `%GITHUB_MAIL%` placeholders replaced during setup
- **AI tools**: `ai-linux/.claude/` for skills and rules, `Claude/` for desktop config

### Package Lists (source files)

- `_brew_pkgs` - Homebrew packages
- `_npm_global_pkgs` - npm global packages
- `_pip_global_pkgs` - pip packages
- `_uv_global_pkgs` - uv tools
- `_gem_global_pkgs` - Ruby gems

### Version Targets (in Makefile)

- Node.js: v24
- Python: v3.14
- Ruby: v4.0
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

## Coding Conventions

### Shell Scripts

- Shebang: Use `#!/bin/bash`
- Variable references: Prefer `${VAR}` format (with braces)
- File naming: snake_case (e.g., `init_npm_global_packages.bash`)
- Package list files: `_` prefix (e.g., `_brew_pkgs`)

### Directory Naming

- Must follow `<tool>-linux/` or `<tool>-mac/` format
- Tool names in lowercase without hyphens (e.g., `zsh-linux`, `nvim-linux`)

## AI Implementation Rules

### Basic Rules

- **Language**: All communication must be in **Japanese**
- **Confirmation First**: Always use AskUserQuestion tool to clarify uncertainties before proceeding
- **Information Gathering**: Collect the latest and most accurate information when gathering from external sources
- **Persistence**: Complete tasks thoroughly and persistently to the end

## Examples

### Adding a New Tool Configuration

```sh
# 1. Create directory (mirror home directory structure)
mkdir -p newtool-linux/.config/newtool/

# 2. Place config files
cp ~/.config/newtool/config.toml newtool-linux/.config/newtool/

# 3. Add as stow target in setup.bash
# Append to the stow command list in setup.bash

# 4. Create symlinks with stow
stow -R --verbose=2 newtool-linux
```

### Mac/Linux Shared Config Pattern

```text
# Good: Mac version symlinks to Linux version for sharing
git-mac/.gitconfig -> ../git-linux/.gitconfig

# Bad: Copying the same content to both (causes sync drift)
git-mac/.gitconfig  (independent copy)
git-linux/.gitconfig (independent copy)
```
