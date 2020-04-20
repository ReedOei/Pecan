" Vim syntax file
" Language:      Pecan
" Maintainers:   Reed Oei <me@reedoei.com>
" Version: 0.1

" Quit if syntax file is already loaded
if version < 600
  syntax clear
elseif exists("b:current_syntax")
  finish
endif

let b:current_syntax = "pecan"

syntax keyword keywords is are forall exists not or and if then match end case else only with let in be do iff
syntax match keyword_op '∀\|∃'
syntax keyword bool true false sometimes
syntax keyword directive that save_aut save_aut_img save_pred context end_context load assert_prop import forget accepting_word shuffle defining
syntax match directiveOp '#'

" syntax keyword praline_directive Alias Example Display Execute Define
syntax match praline_directive '^\s*[A-Z][a-zA-Z_0-9]*\>'

syntax match operator '+\|-\|=\|:=\|=>\|*\|/\|!\|\.\|>\|<\||\|&\|∧\|:\|∈\|≠\|¬\|⟺\|≤\|≥\|⇒\|⟹\|⇔\|∨\|\^\|\\\|∘'

syntax match comment "//.*$"
syntax match todo "TODO"

syntax match annotation "@[A-Za-z0-9_]\+"

syntax match num '\<#\?[-+]\?\d\+\.\?\d*'

syntax region string start='"' end='"' skip='\\"'
syntax region string start='\'' end='\'' skip='\\\''

hi def link praline_directive PreProc

hi def link keywords Function
hi def link keyword_op Function
hi def link operator Operator
hi def link directive PreProc
hi def link directiveOp PreProc
hi def link num Number
hi def link bool Number
hi def link todo Todo
hi def link annotation Todo

