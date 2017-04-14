import numpy as np
# import multiprocessing
from pathos import multiprocessing
import rasterio
class Sum( object ):
	def __init__( self, maps_path, ncpus ):
		self.maps_path = maps_path
		self.firescar_list = self.list_files()
		self.ncpus = ncpus
		self.firescar_grouped = np.array_split( np.array( self.firescar_list ), ncpus*3 )
		# self.pool = multiprocessing.Pool( self.ncpus, maxtasksperchild=2 )

	@staticmethod
	def prep_firescar( fn ):
		import rasterio
		arr = rasterio.open( fn ).read( 3 )
		arr = np.where( arr > -2147483647, 1, 0 )
		return arr
	def list_files( self, wildcard='FireScar_' ):
		'''
		new list files that can deal with the year sub-direcories 
		test change we are making to improve performance.
		'''
		import os
		files = [ os.path.join( root, i ) for root, subs, files in os.walk( self.maps_path ) \
				if len( files ) > 0 for i in files if wildcard in i  ]
		return files
	@staticmethod
	def sum_firescars( fx, firescar_list, ncores ):
		import numpy as np
		pool = multiprocessing.Pool( ncores, maxtasksperchild=2 )
		return np.sum( pool.map( fx, firescar_list ), axis=0 )
		pool.close()
	def _run( self ):
		return np.sum( [ self.sum_firescars( getattr( self, 'prep_firescar' ), fs_list, getattr(self,'ncpus') ) for fs_list in self.firescar_grouped ], axis=0 )
