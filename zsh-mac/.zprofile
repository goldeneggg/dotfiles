echo "---------- loaded .zprofile"

# See: https://zenn.dev/tet0h/articles/a92651d52bd82460aefb
if [[ "${IS_M1_MAC}" == "true" ]]
then
  eval "$(/opt/homebrew/bin/brew shellenv)"
fi
