# ログインシェルとして使うときだけでなく, リモートシェル起動のときなどすべての局面で有効とすべき設定を記述する。
# 以下のようなものが該当する。
#  1.コマンド検索パス($PATH)の定義
#  2.リモートホストから直接起動する可能性があるコマンドに関する設定やエイリアス・シェル関数の定義
#  3.2が参照する環境変数等の設定(cvsやrsyncのための変数など）

# m1 mac or not ("true" or "false")
if [[ "$(uname -m)" = "arm64" ]]
then
  export IS_M1_MAC="true"
else
  export IS_M1_MAC="false"
fi

setopt no_global_rcs

source ~/.zshenv.path
source ~/.zshenv.aws

. "$HOME/.cargo/env"
