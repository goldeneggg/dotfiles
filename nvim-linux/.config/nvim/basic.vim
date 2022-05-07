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
set inccommand=nosplit  "incremental置換でウインドウ分割しない

" backup setting
set nobackup
set nowritebackup
set noswapfile

set ignorecase
set smartcase
set showcmd
set hidden
set wildmenu
set number
set backspace=indent,eol,start  "backspaceキーを有効化
set nofoldenable  "折り畳みはいらない人なんです
set fileformats=unix,dos,mac
set lazyredraw
set signcolumn=yes

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

" python (asdf or system global)
if !empty($ASDF_ROOT)
  let g:python3_host_prog=$ASDF_ROOT.'/shims/python'
else
  let g:python3_host_prog='/usr/bin/python'
endif
