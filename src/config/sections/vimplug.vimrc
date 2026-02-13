
call plug#begin('~/.vim/plugged')

Plug 'tpope/vim-sensible'
Plug 'vim-airline/vim-airline'

" Fuzzy Finder
Plug 'junegunn/fzf', { 'do': './install --all' }
Plug 'junegunn/fzf.vim'

" Color Scheme
Plug 'morhetz/gruvbox'

call plug#end()

" Auto install plugins if missing
if empty(glob('~/.vim/plugged'))
  autocmd VimEnter * PlugInstall --sync | source $MYVIMRC
endif

" Auto set colorscheme
set background=dark
colorscheme gruvbox
