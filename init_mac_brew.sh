#!/bin/sh

###
### initial setup homebrew and brew tools for Mac
###

#ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

declare -ar APPS=("git" \
  "vim" \
  "wget" \
  "lv" \
  "ack" \
  "stow" \
  "zsh" \
  "cmake" \
  "readline" \
  "ctags" \
  "libevent" \
  "pstree")

for app in ${APPS[@]}
do
  brew install ${app}
done

exit 0
