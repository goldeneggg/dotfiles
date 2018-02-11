"==========
" Setup flow
"   1. curl -fLo ~/.local/share/nvim/site/autoload/plug.vim --create-dirs https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim
"   2. nvim
"   3. :PlugInstall
"==========

call plug#begin()

" view
Plug 'jacoborus/tender.vim'
Plug 'itchyny/lightline.vim'

" file search
Plug 'ctrlpvim/ctrlp.vim'

" code search
Plug 'rizzatti/dash.vim'

" edit
Plug 'kana/vim-smartinput' "対応カッコ自動閉じetc
Plug 'tyru/caw.vim'  "複数行コメントアウト. 複数行選択して gci でコメントアウトできる. gccでtoggle

" support language specification
Plug 'fatih/vim-go'
Plug 'sebdah/vim-delve'  " delve debugger support

" completion
Plug 'mattn/emmet-vim'  "zencodingの記法でHTMLやCSSの構造を書き, 「C-Y ,」でそれを展開 http://motw.mods.jp/Vim/emmet-vim.html
Plug 'Shougo/deoplete.nvim', { 'do': ':UpdateRemotePlugins' }
Plug 'zchee/deoplete-go', { 'do': 'make'}  "require: go get -u github.com/nsf/gocode
Plug 'Shougo/neosnippet.vim'
Plug 'Shougo/neosnippet-snippets'

call plug#end()
