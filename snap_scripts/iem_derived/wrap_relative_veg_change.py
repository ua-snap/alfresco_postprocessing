# wrap the relative veg change...
def run_model( command, fn ):
	import subprocess, os

	head = '#!/bin/sh\n' + \
			'#SBATCH --ntasks=32\n' + \
			'#SBATCH --nodes=1\n' + \
			'#SBATCH --ntasks-per-node=32\n' + \
			'#SBATCH --account=snap\n' + \
			'#SBATCH --mail-type=FAIL\n' + \
			'#SBATCH --mail-user=malindgren@alaska.edu\n' + \
			'#SBATCH -p main\n'

	with open( fn, 'w' ) as f:
		f.writelines( head + "\n" + command + '\n' )
	
	subprocess.call([ 'sbatch', fn ])
	return 1

if __name__ == '__main__':
	import glob, os, itertools

	# input args
	base_path = '/atlas_scratch/apbennett/IEM_AR5'
	output_base_path = '/atlas_scratch/malindgren/ALFRESCO_IEM_DERIVED_DEC2016'
	scenarios = ['rcp45']#, 'rcp85']
	models = ['CCSM4']#, 'GFDL-CM3', 'IPSL-CM5A-LR', 'MRI-CGCM3', 'GISS-E2-R']
	script_path = '/workspace/UA/malindgren/repos/alfresco-calibration/alfresco_postprocessing/bin/alfresco_relative_vegetation_change.py'

	ncpus = '50'
	year_ranges = [ ('1901', '1999')]#, ('2000', '2099'), ('1901', '2100') ]
	
	for scenario, model in itertools.product( scenarios, models ):
		output_path = os.path.join( output_base_path, model, 'relative_vegetation_change' )
		if not os.path.exists( output_path ):
			os.makedirs( output_path )
		
		for begin_year, end_year in year_ranges:
			input_path = os.path.join( base_path, '_'.join([model, scenario]), 'Maps' )

			command = 'python ' + script_path + ' -p ' + \
						input_path + ' -o ' + output_path + ' -m ' + model + ' -s ' + \
						scenario + ' -n ' + ncpus + ' -by ' + begin_year + ' -ey ' + end_year

			slurm_fn = 'relveg_slurm_{}_{}_{}-{}.slurm'.format(model, scenario, begin_year, end_year)
			slurm_fn = os.path.join( output_base_path, 'slurm_files', slurm_fn )
			
			dirname = os.path.dirname( slurm_fn )
			
			if not os.path.exists( dirname ):
				os.makedirs( dirname )
			
			os.chdir( dirname )

			done = run_model( command, slurm_fn )

