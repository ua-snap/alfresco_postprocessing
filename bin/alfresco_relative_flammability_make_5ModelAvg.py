# make relflam 5modelAvg
def open_raster( fn, band=1 ):
	with rasterio.open( fn ) as rst:
		arr = rst.read(band)
	return arr

if __name__ == '__main__':
	import os, glob, rasterio, itertools
	import numpy as np

	base_path = '/atlas_scratch/malindgren/ALFRESCO_PostProcessing/relative_flammability'
	scenarios = ['rcp45', 'rcp60', 'rcp85']
	year_groups = ['1900_1999', '2000_2099', '1900_2099']

	for scenario, year_group in itertools.product(scenarios, year_groups):
		files = glob.glob(os.path.join( base_path, '*{}*{}*.tif'.format(scenario, year_group)))
		files = [ fn for fn in files if not '5ModelAvg' in fn ] # remove any old 5ModelAvg files
		with rasterio.open(files[0]) as tmp:
			meta = tmp.meta.copy()
			meta.update(compress='lzw')
			mask = tmp.read(1) == -9999
		
		# read in the files
		arr = np.array([open_raster(fn) for fn in files]).mean(axis=0).astype(np.float32)
		arr[ mask ] = -9999
		out_fn = os.path.join( base_path, 'alfresco_relative_flammability_5ModelAvg_{}_{}.tif'.format( scenario, year_group) )
		with rasterio.open( out_fn, 'w', **meta ) as out:
			out.write( arr, 1 )


