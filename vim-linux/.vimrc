" for vim 8.1 later
" See: https://github.com/Shougo/dein.vim/issues/9
if v:version > 800
  set nocompatible
endif

" basic settings
source $HOME/.vimrc.settings
source $HOME/.vimrc.keymaps
source $HOME/.vimrc.lets
source $HOME/.vimrc.encoding
source $HOME/.vimrc.macros
source $HOME/.vimrc.ctags

if v:version > 701
  " configure plugins(using neobundle) and runtimes
  " See: http://mattn.kaoriya.net/software/vim/20120618123848.htm

  filetype off
  filetype plugin indent off
  source $HOME/.vimrc.neobundle
  source $HOME/.vimrc.goruntime
  filetype plugin indent on
  source $HOME/.vimrc.neobundlecheck

  " later assumed to be set plugins
  source $HOME/.vimrc.colorscheme

  source $HOME/.vimrc.unite
  "source $HOME/.vimrc.vimfiler
  "source $HOME/.vimrc.neocomplcache
  source $HOME/.vimrc.deoplete
  source $HOME/.vimrc.neosnippet

  source $HOME/.vimrc.ctrlp

  source $HOME/.vimrc.quickrun
  source $HOME/.vimrc.syntastic
  "source $HOME/.vimrc.easymotion
  source $HOME/.vimrc.switchvim
  source $HOME/.vimrc.yanktmp
  source $HOME/.vimrc.indentguides
  source $HOME/.vimrc.lightline
  source $HOME/.vimrc.dash
endif

if has("autocmd")
  " See: http://blog.livedoor.jp/sasata299/archives/51179057.html

  source $HOME/.vimrc.autocmd-basic
  "source $HOME/.vimrc.autocmd-php
  "source $HOME/.vimrc.autocmd-java
  source $HOME/.vimrc.autocmd-golang
  source $HOME/.vimrc.autocmd-ruby
  source $HOME/.vimrc.autocmd-markdown
  source $HOME/.vimrc.autocmd-tmux
endif
