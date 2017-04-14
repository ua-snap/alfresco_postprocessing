import numpy as np
import pandas as pd
from pathos import multiprocessing
import rasterio

# def prep_firescar( fn ):
# 	import rasterio
# 	array1 = rasterio.open( fn ).read( 3 )
# 	array1 = np.where( array1 > -2147483647, 1, 0 )
# 	return array1

def get_repnum( fn ):
	''' 
	based on the current ALFRESCO FireScar naming convention,
	return the replicate number
	'''
	return os.path.basename( fn ).split( '_' )[-2]

def read_raster( fn, band, masked, **kwargs ):
	''' open a raster '''
	with rasterio.open( fn ) as out:
		arr = out.read( band, masked=masked )
	return arr

def sum_firescars( firescar_list, ncores ):
	from functools import partial
	from pathos.mp_map import mp_map

	# groupby the replicate number
	firescar_series = pd.Series( firescar_list )
	repgrouper = firescar_series.apply( get_repnum )
	firescar_groups = [ j.tolist() for i,j in firescar_series.groupby( repgrouper ) ]

	# open the rasters and stack to array with their oob values masked.
	repsums = []
	for group in firescar_groups:
		group_arr = np.ma.array( mp_map( partial( read_raster, band=3, masked=True ), group, nproc=32 ), 
									keep_mask=True, fill_value=-9999 )
		group_sum = np.sum( group_arr, axis=0 )
		repsums = repsums + [ group_sum ]

	repsums = np.ma.array( repsums, keep_mask=True )
	sum_arr = repsums.sum( axis=0 )
	return sum_arr

# def sum_firescars2( firescar_list, ncores ):
# 	''' HUUUGE RAM HOG, but very fast. '''
# 	pool = multiprocessing.Pool( processes=ncores, maxtasksperchild=2 )

# 	# groupby the replicate number
# 	firescar_series = pd.Series( firescar_list )
# 	repgrouper = firescar_series.apply( get_repnum )
# 	firescar_groups = [ j.tolist() for i,j in firescar_series.groupby( repgrouper ) ]

# 	def run( group ):
# 		return np.sum( [ rasterio.open( fn ).read( 3 ) for fn in group ], axis=0 )

# 	repsums = pool.map( run, firescar_groups )
# 	# repsums = [ pool.map( lambda fn: np.sum( [ rasterio.open( fn ).read( 3 ), group ), axis=0 ) for group in firescar_groups ]
# 	pool.close()
# 	sum_arr = np.sum( repsums, axis=0 )
# 	return sum_arr

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

	out = sum_firescars( firescar_list, ncores=ncores )

	# calculate the relative flammability -- and fill in the mask with -9999
	relative_flammability = ( out.astype( np.float32 ) / len( firescar_list ) ).filled()

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
	
	try:
		dirname = os.path.dirname( output_filename )
		if not os.path.exists( dirname ):
			os.makedirs( dirname )
	except:
		pass

	with rasterio.open( output_filename, 'w', **meta ) as out_rst:
		out_rst.write( np.around( relative_flammability, 4 ), 1 )

	return output_filename


if __name__ == '__main__':
	import glob, os

	# input path
	maps_path = '/atlas_scratch/apbennett/IEM_AR5/CCSM4_rcp45/Maps'
	model = 'CCSM4'
	scenario = 'rcp45'
	output_path = os.path.join( '/atlas_scratch/malindgren/ALFRESCO_IEM_DERIVED_DEC2016', model, 'relative_flammability' )

	output_filename = os.path.join( output_path, 'alfresco_relative_flammability_' + model + '_' + scenario + '_' + str(1901) + '_' + str(2100) + '.tif' )

	# list the rasters we are going to use here
	firescar_list = [ os.path.join( root, fn ) for root, subs, files in os.walk( maps_path ) for fn in files if 'FireScar_' in fn and fn.endswith('.tif') ]

	# run relative flammability
	relflam_fn = relative_flammability( firescar_list, output_filename, ncores=50, mask_arr=None, mask_value=None, crs={'init':'epsg:3338'} )


# # # TESTING # # # 
# duplicate the existing test data to a few replicates
# duplicate = [ [ shutil.copy( fn, fn.replace('_0_', '_'+str(i)+'_') ) for fn in firescar_list ] for i in [1,2,3,4] ]
