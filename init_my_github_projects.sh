#!/bin/bash

### 
### setup github projects
### Note: setup ssh keys before execute this script
### 

if [ ! -d ${HOME}/github ]
then
  mkdir -p ${HOME}/github/goldeneggg
  git clone git@github.com:goldeneggg/pages.gi ~/github/goldeneggg/pages
  git clone git@github.com:goldeneggg/goldeneggg.github.io.gi ~/github/goldeneggg/goldeneggg.github.io
  git clone git@github.com:goldeneggg/vagrant-vms.gi ~/github/goldeneggg/vagrant-vms
  git clone git@github.com:goldeneggg/provisioning-bash.gi ~/github/goldeneggg/provisioning-bash

  mkdir -p ${HOME}/github/practice-goldeneggg
  git clone git@github.com:practice-goldeneggg/apex-lambdas.gi ~/github/practice-goldeneggg/apex-lambdas
fi

echo ""
echo "---------------------------------------------------------"
echo "Success!"
echo "---------------------------------------------------------"

exit 0
