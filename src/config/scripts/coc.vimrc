" =============================
" Coc.nvim settings
" =============================

" =============================
" Autocomplete navigation
" =============================
" Arrow keys to navigate popup menu
inoremap <expr> <Up>   pumvisible() ? "\<C-p>" : "\<Up>"
inoremap <expr> <Down> pumvisible() ? "\<C-n>" : "\<Down>"

" Tab to accept suggestion
inoremap <expr> <Tab> pumvisible() ? coc#_select_confirm() : "\<Tab>"
inoremap <expr> <S-Tab> pumvisible() ? "\<C-p>" : "\<S-Tab>"

" Optional: trigger completion manually
inoremap <silent><expr> <C-Space> coc#refresh()
