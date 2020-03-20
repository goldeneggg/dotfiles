#!/bin/bash

### 
### setup dotfiles using GNU Stow
### 

usage() {
  cat << EOT
Usage: $0 <-LM> <--github-user GITHUB_USER> <--github-mail GITHUB_MAIL>  [-n <NAME>] [-v <VERSION>]
Configuration setup script

Options:
  -L | --linux                    target is Linux (default)
  -M | --mac                      target is Mac
  -n | --name NAME                target name
  -v | --version VERSION          target version
  --github-user GITHUB_USER       user account on github (default: "GITHUB_USER" env value)
  --github-mail GITHUB_MAIL       user mail address on github (default: "GITHUB_MAIL" env value)
  --skip-goget                    skip go get commands
  -h | --help                     print a summary of the options

EOT
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

unset NAME VERSION GH_U GH_M SKIP_GOGET
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
    --skip-goget ) SKIP_GOGET="true"; shift ;;
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
    install `ls -1F | \grep "/" | \grep -v -- ${SIGN}`
    install `ls -1F | \grep "/" | \grep -- ${SIGN}`
  elif [ "${SIGN}" = "${SIGN_LINUX}" ]
  then
    install `ls -1F | \grep "/" | \grep -- ${SIGN}`
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
  if [ "${SKIP_GOGET}" != "true" ]
  then
    PATH=${GOROOT}/bin:${PATH}
    # go get -v github.com/github/hub
    # go get -v github.com/peco/peco
    # go get -v github.com/peco/peco/cmd/peco

    # go get -v -u github.com/cweill/gotests
    # go get -v -u golang.org/x/tools/cmd/goimports
    # go get -v -u github.com/golang/lint/golint
    # go get -v github.com/golang/lint
    # go get -v -u golang.org/x/tools/cmd/gopls
    go get -v -u github.com/mgechev/revive
    go get -v -u gopkg.in/alecthomas/gometalinter.v2
  fi
fi

## run ex commands
# TODO: change from vim to neovim
#/usr/bin/vim -e -S vim-linux/init.ex
if [ ! `which nvim` ]
then
  nvim -e -S nvim-linux/.config/nvim/init.ex
fi

# replace token of .gitconfig
cp ${HOME}/.gitconfig ${HOME}/.gitconfig.org
rm ${HOME}/.gitconfig
cp ${HOME}/.gitconfig.org ${HOME}/.gitconfig
sed -i -e "s/%GITHUB_USER%/${GH_U}/g" ${HOME}/.gitconfig
sed -i -e "s/%GITHUB_MAIL%/${GH_M}/g" ${HOME}/.gitconfig

# setup .gitignore_global
GH_GLOBAL_IGNORE=${HOME}/.gitignore_global
if [ -f ${GH_GLOBAL_IGNORE} ]
then
  rm -f ${GH_GLOBAL_IGNORE}
fi

GLOBAL_IGNORE_TARGETS=( \
  "Backup" \
  "Diff" \
  "Dropbox" \
  "Linux" \
  "Mercurial" \
  "Patch" \
  "Redis" \
  "SVN" \
  "Tags" \
  "Vagrant" \
  "Vim" \
  "VisualStudioCode" \
  "Xcode" \
  "macOS" \
)
for t in ${GLOBAL_IGNORE_TARGETS[@]}
do
  ignore_src=https://raw.githubusercontent.com/github/gitignore/master/Global/${t}.gitignore
  echo "#----- ${t}. See: ${ignore_src}" >> ${GH_GLOBAL_IGNORE}
  curl -s ${ignore_src} >> ${GH_GLOBAL_IGNORE}
  echo "" >> ${GH_GLOBAL_IGNORE}
done

# See: https://qiita.com/vzvu3k6k/items/12aff810ea93c7c6f307
ORG_IGNORE_TARGETS=( \
  ".envrc" \  
  "Gemfile.local" \  
  "Gemfile.local.lock" \  
  ".solargraph.yml" \  
)

echo "#----- original global .gitignores" >> ${GH_GLOBAL_IGNORE}
for ot in ${ORG_IGNORE_TARGETS[@]}
do
  echo "${ot}" >> ${GH_GLOBAL_IGNORE}
done

# $HOME/bin
if [ ! -d ${HOME}/bin ]
then
  mkdir -p ${HOME}/bin
fi

# keychain
if [ ! `which keychain` ]
then
  KEYCHAIN_VER="2.8.5"
  KEYCHAIN_ZIP=keychain-${KEYCHAIN_VER}.zip
  curl -s -L -o ${KEYCHAIN_TAR} https://github.com/funtoo/keychain/archive/${KEYCHAIN_ZIP}
  unzip ${KEYCHAIN_ZIP}
  mv keychain-${KEYCHAIN_VER}/keychain ${HOME}/bin/
  mv keychain-${KEYCHAIN_VER}/keychain.pod ${HOME}/bin/
  rm -fr keychain-${KEYCHAIN_VER}/
fi

# tmux plugin manager
if [ ! -d ${HOME}/.tmux/plugins ]
then
  mkdir -p ${HOME}/.tmux/plugins
  git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm

  # for tmux-resurrect
  mkdir -p ${HOME}/.tmux/resurrect
fi
pushd ${HOME}/.tmux/plugins
git pull --rebase origin master
popd

# # install or refresh mongo-hacker
# if [ -f ${HOME}/.mongorc.js ]
# then
#   rm -f ${HOME}/.mongorc.js
# fi
#
# if [ ! -d ${HOME}/mongo-hacker ]
# then
#   git clone https://github.com/goldeneggg/mongo-hacker.git ${HOME}/mongo-hacker
# fi
# pushd ${HOME}/mongo-hacker
# git pull --rebase origin master
# make
# make install
# popd

# install base16
if [ ! -d ${HOME}/.config/base16-shell ]
then
  mkdir -p ${HOME}/.config
  git clone https://github.com/chriskempson/base16-shell.git ${HOME}/.config/base16-shell
fi
pushd ${HOME}/.config/base16-shell
git pull --rebase origin master
popd

echo ""
echo "---------------------------------------------------------"
echo "Success!"
echo "---------------------------------------------------------"

exit 0
