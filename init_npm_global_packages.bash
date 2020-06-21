#!/bin/bash

###
### initial setup npm packages for Mac
###

npm -v

source ./_npm_global_pkgs

for pkg in ${MY_NPM_GLOBAL_PKGS[@]}
do
  npm install -g ${pkg}
done

