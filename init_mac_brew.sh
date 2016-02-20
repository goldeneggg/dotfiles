#!/bin/sh

###
### initial setup homebrew and brew tools for Mac
###

#ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

brew update

declare -ar APPS=("git" \
  "vim" \
  "wget" \
  "lv" \
  "ack" \
  "stow" \
  "zsh" \
  "diff-so-fancy" \
  "cmake" \
  "readline" \
  "ctags" \
  "libevent" \
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


exit 0
