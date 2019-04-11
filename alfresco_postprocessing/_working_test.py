# some setup
import os, glob, rasterio
import numpy as np


class AlfrescoDataset( object ):
	'''
	class to take an output ALFRESCO generated output dataset of
	the flavor Veg, Age, or FireScar and break its filename (fn) to 
	elements needed in summary statistics calculations.
	'''
	def __init__( self, fn, sub_domains=None, *args, **kwargs ):
		'''
		parse elemets of the filename passed

		arguments:
		----------
		fn = [str] path to the input alfresco generated file of type FireScar, Age, or Veg
		nodata = [scalar] value to use as a background so final counts do not include it.
		sub_domains = [alfresco_postprocessing.SubDomains] alfresco_postprocessing SubDomains object

		returns:
		--------
		object of type AlfrescoDataset

		'''
		import rasterio
		self.fn = fn
		self.sub_domains = sub_domains
		self._parse_alf_fn()
		self.rst = rasterio.open( self.fn )
		self._band_reader()
		self.sub_domains = sub_domains

	def _parse_alf_fn( self ):
		'''
		parse the fn data to the needed variable, replicate, year
		'''
		import os
		dirname, basename = os.path.split( self.fn )
		variable, replicate, year_ext = basename.split( '_' )
		year, ext = year_ext.split( '.' )
		self.variable = variable
		self.replicate = replicate
		self.year = year
	def _band_reader( self ):
		''' select proper band from different input variable groups '''
		band = 1
		if self.variable == 'FireScar':
			band = 2
		self.raster_arr = self.rst.read( band )

class SubDomains( object ):
	'''
	rasterize subdomains shapefile to ALFRESCO AOI of output set
	'''
	def __init__( self, subdomains_fn, rasterio_raster, id_field, **kwargs ):
		'''
		initializer for the SubDomains object

		The real magic here is that it will use a generator to loop through the 
		unique ID's in the sub_domains raster map generated.
		'''
		import numpy as np

		self.subdomains_fn = subdomains_fn
		self.rasterio_raster = rasterio_raster
		self.id_field = id_field
		self._rasterize_subdomains( self.subdomains_fn, self.rasterio_raster, self.id_field )

	def _rasterize_subdomains( self, shapefile_fn, rasterio_raster, id_field, fill=0 ):
		'''
		rasterize a subdomains shapefile to the extent and resolution of 
		a template raster file. The two must be in the same reference system 
		or there will be potential issues. 

		returns:
			numpy.ndarray with the shape of the input raster and the shapefile
			polygons burned in with the values of the id_field of the shapefile

		gotchas:
			currently the only supported data type is uint8 and all float values will be
			coerced to integer for this purpose.  Another issue is that if there is a value
			greater than 255, there could be some error-type issues.  This is something that 
			the user needs to know for the time-being and will be fixed in subsequent versions
			of rasterio.  Then I can add the needed changes here.

		'''
		import geopandas as gpd
		import numpy as np

		gdf = gpd.read_file( self.subdomains_fn )
		id_groups = gdf.groupby( self.id_field ) # iterator of tuples (id, gdf slice)

		out_shape = self.rasterio_raster.height, self.rasterio_raster.width
		out_transform = self.rasterio_raster.transform

		arr_list = [ self._rasterize_id( df, value, out_shape, out_transform, fill=fill ) for value, df in id_groups ]
		self.subdomains = arr_list
	@staticmethod
	def _rasterize_id( df, value, out_shape, out_transform, fill=0 ):
		from rasterio.features import rasterize
		geom = df.geometry
		out = rasterize( ( ( g, value ) for g in geom ),
							out_shape=out_shape,
							transform=out_transform,
							fill=fill )
		return out

