#!/bin/bash

### 
### setup github projects
### Note: setup ssh keys before execute this script
### 



GITHUB_HOME=${HOME}/github/goldeneggg
if [ ! -d ${GITHUB_HOME} ]
then
  mkdir -p ${GITHUB_HOME}
fi
cd ${GITHUB_HOME} 
PJTS=( \
  "pages" \
  "goldeneggg.github.io" \
  "hugo-coder" \
  "goldeneggg" \
  "misc-aws" \
  "misc-puppets" \
  "misc-alfred-workflow" \
  "misc-gas" \
  "provisioning-bash" \
)
for pjt in ${PJTS[@]}
do
  git clone git@github.com:goldeneggg/${pjt}
done

cd ${HOME}
HOMEPJTS=( \
  "mysnippets" \
  "myautomator" \
)
for pjt in ${HOMEPJTS[@]}
do
  git clone git@github.com:goldeneggg/${pjt}
done

echo ""
echo "---------------------------------------------------------"
echo "Success!"
echo "---------------------------------------------------------"

exit 0
