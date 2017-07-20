# RUN RELATIVE FLAMMABILITY ACROSS ALL SUB-DIRS in IEM_AR5 directory
import os, glob

base_path = '/atlas_scratch/apbennett/IEM_AR5'
output_path = '/atlas_scratch/jschroder/ALF_outputs/PP_2017-07-19-09-03_all_polygons/relative_flammability'
mask_fn = None
alfbin_path = '/workspace/UA/malindgren/repos/alfresco-calibration/alfresco_postprocessing/bin'
sub_dirs = os.listdir( base_path )
sub_dirs = [ i for i in sub_dirs if 'Plot' not in i and 'Core' not in i ] # drop unneeded folders...
ncores = 40

maps_paths = [ os.path.join( base_path, i, 'Maps' ) for i in sub_dirs ]
output_filenames = [ os.path.join( output_path, 'alfresco_relative_flammability_'+sub+'.tif' ) for sub in sub_dirs ]

for maps_path, output_filename in zip( maps_paths, output_filenames ):
	print maps_path

	slurm_path = os.path.join( output_path, 'slurm' )
	if not os.path.exists( slurm_path ):
		os.makedirs( slurm_path )

	slurm_file = os.path.join( slurm_path, 'slurm_run_{}.slurm'.format(maps_path.split(os.path.sep)[-2]) )
	with open( slurm_file, 'w' ) as f:
		# change dir to the alf_pp bin dir
		os.chdir( alfbin_path )
		command = 'python alfresco_relative_flammability.py -p ' + maps_path + ' -o ' + output_filename + ' -nc ' + str( ncores ) # + ' -m ' + mask_fn
		f.writelines( ("#!/bin/sh\n#SBATCH --ntasks={}\n#SBATCH --nodes=1\n#SBATCH --ntasks-per-node={}\n#SBATCH --account=snap\n#SBATCH --mail-type=all\n#SBATCH --mail-user=malindgren@alaska.edu\n#SBATCH -p main\n\n" + command + '\n').format(ncores) )
	os.system( 'sbatch '+ slurm_file )
