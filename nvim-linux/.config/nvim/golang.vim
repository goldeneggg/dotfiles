"========== 自動import
let g:go_fmt_command = "goimports"

"========== 保存時にgolintを実行する
"autocmd BufWritePost,FileWritePost *.go execute 'Lint' | cwindow

"========== ハイライト
let g:go_highlight_build_constraints = 1
let g:go_highlight_extra_types = 1
let g:go_highlight_fields = 1
let g:go_highlight_functions = 1
let g:go_highlight_methods = 1
let g:go_highlight_operators = 1
let g:go_highlight_structs = 1
let g:go_highlight_types = 1

let g:go_auto_sameids = 1

"========== ステータスバーに型定義を表示
let g:go_auto_type_info = 1

"========== :GoAddTags時のjson項目名をsnakecase
let g:go_addtags_transform = "snakecase"

"========== lint with lightline TODO

"========== maps
" \ga : :GoAddTags - structにjson tag追加
au FileType go nmap <leader>ga :GoAddTags<cr>
" \gt : パッケージ内の関数や型の定義元一覧, ctrlpで表示
au FileType go nmap <leader>gt :GoDeclsDir<cr>
