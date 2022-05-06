#!/bin/bash

###
### initial setup homebrew and brew tools for Mac
###

# install commandline for homebrew
#ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

function ins() {
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

  # iterm2 shell integration
  # See: https://www.iterm2.com/documentation-shell-integration.html
  curl -L https://iterm2.com/shell_integration/zsh -o ~/.iterm2_shell_integration.zsh
  echo 'Installed iterm2_shell_integration. Check your .zsrhc "source ~/.iterm2_shell_integration.zsh" setting.'
}

function upd() {
  for app in ${MY_BREW_PKGS[@]}
  do
    brew upgrade ${app}
  done
}

source ./_brew_pkgs

brew update

MODE="${1}"

if [[ "${MODE}" = "install" ]]
then
  ins
else
  upd
fi
