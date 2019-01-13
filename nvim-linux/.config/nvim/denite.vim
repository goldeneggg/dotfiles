"==================== Denite
" https://qiita.com/okamos/items/4e1665ecd416ef77df7c
"
" insertモードのデフォルトマッピング
" - <Down> : 次の行へ移動  *デフォルトはC-G
" - <Up> : 前の行へ移動  *デフォルトはC-T
" - <C-O> : ノーマルモードへ切り替え
"
" normalモードのデフォルトマッピング
" - i : insertモードへ切り替え

"========== customizek keys for insert mode
" 候補表示のinsertモード時の前後候補選択はカーソルキーに変更する
call denite#custom#map(
      \ 'insert',
      \ '<Down>',
      \ '<denite:move_to_next_line>',
      \ 'noremap'
      \)
call denite#custom#map(
      \ 'insert',
      \ '<Up>',
      \ '<denite:move_to_previous_line>',
      \ 'noremap'
      \)

"========== Denite prefix key
nnoremap [denite] <Nop>
nmap     ,u [denite]

"========== keymap
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
" grep (and filerec) command
if executable('ack')
  " Use ack
  call denite#custom#var('grep', 'command', ['ack'])
  call denite#custom#var('grep', 'default_opts',
                  \ ['--ackrc', $HOME.'/.ackrc', '-H', '-i',
                  \ '--nopager', '--nocolor', '--nogroup', '--column'])
  "call denite#custom#var('file_rec', 'command', ['ack'])
elseif executable('ack-grep')
  " Use ack-grep (ack on linux)
  call denite#custom#var('grep', 'command', ['ack-grep'])
  call denite#custom#var('grep', 'default_opts',
                  \ ['--ackrc', $HOME.'/.ackrc', '-H', '-i',
                  \ '--nopager', '--nocolor', '--nogroup', '--column'])
  "call denite#custom#var('file_rec', 'command', ['ack-grep'])
endif

call denite#custom#var('grep', 'recursive_opts', [])

nnoremap <silent> ,/ :Denite grep:. -buffer-name=search-buffer<CR>
" カーソル上の単語で検索
nnoremap <silent> ,g :DeniteCursorWord grep:. -buffer-name=search-buffer<CR>
" " 検索結果を再度呼び出し
" nnoremap <silent> ,r  :<C-u>UniteResume search-buffer<CR>
