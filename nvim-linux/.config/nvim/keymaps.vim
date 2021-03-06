" key map
"See: http://vim-jp.org/vimdoc-ja/map.html
"See: http://deris.hatenablog.jp/entry/2013/05/02/192415

" - カレントバッファだけで使用できるマップを作成するには、マップコマンドの引数に"<buffer>" を指定
" - 実行するコマンドがコマンドラインに表示されないようにするには、マップコマンドの引数に "<silent>" を指定
" - マップや短縮入力を定義するときに "<unique>" 引数を指定すると、同じ名前のものがすでに定義されていた場合に、コマンドは失敗
" - マップや短縮入力を定義するときに "<expr>" 引数を指定すると、引数が式 (スクリプト) として扱われ、マップが実行されたときに式が評価され、その値が {rhs}として使われる

"my Leader key is <Space>
let mapleader = "\<Space>"

"nnoremap <Space>e :edit .<CR>
nnoremap <ESC><ESC> :nohlsearch<CR><ESC>
nnoremap <C-j>n :bn<CR>
nnoremap <C-j>p :bp<CR>

" for US keyboard
nnoremap ; :
nnoremap : ;

" paste from clipboard(register * is clipboard)
nnoremap <Leader>pp "*p

" jj でノーマルモードに戻る
inoremap <silent> jj <ESC>
