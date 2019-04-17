# * * * * * * * * * * * * * * * * * * * * * * * * * * *
# ALFRESCO POST-PROCESSING DATASET CLASSES
# * * * * * * * * * * * * * * * * * * * * * * * * * * *
import rasterio
import numpy as np

class AlfrescoDataset( object ):
	'''
	class to take an output ALFRESCO generated output dataset of
	the flavor Veg, Age, or FireScar and break its filename (fn) to 
	elements needed in summary statistics calculations.
	'''
	def __init__( self, fn, sub_domains=None, *args, **kwargs ):
		'''
		parse elements of the filename passed

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
		self.variable = None
		self.replicate = None
		self.year = None
		self._parse_fn()
		self.rst = rasterio.open( self.fn )
		self.raster_arr = None
		self._band_reader()
		self.sub_domains = sub_domains
		self._get_names_dict( )
		self._observed = False
		self.veglag = self._get_lag( 'Veg', direction=-1 )

	def _parse_fn( self ):
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
	def _get_names_dict( self ):
		if self.sub_domains != None:
			self.names_dict = self.sub_domains.names_dict
		else:
			self.names_dict = None
	def _get_lag( self, variable, direction=-1 ):
		''' direction can be -1 for negative lag, or 1 for positive lag '''
		import os
		split = os.path.basename( self.fn ).split( '.' )[0].split( '_' )
		year = split[-1]
		if direction == -1:
			split[-1] = str( int( year ) - 1 )
		else:
			split[-1] = str( int( year ) + 1 )
		split[-3] = variable
		return os.path.join( os.path.dirname( self.fn ) , '_'.join( split ) + '.tif' )

	# def _get_lag( self, variable, direction=-1 ):
	# 	''' direction can be -1 for negative lag, or 1 for positive lag '''
	# 	split = self.fn.split( '.' )[0].split( '_' )
	# 	year = split[-1]
	# 	if direction == -1:
	# 		split[-1] = str( int( year ) - 1 )
	# 	else:
	# 		split[-1] = str( int( year ) + 1 )
	# 	split[-3] = variable
	# 	return '_'.join( split ) + '.tif'


class ObservedDataset( AlfrescoDataset ):
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
		super( ObservedDataset, self ).__init__( fn, sub_domains, *args, **kwargs )
		self._observed = True

	def _parse_fn( self ):
		'''
		parse the fn data to the needed variable, replicate, year
		'''
		import os
		dirname, basename = os.path.split( self.fn )
		year_ext = basename.split( '_' )[-1]
		year, ext = year_ext.split( '.' )
		self.variable = 'FireHistory'
		self.replicate = 'observed'
		self.year = year
	def _band_reader( self ):
		''' select proper band from different input variable groups '''
		import rasterio
		from scipy import ndimage

		band = 1
		fire_arr = rasterio.open( self.fn ).read( band )
		label_im, nb_labels = ndimage.label( fire_arr )
		self.raster_arr = label_im


class SubDomains( object ):
	'''
	rasterize subdomains shapefile to ALFRESCO AOI of output set
	'''
	def __init__( self, subdomains_fn, rasterio_raster, id_field, name_field, background_value=0, *args, **kwargs ):
		'''
		initializer for the SubDomains object

		The real magic here is that it will use a generator to loop through the 
		unique ID's in the sub_domains raster map generated.
		'''
		import numpy as np
		self.subdomains_fn = subdomains_fn
		self.rasterio_raster = rasterio_raster
		self.id_field = id_field
		self.name_field = name_field
		self.background_value = background_value
		self._get_subdomains_dict( )
		self._rasterize_subdomains( )

	def _rasterize_subdomains( self ):
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

		arr_list = [ self._rasterize_id( df, value, out_shape, out_transform, background_value=self.background_value ) for value, df in id_groups ]
		arr_list = [ i for i in arr_list if not np.all(i == self.background_value) ] # [added for JFSP app update...]
		self.sub_domains = arr_list
		# update the names dict if arr members were dropped due to non-overlap
		all_values = [ np.unique(i[i != self.background_value])[0] for i in arr_list ] # [added for JFSP app update...]
		self.names_dict = { i:self.names_dict[i] for i in all_values } # [added for JFSP app update...]
	@staticmethod
	def _rasterize_id( df, value, out_shape, out_transform, background_value=0 ):
		from rasterio.features import rasterize
		geom = df.geometry
		out = rasterize( ( ( g, value ) for g in geom ),
							out_shape=out_shape,
							transform=out_transform,
							fill=background_value )
		return out
	def _get_subdomains_dict( self ):
		import geopandas as gpd
		gdf = gpd.read_file( self.subdomains_fn )
		self.names_dict = dict( zip( gdf[self.id_field], gdf[self.name_field] ) )

class SubDomainsRaster( object ):
	'''
	rasterize subdomains shapefile to ALFRESCO AOI of output set
	'''
	def __init__( self, subdomains_fn, rasterio_raster, background_value=0, id_name_dict=None, *args, **kwargs ):
		'''
		initializer for the SubDomains object

		The real magic here is that it will use a generator to loop through the 
		unique ID's in the sub_domains raster map generated.
		'''
		import numpy as np
		self.subdomains_fn = subdomains_fn
		self.rasterio_raster = rasterio_raster
		self.background_value = background_value
		self.names_dict = id_name_dict
		self._validate_raster_domains()
		self.sub_domains = self._breakout_domains()
		self._get_subdomains_dict()

	def _validate_raster_domains( self ):
		domains = rasterio.open( self.subdomains_fn )
		alf = self.rasterio_raster

		# test shape
		domains_arr = domains.read( 1 )
		alf_arr = domains.read( 1 )
		try:
			assert domains_arr == alf_arr
			# this might need some base GDAL love to properly compare ref sys
			# write a function to do this...if needed
			assert domains.crs == alf_arr.crs
		except:
			TypeError( 'invalid raster input.  Must match alfresco output raster.' )
	def _breakout_domains( self ):
		import numpy as np
		domains = rasterio.open( self.subdomains_fn )
		domains_arr = domains.read( 1 )
		# we require a background value HERE -- COULD BE A GOTCHA!
		uniques = np.unique( domains_arr[ domains_arr != self.background_value ] )
		# add an attribute to self of unique domains
		self.unique_domains = uniques
		
		arr_list = []
		for val in uniques:
			arr = np.zeros_like( domains_arr )
			arr[ domains_arr == val ] = val
			arr_list.append( arr )
		return arr_list
	def _get_subdomains_dict( self ):
		import geopandas as gpd
		if self.names_dict == None:
			self.names_dict = { i:str(i) for i in self.unique_domains }

class FullDomain( object ):
	'''
	make a subdomains object when there are no domains passed to the run function.
	This allows all data to have the same output JSON structure.
	Nesting for this variable gives the domain name of `_alf_`.
	'''
	def __init__( self, rasterio_raster, background_value=None, *args, **kwargs ):
		'''
		initializer for the SubDomains object

		The real magic here is that it will use a generator to loop through the 
		unique ID's in the sub_domains raster map generated.
		'''
		import numpy as np
		self.rasterio_raster = rasterio_raster
		self.names_dict = { 1:'_alf_' }
		self.background_value = background_value
		self.sub_domains = self._get_full_domain()

	def _get_full_domain( self ):
		hold = self.rasterio_raster.read( 1 ).astype( np.int )
		if self.background_value == None:
			hold[:] = 1
		else:
			hold[ hold != self.background_value ] = 1
			hold[ hold == self.background_value ] = 0
		return [ hold ]






