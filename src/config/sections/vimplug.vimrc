
call plug#begin('~/.vim/plugged')

Plug 'tpope/vim-sensible'
Plug 'vim-airline/vim-airline'

" Fuzzy Finder
Plug 'junegunn/fzf', { 'do': './install --all' }
Plug 'junegunn/fzf.vim'

" Color Scheme
Plug 'morhetz/gruvbox'

call plug#end()

" Auto set colorscheme
set background=dark
colorscheme gruvbox
