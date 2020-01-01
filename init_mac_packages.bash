#!/bin/bash

###
### initial setup homebrew and brew tools for Mac
###

# install commandline for homebrew
#ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

source ./_brew_pkgs

brew update

for tap in ${MY_BREW_TAPS[@]}
do
  brew tap ${tap}
done

for app in ${MY_BREW_PKGS[@]}
do
  brew install ${app}
done

# base16-manager
# Note: shellとvimでしか使わないのでmanagerは使わず個別にインストールする
# brew tap chrokh/tap
# brew install base16-manager

declare -ar CASKS=("aws-vault")
for caskapp in ${CASKS[@]}
do
  brew cask install ${caskapp}
done
