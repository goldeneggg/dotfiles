" 自動import
let g:go_fmt_command = "goimports"

" 保存時にgolintを実行する
"autocmd BufWritePost,FileWritePost *.go execute 'Lint' | cwindow

" ハイライト
" let g:go_highlight_build_constraints = 1
" let g:go_highlight_extra_types = 1
let g:go_highlight_fields = 1
let g:go_highlight_functions = 1
let g:go_highlight_methods = 1
" let g:go_highlight_operators = 1
" let g:go_highlight_structs = 1
" let g:go_highlight_types = 1

"let g:go_auto_sameids = 1

" ステータスバーに型定義を表示
let g:go_auto_type_info = 1

" :GoAddTags時のjson項目名をsnakecase
let g:go_addtags_transform = "snakecase"

" snippet
let g:go_snippet_engine = "neosnippet"

" lint with lightline TODO

" maps
" FIXME: 下記mapが機能しなくなっている（何らかの設定とバッティングしている？）
" \ga : :GoAddTags - structにjson tag追加
au FileType go nmap <Leader>ga :GoAddTags<cr>
" \gt : パッケージ内の関数や型の定義元一覧, ctrlpで表示
au FileType go nmap <Leader>gt :GoDeclsDir<cr>

" 補完はcoc.nvimに任せる
let g:go_code_completion_enabled = 0

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
