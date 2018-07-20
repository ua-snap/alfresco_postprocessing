import numpy as np
import pandas as pd
import rasterio
try:
	from pathos import multiprocessing
except:
	import multiprocessing

def get_repnum( fn ):
	''' 
	based on the current ALFRESCO FireScar naming convention,
	return the replicate number
	'''
	return os.path.basename( fn ).split( '_' )[-2]

def read_raster_band( fn, band ):
	''' cleanly open and read a band from a raster fn '''
	with rasterio.open( fn ) as rst:
		arr = rst.read( band )
	return arr

def prep_firescar( fn ):
	import rasterio
	arr = read_raster_band( fn, band=3 )
	arr = np.where( arr > -2147483647, 1, 0 )
	return arr

def sum_firescars( firescar_list, ncores ):
	pool = multiprocessing.Pool( processes=ncores, maxtasksperchild=2 )
	# groupby the replicate number
	firescar_series = pd.Series( firescar_list )
	repgrouper = firescar_series.apply( get_repnum )
	firescar_groups = [ j.tolist() for i,j in firescar_series.groupby( repgrouper ) ]

	repsums = [ np.sum( pool.map( lambda fn: prep_firescar(fn), group ), axis=0 ) 
					for group in firescar_groups ]

	pool.close()
	pool.join()
	sum_arr = np.sum( repsums, axis=0 )
	return sum_arr

def relative_flammability( firescar_list, output_filename, ncores=None, mask_arr=None, mask_value=None, crs=None ):
	'''
	run relative flammability.
	Arguments:
		firescar_list = [list] string paths to all GeoTiff FireScar outputs to be processed
		output_filename = [str] path to output relative flammability filename to be generated. 
						* only GTiff supported. *
		ncores = [int] number of cores to use if None multiprocessing.cpu_count() used.
		mask_arr = [numpy.ndarray] numpy ndarray with dimensions matching the rasters' arrays
					listed in firescar_list and masked where 1=dontmask 0=mask (this is opposite
					numpy mask behavior, but follows common GIS patterns ) * THIS MAY CHANGE. *
		mask_value = [numeric] single numeric value determining the value of the newly masked out
					regions. If None, the nodata value from the firescar outputs will be used and 
					if this is an invalid value, it will be set to -9999.
		crs=[dict] rasterio-compatible crs dict object i.e.: {'init':'epsg:3338'}
	
	Returns:
		output_filename, with the side effect of the relative flammability raster being written to 
		disk in that location.
	'''
	tmp_rst = rasterio.open( firescar_list[0] )

	if ncores == None:
		ncores = multiprocessing.cpu_count() - 1

	# ALTERNATIVE SUM FIRESCARS in VERSION 2
	out = sum_firescars( firescar_list, ncores=ncores )

	# calculate the relative flammability
	relative_flammability = ( out / float( len( firescar_list ) ) )

	if mask_value == None:
		mask_value = tmp_rst.nodata
		if mask_value == None or mask_value == '':
			print( 'setting mask_value to -9999')
			mask_value = -9999

	if mask_arr:
		relative_flammability[ mask_arr == 0 ] = mask_value

	meta = tmp_rst.meta
	# pop out transform to overcome warning
	if 'transform' in meta.keys():
		_ = meta.pop( 'transform' )

	meta.update( compress='lzw', count=1, dtype='float32', nodata=mask_value )

	if crs:
		meta.update( crs=crs )

	with rasterio.open( output_filename, 'w', **meta ) as out:
		out.write( relative_flammability.astype( np.float32 ), 1 )

	return output_filename


if __name__ == '__main__':
	import glob, os

	# input path
	maps_path = '/workspace/Shared/Users/malindgren/SERDP/test_fire'

	# output filename
	output_filename = '/workspace/Shared/Users/malindgren/ALFRESCO/relative_flammability_test_async.tif'

	# list the rasters we are going to use here
	firescar_list = glob.glob( os.path.join( maps_path, 'Fire*.tif' ) )

	# make the list larger for a real dummy set. this will make 200 years * 25 replicates
	# firescar_list = [ i for i in firescar_list for j in range( 25 ) ]

	# run relative flammability
	relflam_fn = relative_flammability( firescar_list, output_filename, ncores=50, mask_arr=None, mask_value=None, crs={'init':'epsg:3338'} )



# # # TESTING # # # 
# duplicate the existing test data to a few replicates
duplicate = [ [ shutil.copy( fn, fn.replace('_0_', '_'+str(i)+'_') ) for fn in firescar_list ] for i in [1,2,3,4] ]

