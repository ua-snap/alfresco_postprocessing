def prep_firescar( fn ):
	import rasterio
	arr = rasterio.open( fn ).read( 3 )
	arr = np.where( arr > -2147483647, 1, 0 )
	return arr

def list_files( maps_path, wildcard='FireScar_' ):
	'''
	new list files that can deal with the year sub-direcories 
	test change we are making to improve performance.
	'''
	import os
	files = [ os.path.join( root, i ) for root, subs, files in os.walk( maps_path ) \
			if len( files ) > 0 for i in files if wildcard in i  ]
	return files

def sum_firescars( firescar_list ):
	import numpy as np
	return np.sum( pool.map( prep_firescar, firescar_list ), axis=0 )

def _run( fs_grouped, ncpus ):
	return np.sum( [ sum_firescars( fs_list ) for fs_list in fs_grouped ], axis=0 )

if __name__ == '__main__':
	import numpy as np
	# import multiprocessing
	from pathos import multiprocessing
	import rasterio

	maps_path = '/atlas_scratch/apbennett/Calibration/HighCalib/FMO_Calibrated/GISS-E2-R_rcp85_AltFMO/Maps'
	ncpus = 32
	firescar_list = list_files( maps_path )
	firescar_grouped = np.array_split( np.array( firescar_list ), len(firescar_list)/ncpus )
	pool = multiprocessing.Pool( ncpus, maxtasksperchild=2 )
	out = _run( firescar_grouped, ncpus )
	pool.close()