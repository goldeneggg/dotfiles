"==========
" See: https://github.com/ctrlpvim/ctrlp.vim/blob/master/doc/ctrlp.txt
" See: https://github.com/tacahiroy/ctrlp-funky/blob/master/doc/ctrlp-funky.txt
"==========

"===== ctrlp
"let g:ctrlp_clear_cache_on_exit = 1  "vim終了時にキャッシュをクリア
let g:ctrlp_show_hidden = 1  "dotfileも対象に含める

nnoremap [ctrlpcmd] <nop>
nmap     ,c [ctrlpcmd]

nnoremap <silent> [ctrlpcmd]b :<C-u>CtrlPBuffer<CR>
nnoremap <silent> [ctrlpcmd]m :<C-u>CtrlPMRU<CR>

if isdirectory(getcwd()."/.git")
  let g:ctrlp_user_command = ['.git/', 'git --git-dir=%s/.git ls-files -oc --exclude-standard']
endif

"===== ctrlp-funky
let g:ctrlp_funky_syntax_highlight = 1

nnoremap <silent> [ctrlpcmd]f :<C-u>CtrlPFunky<CR>
