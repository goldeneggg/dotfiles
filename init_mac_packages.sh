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
  "bash" \
  "zsh" \
  "tmux" \
  "wget" \
  "lv" \
  "gawk" \
  "ack" \
  "jq" \
  "the_silver_searcher" \
  "tkengo/highway/highway" \
  "stow" \
  "grep" \
  "yarn" \
  "cookiecutter" \
  "diff-so-fancy" \
  "cmake" \
  "direnv" \
  "readline" \
  "tree" \
  "travis" \
  "zlib" \
  "icu4c" \
  "ctags" \
  "reattach-to-user-namespace" \
  "urlview" \
  "awscli" \
  "extract_url" \
  "libevent" \
  "libmcrypt" \
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

# base16-manager
# Note: shellとvimでしか使わないのでmanagerは使わず個別にインストールする
# brew tap chrokh/tap
# brew install base16-manager

declare -ar CASKS=("aws-vault")
for caskapp in ${CASKS[@]}
do
  brew cask install ${caskapp}
done

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

# phpenv
git clone https://github.com/phpenv/phpenv.git ~/.phpenv
mkdir ~/.phpenv/plugins
git clone https://github.com/php-build/php-build ~/.phpenv/plugins/php-build

# apex
curl https://raw.githubusercontent.com/apex/apex/master/install.sh | sh

exit 0
