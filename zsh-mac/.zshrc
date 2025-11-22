# 対話的に起動する場合にのみ必要な設定。シェルのオプションの設定。
# すべてのエイリアス・シェル関数・キー割り当て・補完動作の定義・プロンプトなどほぼすべての個人嗜好設定。

echo "---------- loaded .zshrc"

source ~/.zshrc.oscommon

source ~/.zshrc.vcs
source ~/.zshrc.prompt
source ~/.zshrc.gitpjt
source ~/.zshrc.tmux
source ~/.zshrc.grep
source ~/.zshrc.golang
source ~/.zshrc.ssh
source ~/.zshrc.aliases
#source ~/.zshrc.base16

#- using fzf if exists
if [[ -x "$(command -v fzf)" ]]
then
  source ~/.zshrc.fzf
fi

#- 個人のその端末専用のローカルな設定を ~/.personal に配置
if [[ -d ~/.personal ]]
then
  for f in `ls -d ~/.personal/*`
  do
    source ${f}
  done
fi

# maconly settings
source ~/.zshrc.maconly.autojump
source ~/.zshrc.maconly.symlink
source ~/.zshrc.maconly.virtualbox
source ~/.zshrc.maconly.vscode
source ~/.zshrc.maconly.vagrant
source ~/.zshrc.maconly.vagrant-coreos

source ~/.iterm2_shell_integration.zsh

# fix: 2025/02: asdf最新バージョンで libexec/asdf.sh が無くなっているので修正
# See: https://asdf-vm.com/guide/getting-started.html
# 上記Seeに合わせて、以下は不要なのでコメントアウト
# . $(brew --prefix asdf)/libexec/asdf.sh

#source /Users/fskmt/.docker/init-zsh.sh || true # Added by Docker Desktop

# The next line updates PATH for the Google Cloud SDK.
if [ -f "$HOME/google-cloud-sdk/path.zsh.inc" ]; then . "$HOME/google-cloud-sdk/path.zsh.inc"; fi

# The next line enables shell command completion for gcloud.
if [ -f "$HOME/google-cloud-sdk/completion.zsh.inc" ]; then . "$HOME/google-cloud-sdk/completion.zsh.inc"; fi


# Added by Antigravity
export PATH="$HOME/.antigravity/antigravity/bin:$PATH"
