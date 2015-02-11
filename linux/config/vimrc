" An example for a vimrc file.
"
" Maintainer:	Bram Moolenaar <Bram@vim.org>
" Last change:	2008 Jul 02
"
" To use it, copy it to
"     for Unix and OS/2:  ~/.vimrc
"	      for Amiga:  s:.vimrc
"  for MS-DOS and Win32:  $VIM\_vimrc
"	    for OpenVMS:  sys$login:.vimrc

" When started as "evim", evim.vim will already have done these settings.
if v:progname =~? "evim"
  finish
endif

" Use Vim settings, rather then Vi settings (much better!).
" This must be first, because it changes other options as a side effect.
set nocompatible

" allow backspacing over everything in insert mode
set backspace=indent,eol,start

if has("vms")
  set nobackup		" do not keep a backup file, use versions instead
else
  set backup		" keep a backup file
endif
set history=50		" keep 50 lines of command line history
set ruler		" show the cursor position all the time
set showcmd		" display incomplete commands
set incsearch		" do incremental searching

" For Win32 GUI: remove 't' flag from 'guioptions': no tearoff menu entries
" let &guioptions = substitute(&guioptions, "t", "", "g")

" Don't use Ex mode, use Q for formatting
map Q gq

" CTRL-U in insert mode deletes a lot.  Use CTRL-G u to first break undo,
" so that you can undo CTRL-U after inserting a line break.
inoremap <C-U> <C-G>u<C-U>

" In many terminal emulators the mouse works just fine, thus enable it.
"if has('mouse')
"  set mouse=a
"endif

" Switch syntax highlighting on, when the terminal has colors
" Also switch on highlighting the last used search pattern.
if &t_Co > 2 || has("gui_running")
  syntax on
  set hlsearch
endif

" Only do this part when compiled with support for autocommands.
if has("autocmd")

  " Enable file type detection.
  " Use the default filetype settings, so that mail gets 'tw' set to 72,
  " 'cindent' is on in C files, etc.
  " Also load indent files, to automatically do language-dependent indenting.
  filetype plugin indent on

  " Put these in an autocmd group, so that we can delete them easily.
  augroup vimrcEx
  au!

  " For all text files set 'textwidth' to 78 characters.
  autocmd FileType text setlocal textwidth=78
  autocmd FileType gitcommit let g:secure_modelines_allowed_items = [] |
			  \ setlocal textwidth=72

  " When editing a file, always jump to the last known cursor position.
  " Don't do it when the position is invalid or when inside an event handler
  " (happens when dropping a file on gvim).
  " Also don't do it when the mark is in the first line, that is the default
  " position when opening a file.
  autocmd BufReadPost *
    \ if line("'\"") > 1 && line("'\"") <= line("$") |
    \   exe "normal! g`\"" |
    \ endif

  augroup END

else

  set autoindent		" always set autoindenting on

endif " has("autocmd")

" Convenient command to see the difference between the current buffer and the
" file it was loaded from, thus the changes you made.
" Only define it when not defined already.
if !exists(":DiffOrig")
  command DiffOrig vert new | set bt=nofile | r # | 0d_ | diffthis
		  \ | wincmd p | diffthis
endif

" ------------------ZZH configuration ;-)---------------------
set nobackup

"Set mapleader
let mapleader = ","

" Platform
function! MySys()
  if has("win32")
      return "windows"
  else
    return "linux"
  endif
endfunction


function! SwitchToBuf(filename)
    "let fullfn = substitute(a:filename, "^\\~/", $HOME . "/", "")
    " find in current tab
    let bufwinnr = bufwinnr(a:filename)
    if bufwinnr != -1
        exec bufwinnr . "wincmd w"
        return
    else
	" find in each tab
	tabfirst
	let tab = 1
	while tab <= tabpagenr("$")
	    let bufwinnr = bufwinnr(a:filename)
	    if bufwinnr != -1
		exec "normal" . tab . "gt"
		exec bufwinnr . "wincmd w"
		return
	    endif
	    tabnext
	    let tab = tab + 1
	endwhile
	" not exist, new tab
	exec "tabnew" . a:filename
    endif
endfunction

"Fast edit vimrc
if MySys() == 'linux'
	"Fast reloading of the .vimrc
	map <silent> <leader>ss :source ~/.vimrc<cr>
	"Fast editing of .vimrc
	map <silent> <leader>ee :e ~/.vimrc<cr>
	"When .vimrc is edited, reload it
	"autocmd! bufwritepost .vimrc source ~/.vimrc 
