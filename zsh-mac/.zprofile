echo "---------- loaded .zprofile"

# See: https://zenn.dev/tet0h/articles/a92651d52bd82460aefb
# 20250403: /opt/homebrew/bin がPATHの先頭になってしまって.zshenv.pathの設定が無意味になってしまっているので、
# コメントアウトした
# if [[ "${IS_M1_MAC}" == "true" ]]
# then
#   eval "$(/opt/homebrew/bin/brew shellenv)"
# fi
