import numpy as np
import pandas as pd
from pathos import multiprocessing
from pathos.mp_map import mp_map
import rasterio
import multiprocessing as mp
from functools import partial

def get_repnum( fn ):
	''' 
	based on the current ALFRESCO FireScar naming convention,
	return the replicate number
	'''
	return os.path.basename( fn ).split( '_' )[-2]

def read_raster( fn, band, masked=False, **kwargs ):
	''' open a raster '''
	with rasterio.open( fn ) as out:
		arr = out.read( band, masked=masked )
	return arr

def prep_firescar( arr ):
	arr = np.where( arr >= 0, 1, 0 )
	return arr

f = partial( read_raster, band=3, masked=False )

def rg( fn ):
	from functools import partial
	arr = f( fn )
	return np.where( arr >= 0, 1, 0 )

# def run_group( group ):
# 	from pathos.mp_map import mp_map
# 	# group_arr = np.array( mp_map( rg, group, nproc=32 ) )
# 	pool = mp.Pool( 32 )
# 	group_arr = np.array( pool.map( rg, group ) )
# 	pool.close()
# 	pool.join()
# 	group_sum = np.sum( group_arr, axis=0 )
# 	return group_sum

def run_group( group ):
	# from pathos.mp_map import mp_map
	group_arr = np.array([ rg(fn) for fn in group ])
	# group_arr = np.array( mp_map( rg, group, nproc=32 ) )
	group_sum = np.sum( group_arr, axis=0 )
	return group_sum

def sum_firescars( firescar_list, ncores ):
	# groupby the replicate number
	firescar_series = pd.Series( firescar_list )
	repgrouper = firescar_series.apply( get_repnum )
	firescar_groups = [ j.tolist() for i,j in firescar_series.groupby( repgrouper ) ]

	# open the rasters and stack to array with their oob values masked.
	pool = mp.Pool( ncores )
	repsums = pool.map( run_group, firescar_groups )
	pool.close()
	pool.join()

	sum_arr = np.sum( np.array(repsums), axis=0 )
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

	out = sum_firescars( firescar_list, ncores=ncores )

	# calculate the relative flammability -- and fill in the mask with -9999
	relative_flammability = ( out.astype( np.float32 ) / len( firescar_list ) )

	if mask_value == None:
		mask_value = tmp_rst.nodata
		if mask_value == None or mask_value == '':
			print( 'setting mask_value to -9999')
			mask_value = -9999

	if mask_arr is not None:
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
	import argparse

	parser = argparse.ArgumentParser( description='program to calculate Relative Flammability from ALFRESCO' )
	parser.add_argument( '-p', '--maps_path', action='store', dest='maps_path', type=str, help='path to ALFRESCO output Maps directory' )
	parser.add_argument( '-o', '--output_filename', action='store', dest='output_filename', type=str, help='path to output directory' )
	parser.add_argument( '-nc', '--ncores', action='store', dest='ncores', type=int, help='number of cores' )
	parser.add_argument( '-by', '--begin_year', action='store', dest='begin_year', type=int, help='beginning year in the range' )
	parser.add_argument( '-ey', '--end_year', action='store', dest='end_year', type=int, help='ending year in the range' )
	# parser.add_argument( '-m', '--mask', nargs='?', const=1, default=None, action='store', dest='mask', type=str, help='path to mask raster if desired.' )

	args = parser.parse_args()
	
	maps_path = args.maps_path
	output_filename = args.output_filename
	ncores = args.ncores
	begin_year = args.begin_year
	end_year = args.end_year
	# if args.mask:
	# 	mask = rasterio.open( args.mask )

	# # TEST
	# maps_path = '/atlas_scratch/apbennett/IEM_AR5/GFDL-CM3_rcp60/Maps'
	# output_filename = '/workspace/Shared/Users/malindgren/TEST_ALF/alf_relflam_test_1900_1999.tif'
	# ncores = 32
	# begin_year = 1900
	# end_year = 1999

	# list the rasters we are going to use here
	firescar_list = [ os.path.join( root, fn ) for root, subs, files in os.walk( maps_path ) 
							for fn in files if 'FireScar_' in fn and fn.endswith('.tif') ]

	year_list = range( begin_year, end_year + 1 )
	firescar_list = [ i for i in firescar_list if int( os.path.basename( i ).split('_')[ len( os.path.basename( i ).split( '_' ) )-1 ].split( '.' )[0] ) in year_list ]

	# mask -- get from the Veg file of firescar_list[0]
	mask = rasterio.open( firescar_list[0].replace('FireScar_', 'Veg_') ).read_masks( 1 )
	mask = (mask == 255).astype(int)
	mask_value = -9999

	# run relative flammability
	relflam_fn = relative_flammability( firescar_list, output_filename, ncores=ncores, mask_arr=mask, mask_value=mask_value, crs={'init':'epsg:3338'} )

