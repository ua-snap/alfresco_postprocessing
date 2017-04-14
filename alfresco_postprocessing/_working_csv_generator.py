# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Beginnings of the output CSV creator functionality.  
# this is currently working and is extremely fast, but requires
# more testing and tests built around it.
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
def get_metric_json( db, metric_name ):
	'''
	take an ALFRESCO Post Processing output TinyDB database
	and along with the name of a metric return a nested JSON
	structure (as dict) with 3 levels replicates:years:metric_values

	Arguments:
	----------

	db = [tinydb.TinyDB] open tinydb object from an ALFRESCO Post Processing run
	metric_name = [str] name of metric to extract and output to csv.
		supported types: 'veg_counts','avg_fire_size','number_of_fires',
						'all_fire_sizes','total_area_burned'

	Returns:
	--------
	dict object with structure replicates:years:metric_values.

	Notes:
	------
	This can be read into a PANDAS Panel object with pd.Panel( obj_name )
	and used in this data structure for groupby / apply / etc

	'''
	# get all the records from the TinyDB storage solution
	records = db.all()
	replicates = np.unique( [ rec['replicate'] for rec in records ] ).astype( np.int )
	replicates.sort()
	replicates = replicates.astype( str )

	# generate a nested dict (JSON) for a single metric
	metric_select = { replicate:{ record[ 'year' ] : record[ metric_name ] \
			for record in records if record[ 'replicate' ] == replicate } \
			for replicate in replicates  }
	return metric_select

def metric_to_csvs( db, metric_name, output_path ):
	'''
	output ALFRESCO Derived Summary Statistics to CSV files
	for ease-of-use with spreadsheet softwares.

	Arguments:
	----------

	db = [tinydb.TinyDB] open tinydb object from an ALFRESCO Post Processing run
	metric_name = [str] name of metric to extract and output to csv.
			supported types: 'veg_counts','avg_fire_size','number_of_fires',
							'all_fire_sizes','total_area_burned'
	output_path = [str] path to the folder where you want the output csvs to be 
							written to

	Returns:
	--------
	[str] output_path 

	'''
	# select the data we need from the TinyDB
	metric_select = get_metric_json( db, metric_name )
	years = metric_select[ replicates[0] ].keys()
	domains = metric_select[ replicates[0] ][ years[0] ].keys()

	# make a panel (replicates, domains, years)
	panel = pd.Panel( metric_select ) 
	startyear = min(years)
	endyear = max(years)

	for domain in domains:
		if metric_name != 'veg_counts': # fire
			output_filename = os.path.join( output_path, '_'.join([ 'alfresco', metric_name.replace('_',''), domain,\
												startyear, endyear ]) + '.csv' )
			panel[ :, domain, : ].to_csv( output_filename, sep=',' )

		if metric_name == 'veg_counts': # veg
			df = panel[ :, domain, : ]
			vegtypes = sorted( df.ix[0,0].keys() )
			new_panel = pd.Panel( df.to_dict() )
			for vegtype in vegtypes:
				# subset the data again into vegetation types
				output_filename = os.path.join( output_path, '_'.join([ 'alfresco', metric_name.replace('_',''),\
													domain, vegtype, startyear, endyear ]) + '.csv' )
				new_panel[ :, vegtype, : ].to_csv( output_filename, sep=',' )
	return 1


# get dicts of needed identifier names and id values -- HARDWIRED
shp = gpd.read_file( subdomains_path )
id_name = zip( shp.OBJECTID_1 , shp.Name )
# id_name.insert( 0, (0, u'IEM Domain') ) # add in the domain 0 or domain-wide (HACKY!!)
id_name_dict = OrderedDict( id_name ) # this needs to be a helper function to get this from another dataset 
# id_name_dict[ 3 ] ='Northwest Boreal LCC' # this updates the name for this LCC (HACKY!!!)

veg_name_dict = {1:'Black Spruce',
				2:'White Spruce',
				3:'Deciduous',
				4:'Shrub Tundra',
				5:'Graminoid Tundra',
				6:'Wetland Tundra',
				7:'Barren lichen-moss',
				8:'Temperate Rainforest'}



if __name__ == '__main__':
	from tinydb import TinyDB
	from tinydb.middlewares import CachingMiddleware
	from tinydb.storages import JSONStorage
	import ujson

	# args
	out_json_fn = '/atlas_scratch/malindgren/test_stuff/test_json_3_1.json'
	metrics = [ 'veg_counts','avg_fire_size','number_of_fires','all_fire_sizes','total_area_burned' ]
	output_path = '/atlas_scratch/malindgren/test_stuff'
	
	# read in the tinydb -- a simple data store
	db = TinyDB( out_json_fn, storage=CachingMiddleware(JSONStorage), cache_size=None )

	# output the JSON data to CSVs:
	out = [ metric_to_csvs( db, metric_name, output_path ) for metric_name in metrics ]

