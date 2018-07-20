#!/bin/sh
#SBATCH --ntasks=320
#SBATCH --nodes=10
#SBATCH --ntasks-per-node=32
#SBATCH --account=snap
#SBATCH --mail-type=all
#SBATCH --mail-user=malindgren@alaska.edu
#SBATCH -p main

source ~/v2/bin/activate
ipython /workspace/UA/malindgren/repos/alfresco-calibration/alfresco_postprocessing/bin/run_relflam_slurm_SERDP_EPA.py
