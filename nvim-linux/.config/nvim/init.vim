"==========
" Neovim Setup flow
"   1. curl -fLo ~/.local/share/nvim/site/autoload/plug.vim --create-dirs https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim
"   2. nvim
"   3. :PlugInstall
"==========

" 基本設定
source $HOME/.config/nvim/basic.vim
source $HOME/.config/nvim/keymaps.vim
source $HOME/.config/nvim/encoding.vim

" プラグイン
source $HOME/.config/nvim/plug.vim

" カラースキーム
source $HOME/.config/nvim/colorscheme.vim

" ステータスバー
source $HOME/.config/nvim/lightline.vim

" yanktmp
source $HOME/.config/nvim/yanktmp.vim

" ファイル検索
source $HOME/.config/nvim/ctrlp.vim

" 補完（闇）
source $HOME/.config/nvim/deoplete.vim

" Dash連携
source $HOME/.config/nvim/dash.vim

" 言語別
source $HOME/.config/nvim/golang.vim  " Golang, deoplete-go
source $HOME/.config/nvim/vue.vim  " Vue.js

" スニペット
source $HOME/.config/nvim/neosnippet.vim

" denite
source $HOME/.config/nvim/denite.vim
