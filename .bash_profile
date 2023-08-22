# .bash_profile

# Get the aliases and functions
if [ -f ~/.bashrc ]; then
	. ~/.bashrc
fi

PATH=$PATH:$HOME/bin

export PATH
unset USERNAME


# User specific environment and startup programs

#	Set default text editor
export VISUAL='nano'
