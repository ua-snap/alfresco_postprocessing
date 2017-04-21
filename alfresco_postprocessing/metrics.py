# * * * * * * * * * * * * * * * * * * * * * * * * * * *
# ALFRESCO POST-PROCESSING METRICS CLASSES
# * * * * * * * * * * * * * * * * * * * * * * * * * * *
import numpy as np

class Fire( object ):
	'''
	calculate FireScar metrics from ALFRESCO Fire Dynamics Model 
	output rasters across subdomains if applicable.
	'''
	def __init__( self, alf_ds, **kwargs ):
		'''
		initialize fire scar data and calculate fire metrics

		Arguments:
		----------
		alf_ds = (AlfrescoDataset) an object of type AlfrescoDataset which contains
				all needed attributes to run the fire metrics.

		returns:
		--------
		object of class AlfrescoFire containing attributes calculated over the raster
		and potentially the subdomains in that area of interest.

		'''
		self.alf_ds = alf_ds
		self.fire_counts = self._unique_counts_domains( )
		self.all_fire_sizes = self._all_fire_sizes( )
		self.avg_fire_size = self._avg_fire_size( )
		self.number_of_fires = self._number_of_fires( )
		self.total_area_burned = self._total_area_burned( )

	def _all_fire_sizes( self, *args, **kwargs ):
		return { i:self.fire_counts[ i ].values() for i in self.fire_counts.keys() }
	def _avg_fire_size( self, *args, **kwargs ):
		return { i:( np.round( np.average( self.all_fire_sizes[ i ]), decimals=2 ) \
					if len(self.all_fire_sizes[ i ]) > 0 else 0 ) for i in self.all_fire_sizes }
	def _number_of_fires( self, *args, **kwargs ):
		return { i:len( self.fire_counts[ i ].values() ) for i in self.fire_counts.keys() }
	def _total_area_burned( self, *args, **kwargs ):
		return { i:np.sum( self.fire_counts[ i ].values() ) for i in self.fire_counts.keys() }
	def _unique_counts_domains( self ):
		domains = self.alf_ds.sub_domains.sub_domains
		domains = [ (np.unique( domain[domain > 0] )[0], domain) for domain in domains ]
		raster_arr = self.alf_ds.raster_arr
		return { self.alf_ds.sub_domains.names_dict[domain_num]:\
					dict( zip( *np.unique( raster_arr[ (domain == domain_num) & (raster_arr > 0) ], return_counts=True ) ) ) \
					for domain_num, domain in domains } # changed (raster_arr > 0) from (raster_arr >= 0)  WATCH IT!


class Veg( object ):
	'''
	calculate vegetation metrics from ALFRESCO Fire Dynamics Model 
	output rasters across subdomains if applicable.
	'''
	def __init__( self, alf_ds, veg_name_dict, **kwargs ):
		'''
		initialize vegetation data and calculate veg metrics

		Arguments:
		----------
		alf_ds = (AlfrescoDataset) an object of type AlfrescoDataset which contains
				all needed attributes to run the vegetation metrics.

		returns:
		--------
		object of class AlfrescoVeg containing attributes calculated over the raster
		and potentially the subdomains in that area of interest.

		'''
		self.alf_ds = alf_ds
		self.veg_name_dict = veg_name_dict
		self.veg_counts = self._unique_counts_domains( )

	def _unique_counts_domains( self ):
		domains = self.alf_ds.sub_domains.sub_domains
		domains = [ (np.unique( domain[domain > 0] )[0], domain) for domain in domains ]
		raster_arr = self.alf_ds.raster_arr
		hold = { self.alf_ds.sub_domains.names_dict[domain_num]:\
					dict( zip( *np.unique( raster_arr[ domain == domain_num ], return_counts=True ) ) ) \
					for domain_num, domain in domains }
		return { k:{ self.veg_name_dict[int(vegtype)]:v[int(vegtype)] \
					for vegtype in v.keys() if vegtype in self.veg_name_dict.keys() } \
					for k,v in hold.iteritems() }


