import numpy as np
import pandas as pd
# import multiprocessing
from pathos import multiprocessing
import rasterio

class FireSum:
	'''
	simple class to sum prepared firescar outputs to boolean. where fire=1, nofire=0
	in a rolling manner using multiprocessing and callbacks.
	The only needed input is a numpy 2-D array that will be used as a template to 
	'zero-out' the rolling sum.  multiprocessing Lock() is used to ensure access to
	the add method is performed by only one worker at a time.  This is performed to 
	reduce the RAM overhead of summation across the entire range of outputs using 
	numpy and multiprocessing map(). 
	Arguments:
		arr = [numpy.ndarray] with 2 dimensions in the order of (lat, lon)
	
	Returns:
		FireSum() object with zeroed-out template of arr
	'''
	def __init__( self, arr ):
		self.value = np.zeros_like( arr ) #this is the initialization of the sum
		self.lock = multiprocessing.Lock()
		self.count = 0
		
	def add( self, value ):
		self.count += 1
		self.lock.acquire() #lock so sum is correct if two processes return at same time
		self.value += value #the actual summation
		self.lock.release()

def prep_firescar( fn ):
	import rasterio
	array1 = rasterio.open( fn ).read( 3 )
	array1 = np.where( array1 > -2147483647, 1, 0 )
	return array1

def get_repnum( fn ):
	''' 
	based on the current ALFRESCO FireScar naming convention,
	return the replicate number
	'''
	return os.path.basename( fn ).split( '_' )[-2]

def sum_firescars( firescar_list, ncores ):
	pool = multiprocessing.Pool( processes=ncores, maxtasksperchild=2 )

	# tmp_rst = rasterio.open( firescar_list[0] )
	# tmp_arr = tmp_rst.read( 3 )

	# groupby the replicate number
	firescar_series = pd.Series( firescar_list )
	repgrouper = firescar_series.apply( get_repnum )
	firescar_groups = [ j.tolist() for i,j in firescar_series.groupby( repgrouper ) ]

	repsums = [ np.sum( pool.map( lambda fn: rasterio.open( fn ).read( 3 ), group ), axis=0 ) for group in firescar_groups ]
	pool.close()
	sum_arr = np.sum( repsums, axis=0 )
	return sum_arr

def sum_firescars2( firescar_list, ncores ):
	''' HUUUGE RAM HOG, but very fast. '''
	pool = multiprocessing.Pool( processes=ncores, maxtasksperchild=2 )

	# groupby the replicate number
	firescar_series = pd.Series( firescar_list )
	repgrouper = firescar_series.apply( get_repnum )
	firescar_groups = [ j.tolist() for i,j in firescar_series.groupby( repgrouper ) ]

	def run( group ):
		return np.sum( [ rasterio.open( fn ).read( 3 ) for fn in group ], axis=0 )

	repsums = pool.map( run, firescar_groups )
	# repsums = [ pool.map( lambda fn: np.sum( [ rasterio.open( fn ).read( 3 ), group ), axis=0 ) for group in firescar_groups ]
	pool.close()
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
	relative_flammability = ( out / len( firescar_list ) )

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
	output_filename = '/workspace/Shared/Users/malindgren/SERDP/test_fire/output/relative_flammability_test_async.tif'

	# list the rasters we are going to use here
	firescar_list = glob.glob( os.path.join( maps_path, 'Fire*.tif' ) )

	# make the list larger for a real dummy set. this will make 200 years * 25 replicates
	# firescar_list = [ i for i in firescar_list for j in range( 25 ) ]

	# run relative flammability
	relflam_fn = relative_flammability( firescar_list, output_filename, ncores=32, mask_arr=None, mask_value=None, crs={'init':'epsg:3338'} )



# # # TESTING # # # 
# duplicate the existing test data to a few replicates
duplicate = [ [ shutil.copy( fn, fn.replace('_0_', '_'+str(i)+'_') ) for fn in firescar_list ] for i in [1,2,3,4] ]

