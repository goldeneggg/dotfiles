set completeopt+=noselect

let g:python3_host_prog = $PYENV_ROOT . '/shims/python3'
let g:python3_host_skip_check = 1

let g:deoplete#enable_at_startup = 1

"========== deoplete-go
let g:deoplete#sources#go#gocode_binary = $GOPATH . '/bin/gocode'
let g:deoplete#sources#go#sort_class = ['package', 'func', 'type', 'var', 'const']
