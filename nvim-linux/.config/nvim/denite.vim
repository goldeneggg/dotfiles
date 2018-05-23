"==================== Denite
" https://qiita.com/okamos/items/4e1665ecd416ef77df7c

"========== Denite prefix key
nnoremap [denite] <Nop>
nmap     ,u [denite]

"========== settings
" " 結果表示をinsertモードで開始
" let g:unite_enable_start_insert=1
" " 大文字小文字を区別しない
" let g:unite_enable_ignore_case = 1
" let g:unite_enable_smart_case = 1
" " 最近開いたファイル一覧の最大数
" let g:unite_source_file_mru_limit = 200
" " dotfileも表示対象にする TODO
" "call unite#custom#source('file', 'matchers', 'matcher_default')
" "call unite#custom#source('grep', 'matchers', 'matcher_default')
" " 無視パターンをスクリプト変数で定義
" let s:unite_ignore_patterns=
"   \ ''
"   \ .'vendor/bundle\|\.bundle/\|log/\|public/\|tmp/\|'
"   \ .'.vim/\|'
"   \ .'node_modules/\|'
"   \ .'\.\(gif\|jpe\?g\|png\|bmp\|pdf\|webp\)$'

"========== keymap
" カレントディレクトリ下一覧
" nnoremap <silent> [unite]c :<C-u>UniteWithCurrentDir -buffer-name=curdir-buffer buffer bookmark file<CR>

" バッファ + 最近開いたファイル
nnoremap <silent> [denite]u :<C-u>Denite buffer file_mru<CR>
" バッファ一覧
nnoremap <silent> [denite]b :<C-u>Denite buffer<CR>
" 最近開いたファイル
nnoremap <silent> [denite]m :<C-u>Denite file_mru<CR>
" プロジェクトディレクトリ下一覧
nnoremap <silent> [denite]c :<C-u>DeniteProjectDir -buffer-name=pjtdir-buffer buffer file<CR>
" 現在開いているファイルのディレクトリ下一覧
nnoremap <silent> [denite]a :<C-u>DeniteBufferDir -buffer-name=bufdir-buffer buffer file<CR>

"========== line
" nnoremap <silent> ,l :<C-u>Unite line:all -no-quit -buffer-name=line-buffer<CR>
nnoremap <silent> ,l :Denite line:all:noempty -no-quit -buffer-name=line-buffer<CR>

"========== like CtrlP
" gitプロジェクトのdirの場合は file_rec/git を定義/利用する
function! DeniteFileRecAsyncOrGit()
  if isdirectory(getcwd()."/.git")
    call denite#custom#alias('source', 'file_rec/git', 'file_rec')
    call denite#custom#var('file_rec/git', 'command', ['git', 'ls-files', '-co', '--exclude-standard'])
    Denite file_rec/git
  else
    Denite file_rec
  endif
endfunction
nnoremap ,p :<C-u>call DeniteFileRecAsyncOrGit()<CR>

"========== grep
" let g:unite_source_grep_max_candidates = 200
" let g:unite_source_grep_recursive_opt = ''

" grep (and filerec) command
if executable('hw')
  " Use hw (highway)
  " https://github.com/tkengo/highway
  call denite#custom#var('grep', 'command', ['hw'])
  call denite#custom#var('grep', 'default_opts', ['--no-group', '--no-color'])
  call denite#custom#var('file_rec', 'command', ['hw', '--no-group', '--no-color'])
elseif executable('ack')
  " Use ack
  call denite#custom#var('grep', 'command', ['ack'])
  call denite#custom#var('file_rec', 'command', ['ack'])
elseif executable('ack-grep')
  " Use ack-grep (ack on linux)
  call denite#custom#var('grep', 'command', ['ack-grep'])
  call denite#custom#var('file_rec', 'command', ['ack-grep'])
endif

call denite#custom#var('grep', 'recursive_opts', [])

nnoremap <silent> ,/ :Denite grep:. -buffer-name=search-buffer<CR>
" カーソル上の単語で検索
nnoremap <silent> ,g :DeniteCursorWord grep:. -buffer-name=search-buffer<CR>
" " 検索結果を再度呼び出し
" nnoremap <silent> ,r  :<C-u>UniteResume search-buffer<CR>
