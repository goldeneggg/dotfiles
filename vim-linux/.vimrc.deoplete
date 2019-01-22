"==========
" See: https://github.com/Shougo/deoplete.nvim/blob/master/doc/deoplete.txt
"==========

set completeopt+=noselect

let g:deoplete#enable_at_startup = 1

" 補完完了したらプレビューウインドウを閉じる
autocmd CompleteDone * silent! pclose!

" deoplete-go
let g:deoplete#sources#go#gocode_binary = $GOPATH . '/bin/gocode'
let g:deoplete#sources#go#sort_class = ['package', 'func', 'type', 'var', 'const']