class VegFire( object ):
	'''
	calculate FireScar metrics based on vegetation types or groups 
	of vegetation types from the year prior to fire across subdomains
	if applicable.
	'''
	def __init__( self, alf_ds, veg_groups=None, **kwargs ):
		'''
		initialize fire scar data and calculate fire metrics

		Arguments:
		----------
		alf_ds = (AlfrescoDataset) an object of type AlfrescoDataset which contains
				all needed attributes to run the fire metrics.

		returns:
		--------
		object of class AlfrescoFire containing attributes calculated over the raster
		and potentially the subdomains in that area of interest.

		'''
		self.alf_ds = alf_ds
		self.veg_groups = veg_groups
		self.fire_counts = self._unique_counts_domains( )
		self.all_fire_sizes = self._all_fire_sizes( )
		self.avg_fire_size = self._avg_fire_size( )
		self.number_of_fires = self._number_of_fires( )
		self.total_area_burned = self._total_area_burned( )

		# read in the veg lag-1 data:
		self.veg = self.alf_ds.veglag.read( 1 )

		# multiply 
		self.prod_arr = (self.alf_ds.raster_arr > 0).astype(np.int16) * self.veg
		self.counts_df = pd.DataFrame( dict( zip( *np.unique( self.prod_arr, return_counts=True ) ) ) )

	def _total_area_burned( self, *args, **kwargs ):
		return { i:np.sum( self.fire_counts[ i ].values() ) for i in self.fire_counts.keys() }
	def _all_fire_sizes( self, *args, **kwargs ):
		return { i:self.fire_counts[ i ].values() for i in self.fire_counts.keys() }
	def _avg_fire_size( self, *args, **kwargs ):
		return { i:( np.round( np.average( self.all_fire_sizes[ i ]), decimals=2 ) \
					if len(self.all_fire_sizes[ i ]) > 0 else 0 ) for i in self.all_fire_sizes }
	def _number_of_fires( self, *args, **kwargs ):
		return { i:len( self.fire_counts[ i ].values() ) for i in self.fire_counts.keys() }
	def _total_area_burned( self, *args, **kwargs ):
		return { i:np.sum( self.fire_counts[ i ].values() ) for i in self.fire_counts.keys() }
	def _unique_counts_domains( self ):
		veg = rasterio.open( self.veg )
		vegtypes = np.unique( (veg < 255) & (veg > 0) ) #veg
		domains = self.alf_ds.sub_domains.sub_domains
		domains = [ (np.unique( domain[domain > 0] )[0], domain) for domain in domains ]
		raster_arr = self.alf_ds.raster_arr
		# we need to loop through vegtypes here and return by subdomain
		# dimensions: rep:year:metric for each vegtype and subdomain
		return { self.alf_ds.sub_domains.names_dict[domain_num]:\
					dict( zip( *np.unique( raster_arr[ (domain == domain_num) & (raster_arr > 0) ], return_counts=True ) ) ) \
					for domain_num, domain in domains } # changed (raster_arr > 0) from (raster_arr >= 0)  WATCH IT!


class BurnSeverity( object ):
	'''
	[ experimental ]
	calculate BurnSeverity metrics from ALFRESCO Fire Dynamics Model 
	output rasters across subdomains if applicable.
	'''
	def __init__( self, alf_ds, **kwargs ):
		'''
		initialize BurnSeverity data and calculate metrics

		severity_counts = counts of unique burn severity levels in a given subdomain

		Arguments:
		----------
		alf_ds = (AlfrescoDataset) an object of type AlfrescoDataset which contains
				all needed attributes to run the fire metrics.

		returns:
		--------
		object of class AlfrescoFire containing attributes calculated over the raster
		and potentially the subdomains in that area of interest.

		'''
		self.alf_ds = alf_ds
		self.severity_counts = self._unique_counts_domains( )

	def _total_area_burned( self, *args, **kwargs ):
		return { i:np.sum( self.fire_counts[ i ].values() ) for i in self.fire_counts.keys() }
	def _unique_counts_domains( self ):
		domains = self.alf_ds.sub_domains.sub_domains
		domains = [ (np.unique( domain[domain > 0] )[0], domain) for domain in domains ]
		raster_arr = self.alf_ds.raster_arr
		return { self.alf_ds.sub_domains.names_dict[domain_num]:\
					dict( zip( *np.unique( raster_arr[ (domain == domain_num) & (raster_arr > 0) & (raster_arr != 255) ], return_counts=True ) ) ) \
					for domain_num, domain in domains } # changed (raster_arr > 0) from (raster_arr >= 0)  WATCH IT!

