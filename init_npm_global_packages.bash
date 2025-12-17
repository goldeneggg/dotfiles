#!/bin/bash

###
### initial setup npm packages for Mac
###

source ./_npm_global_pkgs

npm i -g npm
npm -v
for pkg in ${MY_NPM_GLOBAL_PKGS[@]}
do
  npm install -g ${pkg}
done

