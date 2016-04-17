" window
set lines=50
set columns=170

" font
set guifont=Osaka-Mono:h16
set linespace=0

" color
colorscheme hybrid

" tab
function GuiTabLabel()
  return fnamemodify(getcwd(), ':t')
endfunction

set guitablabel=%{GuiTabLabel()}
set showtabline=2

" keymap
" TODO 効かない
let g:mapleader = <Space>
