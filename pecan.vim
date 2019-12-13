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

let b:current_syntax = "pn"

syntax keyword keywords is are forall exists not or and sometimes
syntax match keyword_op '∀\|∃'
syntax keyword bool true false
syntax keyword directive save_aut save_aut_img save_pred context end_context load assert_prop import forget type show_word accepting_word
syntax match directiveOp '#'

syntax match operator '+\|-\|=\|:=\|=>\|*\|/\|!\|\.\|>\|<\||\|&\|∧\|:\|∈\|≠\|¬\|⟺\|≤\|≥\|⇒\|⟹\|⇔\|∨'

syntax match comment "//.*$"
syntax match todo "TODO"

syntax match num '\<#\?[-+]\?\d\+\.\?\d*'

syntax region string start='"' end='"' skip='\\"'
syntax region string start='\'' end='\'' skip='\\\''

hi def link keywords Function
hi def link keyword_op Function
hi def link operator Operator
hi def link directive PreProc
hi def link directiveOp PreProc
hi def link num Number
hi def link bool Number
hi def link todo Todo

