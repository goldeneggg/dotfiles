# ~/.profile: executed by the command interpreter for login shells.
# This file is not read by bash(1), if ~/.bash_profile or ~/.bash_login
# exists.
# see /usr/share/doc/bash/examples/startup-files for examples.
# the files are located in the bash-doc package.

# the default umask is set in /etc/profile; for setting the umask
# for ssh logins, install and configure the libpam-umask package.
#umask 022

ZSH=`which zsh`
ZSH_OPT=-l

if [[ -x $ZSH ]]
then
    export SHELL=$ZSH
    exec $ZSH $ZSH_OPT
else
    ## original bashrc content
    # if running bash
    if [[ -n "$BASH_VERSION" ]]
    then
        # include .bashrc if it exists
        if [[ -f "$HOME/.bashrc" ]]
        then
        . "$HOME/.bashrc"
        fi
    fi
    # set PATH so it includes user's private bin if it exists
    if [[ -d "$HOME/bin" ]]
    then
        PATH="$HOME/bin:$PATH"
    fi
fi
. "$HOME/.cargo/env"

#source /Users/fskmt/.docker/init-bash.sh || true # Added by Docker Desktop