class AlfrescoFire( object ):
	'''
	calculate ALFRESCO output FireScar Metrics
	'''
	def __init__( self, alf_ds, **kwargs ):
		'''
		initialize the firescar data
		'''
		self.alf_ds = alf_ds
		# self.fire_bool = alf_ds.rst.read( 1 ) # [NYI] used in relative flammability map aggregator
		self.fire_counts = self._counter_wrapper( )
		self.all_fire_sizes = self._all_fire_sizes( )
		self.avg_fire_size = self._avg_fire_size( )
		self.number_of_fires = self._number_of_fires( )
		self.total_area_burned = self._total_area_burned( )

	def _all_fire_sizes( self, *args, **kwargs ):
		if self.alf_ds.sub_domains != None:
			out = { i:self.fire_counts[ i ].values() for i in self.fire_counts.keys() }
		elif self.alf_ds.sub_domains == None:
			out = self.fire_counts.values()
		else:
			BaseException( 'check sub_domains input' )
		return out
	def _avg_fire_size( self, *args, **kwargs ):
		if self.alf_ds.sub_domains != None:
			out = { i:(np.average( self.all_fire_sizes[ i ]) if len(self.all_fire_sizes[ i ]) > 0 else 0 ) for i in self.all_fire_sizes }
		elif self.alf_ds.sub_domains == None:
			out = np.average( self.all_fire_sizes )
		else:
			BaseException( 'check sub_domains input' )
		return out
	def _number_of_fires( self, *args, **kwargs ):
		if self.alf_ds.sub_domains != None:
			out = { i:len( self.fire_counts[ i ].values() ) for i in self.fire_counts.keys() }
		elif self.alf_ds.sub_domains == None:
			out = np.max( self.fire_counts.keys() )
		else:
			BaseException( 'check sub_domains input' )
		return out
	def _total_area_burned( self, *args, **kwargs ):
		if self.alf_ds.sub_domains != None:
			out = { i:np.sum( self.fire_counts[ i ].values() ) for i in self.fire_counts.keys() }
		elif self.alf_ds.sub_domains == None:
			out = sum( self.fire_counts.values() )
		else:
			BaseException( 'check sub_domains input' )
		return out
	def _unique_counts_domains( self, background_value=0 ):
		domains = self.alf_ds.sub_domains.subdomains
		domains = [ (np.unique( domain[domain > 0] )[0], domain) for domain in domains ]
		raster_arr = self.alf_ds.raster_arr
		return { domain_num:dict( zip( *np.unique( raster_arr[ (domain == domain_num) & (raster_arr > 0) ], return_counts=True ) ) ) for domain_num, domain in domains }
	def _counter_wrapper( self, background_value=0 ):
		if self.alf_ds.sub_domains != None:
			out = self._unique_counts_domains( )
		elif self.alf_ds.sub_domains == None:
			out = dict( zip( *np.unique( self.alf_ds.raster_arr, return_counts=True ) ) )
		else:
			BaseException( 'check sub_domains input' )
		return out

class AlfrescoVeg( object ):
	'''
	class to hold the age and veg metrics data
	'''
	def __init__( self, alf_ds, **kwargs ):
		'''
		initialize the firescar data
		'''
		self.alf_ds = alf_ds
		self.veg_counts = self._counter_wrapper( )
	def _unique_counts_domains( self, background_value=0 ):
		domains = self.alf_ds.sub_domains.subdomains
		domains = [ (np.unique( domain[domain > 0] )[0], domain) for domain in domains ]
		raster_arr = self.alf_ds.raster_arr
		return { domain_num:dict( zip( *np.unique( raster_arr[ domain == domain_num ], return_counts=True ) ) ) for domain_num, domain in domains }
	def _counter_wrapper( self, background_value=0 ):
		if self.alf_ds.sub_domains != None:
			out = self._unique_counts_domains( )
		elif self.alf_ds.sub_domains == None:
			out = dict( zip( *np.unique( self.alf_ds.raster_arr, return_counts=True ) ) )
		else:
			BaseException( 'check sub_domains input' )
		return out

# ** ** STEPS TO RUNNING: ** **
# read
maps_path = '/atlas_scratch/apbennett/IEM/FinalCalib/cccma_cgcm3_1.sresa1b/Maps'

subdomains_fn = '/workspace/Shared/Users/jschroder/ALFRESCO_SERDP/Data/Domains/newfmo.shp'
id_field = 'OID'
rst = rasterio.open( fire_files[0] )
sub_domains = SubDomains( subdomains_fn, rst, id_field )
# subdomains = sub_domains.subdomains

# calculate fire
fire_files = glob.glob( os.path.join( maps_path, 'FireScar_*.tif' ) )
fn = fire_files[ 100 ]
ds = AlfrescoDataset( fn, sub_domains=sub_domains )
fire = AlfrescoFire( ds )

# calculate veg
veg_files = glob.glob( os.path.join( maps_path, 'Veg_*.tif' ) )
fn = veg_files[ 100 ]
ds = AlfrescoDataset( fn, sub_domains=sub_domains )
veg = AlfrescoVeg( ds )


