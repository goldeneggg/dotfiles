#!/bin/sh

###
### initial setup homebrew and brew tools for Mac
###

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
  "diff-so-fancy" \
  "cmake" \
  "readline" \
  "ctags" \
  "reattach-to-user-namespace" \
  "urlview" \
  "extract_url" \
  "libevent" \
  "htop" \
  "pstree")
for app in ${APPS[@]}
do
  brew install ${app}
done

# dupes
brew tap homebrew/dupes
declare -ar DUPES_APPS=("grep")
for app in ${DUPES_APPS[@]}
do
  brew install homebrew/dupes/${app}
done

# highway
brew tap tkengo/highway
brew install highway


exit 0
