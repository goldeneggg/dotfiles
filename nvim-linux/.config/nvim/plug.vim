"==========
" Neovim Setup flow
"   1. curl -fLo ~/.local/share/nvim/site/autoload/plug.vim --create-dirs https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim
"   2. nvim
"   3. :PlugInstall
"==========

call plug#begin()

" view
Plug 'jacoborus/tender.vim'
Plug 'itchyny/lightline.vim'

" file finder
Plug 'ctrlpvim/ctrlp.vim'
Plug 'tacahiroy/ctrlp-funky'

Plug 'Shougo/denite.nvim'

" code information
Plug 'rizzatti/dash.vim'
Plug 'tpope/vim-fugitive'  "git

" edit
Plug 'kana/vim-smartinput' "対応カッコ自動閉じetc
Plug 'tyru/caw.vim'  "複数行コメントアウト. 複数行選択して gci でコメントアウトできる. gccでtoggle
Plug 'Shougo/context_filetype.vim'  "See: https://github.com/posva/vim-vue#how-to-use-commenting-functionality-with-multiple-languages-in-vue-files<Paste>
Plug 'tpope/vim-surround'
Plug 'tpope/vim-endwise'  "自動でend入力
Plug 'vim-scripts/yanktmp.vim'  "別プロセスで開いてるファイルにヤンク・ペースト
Plug 'AndrewRadev/splitjoin.vim'  "gJ で行結合 or gS で行分割

" support language specification
Plug 'fatih/vim-go'
Plug 'jodosha/vim-godebug'
Plug 'sebdah/vim-delve'  "delve debugger support
Plug 'kchmck/vim-coffee-script'
Plug 'othree/javascript-libraries-syntax.vim'  "https://vimawesome.com/plugin/javascript-libraries-syntax
Plug 'posva/vim-vue'  "https://vimawesome.com/plugin/vim-vue-fearless
Plug 'tpope/vim-rails'
Plug 'thoughtbot/vim-rspec'

" completion
Plug 'mattn/emmet-vim'  "zencodingの記法でHTMLやCSSの構造を書き, 「C-Y ,」でそれを展開 http://motw.mods.jp/Vim/emmet-vim.html
Plug 'Shougo/deoplete.nvim', { 'do': ':UpdateRemotePlugins' }
Plug 'zchee/deoplete-go', { 'do': 'make'}  "require: go get -u github.com/nsf/gocode
Plug 'Shougo/neosnippet.vim'
Plug 'Shougo/neosnippet-snippets'
Plug 'Shougo/neomru.vim'
Plug 'ternjs/tern_for_vim', { 'do': 'npm install && npm install -g tern' } "https://vimawesome.com/plugin/tern-for-vim-state-of-grace

call plug#end()
