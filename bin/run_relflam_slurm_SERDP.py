# python code to wrap the relative flamm for SLURM run
import os, glob

base_path = '/atlas_scratch/apbennett/Calibration/HighCalib/FMO_Calibrated'
output_path = '/atlas_scratch/malindgren/SERDP/relative_flammability_v2'
mask_fn = '/atlas_scratch/malindgren/SERDP/relative_flammability_v2/SERDP_MASK.tif'
sub_dirs = os.listdir( base_path )
ncores = 160

maps_paths = [ os.path.join( base_path, i, 'Maps' ) for i in sub_dirs ]

output_filenames = [ os.path.join( output_path, 'alfresco_relative_flammability_'+sub+'.tif' ) for sub in sub_dirs ]

for maps_path, output_filename in zip( maps_paths, output_filenames ):
	os.system( 'python /workspace/UA/malindgren/repos/alfresco-calibration/alfresco_postprocessing/bin/alfresco_relative_flammability.py -p ' + maps_path + ' -o ' + output_filename + ' -nc ' + str( ncores ) + ' -m ' + mask_fn  )



