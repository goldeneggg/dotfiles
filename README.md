# For Mac

## Initial Setup

```sh
% brew install stow

% git clone [this project] ~/dotfiles
% cd ~/dotfiles

# stow and symlink
% make setup-mac
```

## Setup packages

```sh
$ ./init_mac_packages.bash

# Note: require installed node.js using ndenv
$ ./init_npm_global_packages.bash
```

## Update "xxenv" projects

```sh
$ make update-xxenvs
```

