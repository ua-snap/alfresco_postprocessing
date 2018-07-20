# RUN RELATIVE FLAMMABILITY ACROSS ALL SUB-DIRS in IEM_AR5 directory
def run_model( fn, maps_path, output_filename, ncores, begin_year, end_year ):
	import os, subprocess
	head = '#!/bin/sh\n' + \
			'#SBATCH --ntasks=32\n' + \
			'#SBATCH --nodes=1\n' + \
			'#SBATCH --ntasks-per-node=32\n' + \
			'#SBATCH --account=snap\n' + \
			'#SBATCH --mail-type=FAIL\n' + \
			'#SBATCH --mail-user=malindgren@alaska.edu\n' + \
			'#SBATCH -p viz\n'
	
	script_path = '/workspace/UA/malindgren/repos/alfresco_postprocessing/bin/alfresco_relative_flammability.py'
	with open( fn, 'w' ) as f:
		command = ' '.join([ 'ipython', script_path,\
							 '--', '-p', maps_path, '-o', output_filename, '-nc', str(ncores), '-by', str(begin_year), '-ey', str(end_year) ])
		f.writelines( head + '\n' + command + '\n' )
	subprocess.call([ 'sbatch', fn ])
	return 1

if __name__ == '__main__':
	import os, glob, subprocess

	base_path = '/atlas_scratch/apbennett/IEM_AR5'
	output_path = '/atlas_scratch/malindgren/ALFRESCO_PostProcessing/relative_flammability'
	mask_fn = None
	sub_dirs = [ i for i in glob.glob(base_path+'/*') if 'Plot' not in i and 'Core' not in i and os.path.isdir(i) ] # drop unneeded folders...
	# i suggest keeping this number low due to RAM overhead issues.  
	#  10 is good for 200 years / 200 reps over IEM AOI
	ncores=10

	# temp below -- remove after re-run
	ncores = 2
	sub_dirs = [ '/atlas_scratch/apbennett/IEM_AR5/IPSL-CM5A-LR_rcp85','/atlas_scratch/apbennett/IEM_AR5/NCAR-CCSM4_rcp85','/atlas_scratch/apbennett/IEM_AR5/MRI-CGCM3_rcp85']
	sub_dirs = ['/atlas_scratch/apbennett/IEM_AR5/MRI-CGCM3_rcp85']
	# end temp above

	# IEM DATA TIMESTEPS...
	year_ranges = [(1900,1999), (2000,2099), (1900,2099)]
	
	# temp remove below
	year_ranges = [(1900,2099)]
	# end temp remove above

	maps_paths = [ os.path.join( base_path, i, 'Maps' ) for i in sub_dirs ]
	output_filenames = [ os.path.join( output_path, 'alfresco_relative_flammability_'+os.path.basename(sub)+'.tif' ) for sub in sub_dirs ]

	for maps_path, out_fn in zip( maps_paths, output_filenames ):
		for year_range in year_ranges:
			begin_year, end_year = year_range
			output_filename = out_fn.replace('.tif', '_{}_{}.tif'.format(str(begin_year), str(end_year)))
		
			slurm_path = os.path.join( output_path, 'slurm' )
			if not os.path.exists( slurm_path ):
				os.makedirs( slurm_path )
			
			os.chdir( slurm_path )
			
			slurm_file = os.path.join( slurm_path, 'slurm_run_{}.slurm'.format(maps_path.split(os.path.sep)[-2]) )
			run_model( slurm_file, maps_path, output_filename, ncores, begin_year, end_year )
