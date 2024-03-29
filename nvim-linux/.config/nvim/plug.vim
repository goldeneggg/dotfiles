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
Plug 'chriskempson/base16-vim'

" file finder
Plug 'ctrlpvim/ctrlp.vim'
Plug 'tacahiroy/ctrlp-funky'
Plug 'Shougo/denite.nvim'
Plug 'junegunn/fzf', { 'do': { -> fzf#install() } }
" FIXME: UpdateRemotePluginでエラーになるのでコメントアウト中
" Plug 'yuki-yano/fzf-preview.vim', { 'branch': 'release/rpc' }

" code information
Plug 'rizzatti/dash.vim'
Plug 'tpope/vim-fugitive'  "git
Plug 'airblade/vim-gitgutter'

" edit
Plug 'kana/vim-smartinput' "対応カッコ自動閉じetc
Plug 'tyru/caw.vim'  "複数行コメントアウト. 複数行選択して gci でコメントアウトできる. gccでtoggle
Plug 'Shougo/context_filetype.vim'  "See: https://github.com/posva/vim-vue#how-to-use-commenting-functionality-with-multiple-languages-in-vue-files<Paste>
Plug 'tpope/vim-surround'
Plug 'tpope/vim-endwise'  "自動でend入力
Plug 'vim-scripts/yanktmp.vim'  "別プロセスで開いてるファイルにヤンク・ペースト
Plug 'AndrewRadev/splitjoin.vim'  "gJ で行結合 or gS で行分割
Plug 'rhysd/conflict-marker.vim'  "conflict解消ヘルパー
Plug 'tmhedberg/matchit'

" support language specification
Plug 'fatih/vim-go', { 'do': ':GoUpdateBinaries' }
Plug 'jodosha/vim-godebug'
Plug 'sebdah/vim-delve'  "delve debugger support
Plug 'buoto/gotests-vim'
Plug 'othree/javascript-libraries-syntax.vim'  "https://vimawesome.com/plugin/javascript-libraries-syntax

" completion
Plug 'mattn/emmet-vim'  "zencodingの記法でHTMLやCSSの構造を書き, 「C-Y ,」でそれを展開 http://motw.mods.jp/Vim/emmet-vim.html
Plug 'Shougo/neosnippet.vim'
Plug 'Shougo/neosnippet-snippets'
Plug 'Shougo/neomru.vim'
Plug 'github/copilot.vim'

" completion: coc.nvim with LSP
"" - 1st, :Cocinstall coc-gocode  " for golang. See: https://www.npmjs.com/package/coc-gocode
"" - 2nd, and edit coc config using :CocConfig command. See: https://github.com/neoclide/coc.nvim/wiki/Language-servers#go
"" - 3rd, and install gopls using go get -u golang.org/x/tools/cmd/gopls
"
" 各LanguageServerは個別にインストールする必要あり
" https://github.com/rcjsuen/dockerfile-language-server-nodejs
" https://github.com/mads-hartmann/bash-language-server
Plug 'neoclide/coc.nvim', {'branch': 'release'}

call plug#end()
