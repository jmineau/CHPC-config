#!/bin/bash

# ssh ------------------------------------------------------------------

# Start SSH Agent
#if [ -z "$SSH_AUTH_SOCK" ] ; then
#    eval $(ssh-agent -s)
#    ssh-add
#fi


# env ------------------------------------------------------------------

# Add env variables
# export $(grep -v '^#' $HOME/.env | xargs -d '\n')
set -a  # automatically export all variables
source $HOME/.env
set +a  # stop automatically exporting all variables

# Uncomment to set TMPDIR from default (and small) /tmp to /scratch/local
if [ ! -d /scratch/local/$USER ] ; then
     mkdir /scratch/local/$USER 
fi
export TMPDIR=/scratch/local/$USER

# Add API Keys to env
export $(cat $HOME/.api_keys.env)


# modules -------------------------------------------------------------

# module use $HOME/software/modules
# module load miniforge3/mineau

#module load ffmpeg
module load git  > /dev/null 2>&1
module load R > /dev/null 2>&1
# module load RStudio


# Python ---------------------------------------------------------------

activate-mamba  # Activate mamba using /path-to-miniforge3/etc/profile.d/mamba.sh

# Only execute if the shell is interactive
if [[ $- == *i* ]]; then
    # Welcome Message
    python3 $HOME/.days_alive.py

fi

# Add custom python packages to path
#export PYTHONPATH=$PYTHONPATH:$HOME/software/python/pkgs


# R --------------------------------------------------------------------

# Set R user library directory
# R_MAJOR_VERSION=$( echo "$R_VERSION" | cut -d. -f1-2 )
# R_LIBS_USER=$HOME/software/R/$R_MAJOR_VERSION
# mkdir -p "$R_LIBS_USER"
# export R_LIBS_USER="$R_LIBS_USER"
