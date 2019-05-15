" See: https://github.com/chriskempson/base16-shell#base16-vim-users
" need to set 'Plug chriskempson/base16-vim' into .vimrc and execute :PlugInstall
"
" Favorite Colors
" - atelier-savanna
" - bespin
" - codeschool
" - eighties
" - gruvbox-xxx
" - material
" - mocha
" - ocean
" - phd
" - railscasts
" - zenburn
if filereadable(expand("~/.vimrc_background"))
  let base16colorspace=256
  source ~/.vimrc_background
endif
