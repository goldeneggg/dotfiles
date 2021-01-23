#!/bin/bash

###
### initial setup npm packages for Mac
###

pip --version

source ./_pip_global_pkgs

for pkg in ${MY_PIP_GLOBAL_PKGS[@]}
do
  pip install --upgrade ${pkg}
done

