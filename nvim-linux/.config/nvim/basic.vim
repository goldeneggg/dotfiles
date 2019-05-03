" indent settings
set autoindent
set expandtab
set tabstop=2
set softtabstop=2
set shiftwidth=2

" file list completion
set wildmode=list,full
set wildignore+=*.o,*.out,*.obj,.git,*.rbc,*.rbo,*.class,.svn,*.gem
set wildignore+=*.gif,*.jpg,*.png,*.pdf,*.log
set wildignore+=*.zip,*.tar.gz,*.tar.bz2,*.rar,*.tar.xz
set wildignore+=tmp/*,log/*,*/tmp/*,*/log/*
set wildignore+=node_modules/*
set wildignore+=*.sw*,*~,._*
set wildignore+=.DS_Store

" search settings
set incsearch
set hlsearch
set wrapscan  "検索がファイル末尾に到達したら先頭から再検索

set ignorecase
set smartcase
set showcmd
set hidden
set wildmenu
"set number
set backspace=indent,eol,start  "backspaceキーを有効化
set nofoldenable  "折り畳みはいらない人なんです
set fileformats=unix,dos,mac

" status line
set laststatus=2
"set statusline=%<%f\ %m%r%h%w%{'['.(&fenc!=''?&fenc:&enc).']['.&ff.']'}%=%l/%L,%c%V%8P

" listchar
set nolist
set listchars=tab:>-,trail:-,nbsp:%
highlight SpecialKey ctermfg=darkgray

" cursor set for zenkaku char
if exists('&ambiwidth')
  set ambiwidth=double
endif

" pyenv
" pyenv-virtualenv でpython2用（neovim2）, python3（neovim3） 両方のvirtualenvが構築済であること
if exists($ANYENV_ROOT)
  let g:python_host_prog=$ANYENV_ROOT.'/envs/pyenv/versions/neovim2/bin/python'
  let g:python3_host_prog=$ANYENV_ROOT.'envs/pyenv/versions/neovim3/bin/python'
else
  let g:python_host_prog=$PYENV_ROOT.'/versions/neovim2/bin/python'
  let g:python3_host_prog=$PYENV_ROOT.'/versions/neovim3/bin/python'
endif
