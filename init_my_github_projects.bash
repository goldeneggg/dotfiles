#!/bin/bash

### 
### setup github projects
### Note: setup ssh keys before execute this script
### 

GITHUB_HOME=${HOME}/github/goldeneggg
GITHUB_PRAC_HOME=${HOME}/github/practice-goldeneggg

if [ ! -d ${GITHUB_HOME} ]
then
  mkdir -p ${GITHUB_HOME}
  cd ${GITHUB_HOME} 
  git clone git@github.com:goldeneggg/pages
  git clone git@github.com:goldeneggg/goldeneggg.github.io
  git clone git@github.com:goldeneggg/vagrant-vms
  git clone git@github.com:goldeneggg/provisioning-bash

  cd ${HOME}
  git clone git@github.com:goldeneggg/mysnippets
  git clone git@github.com:goldeneggg/myautomator
fi

echo ""
echo "---------------------------------------------------------"
echo "Success!"
echo "---------------------------------------------------------"

exit 0
