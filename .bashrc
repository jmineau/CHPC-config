# please send comments/suggestions to issues@chpc.utah.edu
# currently works on all CHPC based clusters and on Linux desktops

# Source global definitions
if [ -f /etc/bashrc ]; then
        . /etc/bashrc
fi

#MC if UUFSCELL is not defined, try to source it
if [ -z "$UUFSCELL" ] ; then       # Test whether the the $UUFSCELL has zero length
  if [ -e /etc/profile.d/uufs.sh ] ; then
     . /etc/profile.d/uufs.sh
  fi
fi

# Init. modules before setting UUFSCELL
# Unset MODULEPATH + set LUA + LMOD
source /uufs/chpc.utah.edu/sys/modulefiles/scripts/module_init/module_init.sh  > /dev/null 2>&1

# stacksize by default :very small => programs with large static data to segfault
ulimit -s unlimited

# create .pbs_spool if not created already
if [ ! -d $HOME/.pbs_spool ] ; then
     mkdir $HOME/.pbs_spool
fi

# NEVER!!! ADD env. variables into .aliases -> interferes with modules
if [ -f "$HOME/.aliases" ] ; then
    source ~/.aliases
fi

if [ -n "$UUFSCELL" ] ; then       # If the String length is NON-zero
    GRP=`echo $UUFSCELL | cut -d . -f 2`
    
    if [[ $BASHRC_LOADED == 1 ]] ; then
      if [ ! -n "$TERM" ] ; then return; fi
      if [[ $TERM != "screen" ]] ; then return; fi
    fi
    export BASHRC_LOADED=0

    # Template custom.sh to be found at :
    #   /uufs/chpc.utah.edu/sys/modulefiles/templates/custom.sh
    if [ -f "$HOME/.custom.sh" ] ; then
        source $HOME/.custom.sh
    fi
fi # End of the UUFSCELL loop

# scp defines TERM='dumb', so, this condition is not valid
#if [ ! -n "$TERM" ] ; then
# need to use PS1 instead
if [ -z "$PS1" ] ; then
    return
fi

if [[ "$UUFSCELL" = "redwood.bridges" ]] ; then
# set up custom prompt with PE string
  PS1="[\u@\h *PE* \W]\$"
else
#  set prompt = "[$USER@%m:%b%c2]%b "
  PS1="[\u@\h:\W]\$ "
fi

# list completions when the tab key is hit
# menu-complete cycles through options, complete stops at first ambiguous character
#bind "TAB:menu-complete"
bind "TAB:complete"
bind "set show-all-if-ambiguous on"
# expand variable names in tab auto-completion
shopt -s direxpand
export TMOUT=0

# USER COMMANDS

#    Set command prompt
PS1='\[\e[00m\][\[\e[1;34m\]Mineau@\h\[\e[00m\]:\[\e[1;36m\]\W\[\e[00m\]]\[\e[1;31m\]> \[\e[00m\]'

mamba activate Main  # Activate the Main environment