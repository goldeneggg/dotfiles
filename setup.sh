#!/bin/bash

### 
### setup dotfiles using GNU Stow
### 

usage() {
    cat << __EOT__
Usage: $0 <-LM> <--github-user GITHUB_USER> <--github-mail GITHUB_MAIL>  [-n <NAME>] [-v <VERSION>]
Configuration setup script

Options:
  -L | --linux                    target is Linux (default)
  -M | --mac                      target is Mac
  -n | --name NAME                target name
  -v | --version VERSION          target version
  --github-user GITHUB_USER       user account on github (default: "GITHUB_USER" env value)
  --github-mail GITHUB_MAIL       user mail address on github (default: "GITHUB_MAIL" env value)
  -h | --help                     print a summary of the options

__EOT__
}

install() {
  SETTINGS=$@
  for setting in `echo ${SETTINGS}`
  do
    pushd ${setting}
    for f in `ls -a`
    do
      if [ "${f}" != "." -a "${f}" != ".."  ]
      then
        if [ -f ${HOME}/${f} ]
        then
          echo "already exist ${f} in HOME"
          rm ${HOME}/${f}
        fi
      fi
    done
    popd
    s=`echo ${setting} | sed -e "s/\///g"`
    stow -R --verbose=2 ${s}
  done
}

unset NAME VERSION GH_U GH_M
SIGN_LINUX="-linux"
SIGN_MAC="-mac"
SIGN="${SIGN_LINUX}"

while true
do
  case "$1" in
    -h | --help ) usage; exit 1 ;;
    -L | --linux ) SIGN=${SIGN_LINUX}; shift ;;
    -M | --mac ) SIGN=${SIGN_MAC}; shift ;;
    -n | --name ) NAME=$2; shift 2 ;;
    -v | --version ) VERSION="-"$2; shift 2 ;;
    --github-user ) GH_U=$2; shift 2 ;;
    --github-mail ) GH_M=$2; shift 2 ;;
    * ) break ;;
  esac
done

if [ "${SIGN}" != "${SIGN_LINUX}" -a "${SIGN}" != "${SIGN_MAC}" ]
then
  echo "$0: SIGN is not assigned"
  exit 1
fi

if [ ! ${GH_U} ]
then
  # if --github-user option is not specified, check GITHUB_USER env value
  if [ ${GITHUB_USER} ]
  then
    GH_U=${GITHUB_USER}
  else
    echo "$0: github user or GITHUB_USER env value is not assigned"
    exit 1
  fi
fi

if [ ! ${GH_M} ]
then
  # if --github-mail option is not specified, check GITHUB_MAIL env value
  if [ ${GITHUB_MAIL} ]
  then
    GH_M=${GITHUB_MAIL}
  else
    echo "$0: github user or GITHUB_MAIL env value is not assigned"
    exit 1
  fi
fi

if [ `which stow` ]
then
  echo "stow is OK"
else
  echo "stow is not installed, please try again later stow install"
  exit 1
fi


if [ "${NAME}" = "" ]
then
  if [ "${SIGN}" = "${SIGN_MAC}" ]
  then
    install `ls -1F | grep "/" | grep -v -- ${SIGN}`
    install `ls -1F | grep "/" | grep -- ${SIGN}`
  elif [ "${SIGN}" = "${SIGN_LINUX}" ]
  then
    install `ls -1F | grep "/" | grep -- ${SIGN}`
  fi
else
  install ${NAME}${SIGN}${VERSION}
fi

# for neobundle.vim
# TODO: remove after neovim migration
#git submodule update --init

# install vim plugins
## dependency for golang
if [ ! -z "${GOROOT}" ]
then
  export GOROOT=/usr/local/go
fi

if [ ! -z "${GOPATH}" ]
then
  export GOPATH=${HOME}/go
  if [ ! -d ${GOPATH} ]
  then
    mkdir -p ${GOPATH}
  fi
fi

# install go tools
if [ -x ${GOROOT}/bin/go ]
then
  PATH=${GOROOT}/bin:${PATH}
  go get github.com/nsf/gocode
  go get github.com/golang/lint
  go get -u github.com/golang/lint/golint
  go get -u golang.org/x/tools/cmd/goimports
  go get github.com/github/hub
  go get github.com/peco/peco
  go get github.com/peco/peco/cmd/peco
fi

## run ex commands
# TODO: change from vim to neovim
#/usr/bin/vim -e -S vim-linux/init.ex
if [ ! `which nvim` ]
then
  nvim -e -S nvim-linux/.config/nvim/init.ex
fi

# replace token of .gitconfig
GITFILE_SUFFIXS=("config" "ignore")
for gitfile_suffix in ${GITFILE_SUFFIXS[@]}
do
  cp ${HOME}/.git${gitfile_suffix} ${HOME}/.git${gitfile_suffix}.org
  rm ${HOME}/.git${gitfile_suffix}
  cp ${HOME}/.git${gitfile_suffix}.org ${HOME}/.git${gitfile_suffix}
  sed -i -e "s/%GITHUB_USER%/${GH_U}/g" ${HOME}/.git${gitfile_suffix}
  sed -i -e "s/%GITHUB_MAIL%/${GH_M}/g" ${HOME}/.git${gitfile_suffix}
done

# $HOME/bin
if [ ! -d ${HOME}/bin ]
then
  mkdir -p ${HOME}/bin
fi

# keychain
if [ ! `which keychain` ]
then
  KEYCHAIN_VER="2.8.3"
  KEYCHAIN_TAR=keychain-${KEYCHAIN_VER}.tar.bz2
  curl -L http://www.funtoo.org/distfiles/keychain/keychain-${KEYCHAIN_VER}.tar.bz2 -o ${KEYCHAIN_TAR}
  tar jxf ${KEYCHAIN_TAR}
  mv keychain-${KEYCHAIN_VER}/keychain ${HOME}/bin/
  mv keychain-${KEYCHAIN_VER}/keychain.pod ${HOME}/bin/
fi

# tmux plugin manager
if [ ! -d ${HOME}/.tmux/plugins ]
then
  mkdir -p ${HOME}/.tmux/plugins
  git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm

  # for tmux-resurrect
  mkdir -p ${HOME}/.tmux/resurrect
fi

echo ""
echo "---------------------------------------------------------"
echo "Success!"
echo "---------------------------------------------------------"

exit 0
