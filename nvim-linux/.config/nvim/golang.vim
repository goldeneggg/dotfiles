" 自動import
let g:go_fmt_command = "goimports"

" 保存時にgolintを実行する
"autocmd BufWritePost,FileWritePost *.go execute 'Lint' | cwindow

" quickfixのサイズ（高さ）
let g:go_list_height = 5

" ハイライト
let g:go_highlight_fields = 1
let g:go_highlight_functions = 1
let g:go_highlight_methods = 1
let g:go_highlight_operators = 1
let g:go_highlight_structs = 1

" カーソル下と同一識別子の自動ハイライト
let g:go_auto_sameids = 0

" ステータスバーに型定義を表示
let g:go_auto_type_info = 1

" :GoAddTags時のjson項目名をsnakecase
let g:go_addtags_transform = "snakecase"

" snippet
let g:go_snippet_engine = "neosnippet"

" 補完はcoc.nvimに任せる
let g:go_code_completion_enabled = 0

" lint with lightline TODO

" maps
au FileType go nnoremap <Leader>gr <Plug>(go-rename)
au FileType go nnoremap <Leader>gd <Plug>(go-doc)
au FileType go nnoremap <Leader>gi <Plug>(go-info)
" 下記コロンコマンド群はnnoremapで定義すること（nmapだと機能しない）
au FileType go nnoremap <Leader>gat :GoAddTags<cr>
au FileType go nnoremap <Leader>gt :GoDeclsDir<cr>
au FileType go nnoremap <Leader>gec :<C-u>GoErrCheck<cr>

" ----- lsp settings
" Need to install golsp. using "go get -u golang.org/x/tools/cmd/gopls" command.

" for vim-go and gopls. See: https://github.com/golang/go/wiki/gopls
"let g:go_def_mode='gopls'

" for coc.nvim and gopls. See: https://github.com/neoclide/coc.nvim/wiki/Language-servers#go
" Run ":CocConfig" command and edit json as follows
  " "languageserver": {
  "   "golang": {
  "     "command": "gopls",
  "     "rootPatterns": ["go.mod", ".vim/", ".git/", ".hg/"],
  "     "filetypes": ["go"]
  "   }
  " }
