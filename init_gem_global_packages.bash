#!/bin/bash

###
### initial setup gem packages for Mac
###

gem --version

source ./_gem_global_pkgs

for pkg in ${MY_GEM_GLOBAL_PKGS[@]}
do
  gem install ${pkg}
done

