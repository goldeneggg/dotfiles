"let g:ctrlp_clear_cache_on_exit = 1  "vim終了時にキャッシュをクリア
let g:ctrlp_show_hidden = 1  "dotfileも対象に含める

"set wildignore+=*/tmp/*,*/log/*,*.so,*.swp,*.zip
"set wildignore+=*/.git/*,*/.hg/*,*/.svn/*,*/.vim/*
"set wildignore+=*/node_modules/*

if isdirectory(getcwd()."/.git")
  let g:ctrlp_user_command = ['.git/', 'git --git-dir=%s/.git ls-files -oc --exclude-standard']
endif
