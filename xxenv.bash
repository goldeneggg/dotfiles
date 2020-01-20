#!/bin/bash

###
#
# Initialize:
#   ./xxenv.bash
# Update:
#   ./xxenv.bash update
#
###

function xxenv() {
  local e=${1}
  local m=${2}

  local u=https://github.com/${e}
  local t=~/.${e##*/}

  if [ "${m}" = "update" ]
  then
    pushd ${t}
    git pull --rebase origin master
    popd
    echo "UPDATED ${t}"
  else
    git clone ${u} ${t}
    echo "CLONED ${u} ${t}"
  fi
}

function xxenvPlug() {
  local e=${1}
  local m=${2}

  local plugs
  local u
  local t

  # plugin definitions
  case ${e} in
    "rbenv/rbenv")
      plugs=("rbenv/ruby-build")
      ;;
    "pyenv/pyenv")
      plugs=("pyenv/python-build" "pyenv/pyenv-virtualenv" "pyenv/pyenv-doctor")
      ;;
    "riywo/ndenv")
      plugs=("riywo/node-build")
      ;;
    "phpenv/phpenv")
      plugs=("php-build/php-build")
      ;;
  esac

  for p in ${plugs[@]}
  do
    u=https://github.com/${p}

    [ ! -d ~/.${e##*/}/plugins ] && mkdir -p ~/.${e##*/}/plugins
    t=~/.${e##*/}/plugins/${p##*/}

    if [ "${m}" = "update" ]
    then
      pushd ${t}
      git pull --rebase origin master
      popd
      echo "UPDATED ${t}"
    else
      git clone ${u} ${t}
      echo "CLONED ${u} ${t}"
    fi
  done
}

MODE="${1}"
XXENVS=("rbenv/rbenv" "pyenv/pyenv" "riywo/ndenv" "phpenv/phpenv")
for xxenv in ${XXENVS[@]}
do
  xxenv ${xxenv} ${MODE}
  xxenvPlug ${xxenv} ${MODE}
done

