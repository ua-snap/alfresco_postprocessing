# python code to wrap the relative flamm for SLURM run
import os, glob

base_path = '/atlas_scratch/apbennett/Calibration/HighCalib/FMO_Calibrated'
output_path = '/atlas_scratch/malindgren/SERDP/relative_flammability_EPA'
mask_fn = '/atlas_scratch/malindgren/SERDP/relative_flammability_v2/SERDP_MASK.tif'
sub_dirs = os.listdir( base_path )
sub_dirs = [ i for i in sub_dirs if 'Plot' not in i ] # dont use the plot folder
ncores = 32

maps_paths = [ os.path.join( base_path, i, 'Maps' ) for i in sub_dirs ]
output_filenames = [ os.path.join( output_path, 'alfresco_relative_flammability_'+sub+'.tif' ) for sub in sub_dirs ]

for maps_path, output_filename in zip( maps_paths, output_filenames ):
	print maps_path
	# command = 'python /workspace/UA/malindgren/repos/alfresco-calibration/alfresco_postprocessing/bin/alfresco_relative_flammability.py -p ' + maps_path + ' -o ' + output_filename + ' -nc ' + str( ncores ) + ' -m ' + mask_fn
	# os.system( command )
	# make the slurm sbatch file
	slurm_file = os.path.join( output_path, 'slurm_run.slurm' )
	with open( slurm_file, 'w' ) as f:
		command = 'python /workspace/UA/malindgren/repos/alfresco-calibration/alfresco_postprocessing/bin/alfresco_relative_flammability.py -p ' + maps_path + ' -o ' + output_filename + ' -nc ' + str( ncores ) + ' -m ' + mask_fn
		f.writelines( "#!/bin/sh\n#SBATCH --ntasks=32\n#SBATCH --nodes=1\n#SBATCH --ntasks-per-node=32\n#SBATCH --account=snap\n#SBATCH --mail-type=all\n#SBATCH --mail-user=malindgren@alaska.edu\n#SBATCH -p main\n\n" + command + '\n' )
	os.system( 'sbatch '+ slurm_file )
