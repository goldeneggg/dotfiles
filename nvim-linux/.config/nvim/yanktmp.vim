"==================== yanktmp
" See: http://secondlife.hatenablog.jp/entry/20060705/1152110844
map <silent> sy :call YanktmpYank()<CR>
map <silent> sp :call YanktmpPaste_p()<CR>
map <silent> sP :call YanktmpPaste_P()<CR>
let g:yanktmp_file = $HOME . '/vimyanktmp'