elseif MySys() == 'windows'
	set helplang=cn
	"Fast reloading of the .vimrc
	map <silent> <leader>ss :source ~/_vimrc<cr>
	"Fast editing of .vimrc
	map <silent> <leader>ee :e ~/_vimrc<cr>
	"When .vimrc is edited, reload it
	"autocmd! bufwritepost _vimrc source ~/_vimrc 
map <silent> <leader>
endif

" For windows version
if MySys() == 'windows'
	source $VIMRUNTIME/mswin.vim
	behave mswin
endif

if filereadable("ofono.vim")
	"source ofono.vim
endif

if filereadable("ofono.viminfo")
	"source ofono.viminfo
endif

"--------For winManager
"let g:winManagerWindowLayout = 'BufExplorer, FileExplorer|TagList'
let g:winManagerWidth = 30
let g:defaultExplorer = 0
"nmap <C-W><C-F> :FirstExplorerWindow<cr>
"nmap <C-W><C-B> :BottomExplorerWindow<cr>
"nmap <silent> <F2>wm :WMToggle<cr>
"-------Tlist
nmap <silent> <F3> :TlistToggle<cr>
"-------Lookup<by default>
"nmap <silent> <F5> :LookupFile<cr>
"-------evening
colorscheme evening 
"#set number

set path+=/home/zzhan17/ofono/**

"-----taglist
if MySys() == "windows"
	let Tlist_Ctags_Cmd = 'ctags'
elseif MySys() == "linux"
	let Tlist_Ctags_Cmd = '/usr/bin/ctags'
endif
let Tlist_Show_One_File = 1
let Tlist_Exit_OnlyWindow = 0
let Tlist_Use_Right_Window = 1
let Tlist_Show_Menu = 0

let Tlist_Auto_Open = 0
let Tlist_GainFocus_On_ToggleOpen = 0

"-----LookupFile
let g:LookupFile_MinPatLength = 2               "最少输入2个字符才开始查找
let g:LookupFile_PreserveLastPattern = 1        "不保存上次查找的字符串
let g:LookupFile_PreservePatternHistory = 1     "保存查找历史
let g:LookupFile_AlwaysAcceptFirst = 1          "回车打开第一个匹配项目
let g:LookupFile_AllowNewFiles = 0              "不允许创建不存在的文件

if filereadable("./tags")                "设置tag文件的名字
	let g:LookupFile_TagExpr = '"./tags"'
endif
"映射LookupFile为,lk
nmap <silent> <leader>lk <Plug>LookupFile<cr>
"映射LUBufs为,ll
nmap <silent> <leader>ll :LUBufs<cr>
"映射LUWalk为,lw 
nmap <silent> <leader>lw :LUWalk<cr> 


"-----Omin-complete
" mapping
" 如果下拉菜单弹出，回车映射为接受当前所选项目，否则，仍映射为回车
"inoremap <expr> <CR>       pumvisible()?"\<C-Y>":"\<CR>"
" 如果下拉菜单弹出，CTRL-J映射为在下拉菜单中向下翻页。否则映射为CTRL-X CTRL-O；
"inoremap <expr> <C-J>      pumvisible()?"\<PageDown>\<C-N>\<C-P>":"\<C-X><C-O>"
"  如果下拉菜单弹出，CTRL-K映射为在下拉菜单中向上翻页，否则仍映射为CTRL-K；
"inoremap <expr> <C-K>      pumvisible()?"\<PageUp>\<C-P>\<C-N>":"\<C-K>"
"  如果下拉菜单弹出，CTRL-U映射为CTRL-E，即停止补全，否则，仍映射为CTRL-U；
"inoremap <expr> <C-U>      pumvisible()?"\<C-E>":"\<C-U>" 

" Enable ShowMarks
let showmarks_enable = 1
" " Show which marks
" let showmarks_include = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
" " Ignore help, quickfix, non-modifiable buffers
let showmarks_ignore_type = "hqm"
" " Hilight lower & upper marks
"
"
let showmarks_hlline_lower = 1
let showmarks_hlline_upper = 1 

" For miniBufExplorer
let g:miniBufExplMapWindowNavVim = 1 
let g:miniBufExplMapWindowNavArrows = 1 
let g:miniBufExplMapCTabSwitchBufs = 1 
let g:miniBufExplModSelTarget = 1 

" whether replace tab with space
"set ts=4 expandtab
