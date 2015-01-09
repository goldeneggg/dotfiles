#!/bin/sh

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
                if [ -f ~/${f} ]
                then
                    echo "already exist ${f} in HOME"
                    rm ~/${f}
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
#    else
#        echo "$0: github user or GITHUB_USER env value is not assigned"
#        exit 1
    fi
fi

if [ ! ${GH_M} ]
then
    # if --github-mail option is not specified, check GITHUB_MAIL env value
    if [ ${GITHUB_MAIL} ]
    then
        GH_M=${GITHUB_MAIL}
#    else
#        echo "$0: github user or GITHUB_MAIL env value is not assigned"
#        exit 1
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
    install `ls -1F | grep "/" | grep -v -- ${SIGN}`
    install `ls -1F | grep "/" | grep -- ${SIGN}`
else
    install ${NAME}${SIGN}${VERSION}
fi

# for neobundle.vim
git submodule update --init

# install vim plugins
/usr/bin/vim -e -S vim-linux/init.ex

# replace token of .gitconfig
cp ~/.gitconfig ~/.gitconfig.org
rm ~/.gitconfig
cp ~/.gitconfig.org ~/.gitconfig
sed -i -e "s/%GITHUB_USER%/${GH_U}/g" ~/.gitconfig
sed -i -e "s/%GITHUB_MAIL%/${GH_M}/g" ~/.gitconfig


echo ""
echo "---------------------------------------------------------"
echo "Next step:"
echo "  - 'chsh -s zsh' : execute 'chsh' from original shell to zsh"
echo "  - install screen ver 4.2 later"
echo "  - convert to 256 colors of terminal"
echo "---------------------------------------------------------"

exit 0
