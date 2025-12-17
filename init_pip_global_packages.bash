#!/bin/bash

###
### initial setup npm packages for Mac
###

source ./_pip_global_pkgs
pip install --upgrade pip
pip --version
# Note: 2025-08-23: 3.13へのupgradeでopen-interpreterのインストールがエラーになるので、pkgsファイルから一旦削除している
# See: https://github.com/openinterpreter/open-interpreter/issues/1539
for pkg in ${MY_PIP_GLOBAL_PKGS[@]}
do
  pip install --upgrade ${pkg}
done

source ./_uv_global_pkgs
pip install --upgrade uv
uv --version
for pkg in ${MY_UV_GLOBAL_PKGS[@]}
do
  uv tool install --upgrade ${pkg}
done
