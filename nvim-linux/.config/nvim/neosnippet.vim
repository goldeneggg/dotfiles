imap <C-k> <Plug>(neosnippet_expand_or_jump)
smap <C-k> <Plug>(neosnippet_expand_or_jump)
xmap <C-k> <Plug>(neosnippet_expand_target)

imap <expr><TAB> neosnippet#expandable_or_jumpable() ? "\<Plug>(neosnippet_expand_or_jump)" : pumvisible() ? "\<C-n>" : "\<TAB>"
smap <expr><TAB> neosnippet#expandable_or_jumpable() ? "\<Plug>(neosnippet_expand_or_jump)" : "\<TAB>"

let g:neosnippet#snippets_directory = '~/mysnippets'

let g:neosnippet#enable_snipmate_compatibility = 1

let g:neosnippet#scope_aliases = {}
let g:neosnippet#scope_aliases['ruby'] = 'ruby,rails,rspec' "TODO railsっぽいファイル開いた時のみ とか、rspecとか、諸々対応したい
let g:neosnippet#scope_aliases['eruby'] = 'eruby,html'

" if has('conceal')
"     set conceallevel=2 concealcursor=i
" endif

" Disable the default snippets (needed since we do not install Shougo/neosnippet-snippets).
" Below you can disable default snippets for specific languages. If you set " the
" language to _ it sets the default for all languages.
"let g:neosnippet#disable_runtime_snippets = {
"   \ 'go': 1
"   \}
"})

"with unite
"imap <C-s> <Plug>(neosnippet_start_unite_snippet)
