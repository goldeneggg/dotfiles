# dotfiles

Personal dotfiles managed with [GNU Stow](https://www.gnu.org/software/stow/), supporting both **macOS** and **Linux**.

## What's Included

| Tool | Description |
|------|-------------|
| **zsh** | Modular config (`.zshrc.prompt`, `.zshrc.fzf`, `.zshrc.aliases`, etc.) |
| **tmux** | Split config with TPM plugin manager |
| **Neovim** | Modern setup with vim-plug |
| **Git** | Template-based config with global gitignore generation |
| **AI tools** | Skills and rules for AI coding assistants |

### Package Management

- **[Homebrew](https://brew.sh/)** — system packages (see [`_brew_pkgs`](./_brew_pkgs))
- **[asdf](https://asdf-vm.com/)** — runtime versions (Node.js, Python, Ruby, Terraform)
- **npm / pip / uv / gem** — language-specific packages

## Prerequisites

- macOS or Linux
- [GNU Stow](https://www.gnu.org/software/stow/)
- [Homebrew](https://brew.sh/) (macOS only)
- Git

## Installation

> **Warning**: Review the code before running. These are *my* personal settings — they will overwrite your existing configs.

```sh
# 1. Clone
git clone https://github.com/goldeneggg/dotfiles.git ~/dotfiles
cd ~/dotfiles

# 2. Install Homebrew packages (macOS only)
make install-brew-pkgs

# 3. Run setup (creates symlinks, configures git, installs plugins)
make setup
```

## Usage

### Regular Updates

```sh
make reset              # Update dotfiles (skip go install)
make reset-with-goget   # Update dotfiles with go install
make work               # Full upgrade: asdf + rust + gems + pips + npms + brew
```

### Package Installation

```sh
make init-npms          # npm global packages
make init-pips          # pip global packages
make init-gems          # gem global packages
make init-projects      # Clone personal GitHub projects
```

### Version Management (asdf)

```sh
make asdf-upgrade             # Upgrade Node.js, Python, Ruby, Terraform
make asdf-uninstall-all       # Remove old versions
make asdf-uninstall-selected  # Interactive removal via fzf
```

### Homebrew (macOS)

```sh
make install-brew-pkgs   # Initial install
make upgrade-brew-pkgs   # Upgrade packages
```

### Other

```sh
make install-op-cli          # Install 1Password CLI (GPG verified)
make skill-repo-add-all      # Add external AI skills
make skill-repo-update-all   # Update external AI skills
```

## How It Works

### Directory Convention

```text
<tool>-linux/     # Linux configs — mirrors $HOME structure
<tool>-mac/       # macOS configs — mirrors $HOME structure
```

GNU Stow creates symlinks from these directories into `$HOME`:

```sh
stow -R --verbose=2 zsh-linux
# Creates: ~/.zshrc -> dotfiles/zsh-linux/.zshrc
```

Mac configs can symlink to Linux versions for shared components:

```text
git-mac/.gitconfig -> ../git-linux/.gitconfig
```

### Setup Process

1. Stow all `*-linux/` or `*-mac/` directories (creates symlinks)
2. Replace `%GITHUB_USER%` / `%GITHUB_MAIL%` placeholders in `.gitconfig`
3. Generate `.gitignore_global` from [github/gitignore](https://github.com/github/gitignore) templates
4. Install tmux plugin manager (TPM) and base16-shell

## Customization

Personal or machine-specific configs go in `~/.personal/` — this directory is not tracked by git.

## Notes

- SSH keys must be set up before `make init-projects`
- Run `asdf reshim <lang>` after installing packages to update PATH
- M1 Mac: `/opt/homebrew` / Intel Mac: `/usr/local`

## License

MIT
