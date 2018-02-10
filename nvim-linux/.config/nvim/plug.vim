call plug#begin()

Plug 'jacoborus/tender.vim'
Plug 'itchyny/lightline.vim'
Plug 'ctrlpvim/ctrlp.vim'
Plug 'kana/vim-smartinput'
" Plug 'mattn/emmet-vim'  "zencodingの記法でHTMLやCSSの構造を書き, 「C-Y ,」でそれを展開 http://motw.mods.jp/Vim/emmet-vim.html
Plug 'fatih/vim-go'
Plug 'Shougo/deoplete.nvim', { 'do': ':UpdateRemotePlugins' }
Plug 'zchee/deoplete-go', { 'do': 'make'}  "require: go get -u github.com/nsf/gocode
" Plug 'SirVer/ultisnips'

call plug#end()
