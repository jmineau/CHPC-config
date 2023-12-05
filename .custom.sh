#!/bin/bash

# Here add custom module loads for all CHPC Linux systems

module use $HOME/software/modules
module load miniconda3/mineau

#module load ffmpeg
module load git
module load R
module load RStudio

# Set R user library directory
R_MAJOR_VERSION=$( echo "$R_VERSION" | cut -d. -f1-2 )
R_LIBS_USER=$HOME/software/R/$R_MAJOR_VERSION
mkdir -p "$R_LIBS_USER"
export R_LIBS_USER="$R_LIBS_USER"


# ----------------------------------------------------------------------
if [[ "$UUFSCELL" = "kingspeak.peaks" ]] ; then
# add custom module loads after this
     :

# ----------------------------------------------------------------------
# Do Notchpeak specific initializations
elif [[ "$UUFSCELL" = "notchpeak.peaks" ]] ; then
# add custom module loads after this
     :

# ----------------------------------------------------------------------
# Do Lonepeak specific initializations
elif [[ "$UUFSCELL" = "lonepeak.peaks" ]] ; then
# add custom module loads after this
     :

# ----------------------------------------------------------------------
# Do Ash specific initializations
elif [[ "$UUFSCELL" = "ash.peaks" ]] ; then
# add custom module loads after this
     :

# ----------------------------------------------------------------------
# Do Tangent specific initializations
elif [[ "$UUFSCELL" = "tangent.peaks" ]] ; then
# add custom module loads after this
     :

# ----------------------------------------------------------------------
elif [[ "$UUFSCELL" = "redwood.bridges" ]] ; then
# add custom module loads after this
     :

# ----------------------------------------------------------------------
# Do astro.utah.edu specific initializations
elif [[ "$UUFSCELL" = "astro.utah.edu" ]] ; then
# add custom module loads after this
	:

# ----------------------------------------------------------------------
# Do cemi specific initializations
elif [[ "$UUFSCELL" = "cemi" ]] ; then
# add custom module loads after this
	:

fi

# Uncomment to set TMPDIR from default (and small) /tmp to /scratch/local
if [ ! -d /scratch/local/$USER ] ; then
     mkdir /scratch/local/$USER 
fi
export TMPDIR=/scratch/local/$USER 

# Only execute if the shell is interactive
if [[ $- == *i* ]]; then
    # Welcome Message
    python3 $HOME/.days_alive.py

fi

# Add custom python packages to path
export PYTHONPATH=$PYTHONPATH:$HOME/software/python/pkgs

# Add env variables
export $(grep -v '^#' $HOME/.env | xargs -d '\n')

# Add API Keys to env
export $(cat $HOME/.api_keys.env)
