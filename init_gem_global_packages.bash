#!/bin/bash

###
### initial setup gem packages for Mac
###

source ./_gem_global_pkgs

gem update --system
gem --version
for pkg in ${MY_GEM_GLOBAL_PKGS[@]}
do
  gem install ${pkg}
done

