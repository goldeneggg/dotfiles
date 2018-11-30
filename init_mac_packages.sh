#!/bin/sh

###
### initial setup homebrew and brew tools for Mac
###

# install commandline for homebrew
#ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

brew update

declare -ar APPS=("git" \
  "vim" \
  "neovim" \
  "zsh" \
  "tmux" \
  "wget" \
  "lv" \
  "ack" \
  "jq" \
  "the_silver_searcher" \
  "tkengo/highway/highway" \
  "stow" \
  "grep" \
  "yarn" \
  "diff-so-fancy" \
  "cmake" \
  "readline" \
  "tree" \
  "zlib" \
  "ctags" \
  "reattach-to-user-namespace" \
  "urlview" \
  "awscli" \
  "extract_url" \
  "libevent" \
  "htop" \
  "ipcalc" \
  "pstree")
for app in ${APPS[@]}
do
  brew install ${app}
done

# highway
brew tap tkengo/highway
brew install highway

# aws
brew tap aws/tap
brew install aws-sam-cli

# rbenv
git clone https://github.com/rbenv/rbenv.git ~/.rbenv
mkdir ~/.rbenv/plugins
git clone https://github.com/rbenv/ruby-build.git ~/.rbenv/plugins/ruby-build

# pyenv
git clone https://github.com/pyenv/pyenv.git ~/.pyenv
git clone https://github.com/pyenv/pyenv-virtualenv.git ~/.pyenv/plugins/pyenv-virtualenv
git clone https://github.com/pyenv/pyenv-doctor.git ~/.pyenv/plugins/pyenv-doctor

# ndenv
git clone https://github.com/riywo/ndenv.git ~/.ndenv
mkdir ~/.ndenv/plugins
git clone https://github.com/riywo/node-build.git ~/.ndenv/plugins/node-build

# apex
curl https://raw.githubusercontent.com/apex/apex/master/install.sh | sh

exit 0
