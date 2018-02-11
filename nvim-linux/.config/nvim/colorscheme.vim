" If you have vim >=8.0 or Neovim >= 0.1.5
if (has("termguicolors"))
 set termguicolors
endif

" modify highlight
" ファイル内検索
autocmd ColorScheme * highlight Search ctermfg=234 ctermbg=221 guifg=#1d1f21 guibg=#f0c674

" theme
syntax enable
colorscheme tender
