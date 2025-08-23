#!/bin/bash

###
### initial setup npm packages for Mac
###

pip --version

source ./_pip_global_pkgs

# Note: 2025-08-23: 3.13へのupgradeでopen-interpreterのインストールがエラーになるので、pkgsファイルから一旦削除している
# See: https://github.com/openinterpreter/open-interpreter/issues/1539
for pkg in ${MY_PIP_GLOBAL_PKGS[@]}
do
  pip install --upgrade ${pkg}
done

