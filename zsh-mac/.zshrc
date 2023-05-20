# 対話的に起動する場合にのみ必要な設定。シェルのオプションの設定。
# すべてのエイリアス・シェル関数・キー割り当て・補完動作の定義・プロンプトなどほぼすべての個人嗜好設定。

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

# asdf ( `echo -e "\n. $(brew --prefix asdf)/libexec/asdf.sh" >> ${ZDOTDIR:-~}/.zshrc` )
. $(brew --prefix asdf)/libexec/asdf.sh

#source /Users/fskmt/.docker/init-zsh.sh || true # Added by Docker Desktop
