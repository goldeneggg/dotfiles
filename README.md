## Setup

```sh
git clone [this project] ~/dotfiles
cd ~/dotfiles

# for Mac only
# *require to install Homebrew. See: https://brew.sh/index_ja
make install-brew-pkgs

make setup
```

## Install npm global packages

```sh
make init-npms
```

## Setup my projects

```sh
make init-projects
```

## Update

### dotfiles

```sh
make reset

# skip "go get" as follows
make reset-skip-goget
```
