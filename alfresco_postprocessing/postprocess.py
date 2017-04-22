# * * * * * * * * * * * * * * * * * * * * * * * * * * *
# ALFRESCO POST-PROCESSING RUN CLASSES
# * * * * * * * * * * * * * * * * * * * * * * * * * * *
import alfresco_postprocessing as ap
import pandas as pd
import numpy as np
import os

class FileLister( object ):
	'''
	return flavors of file lists
	'''
	def __init__( self, maps_path, lagfire=False, *args, **kwargs ):
		self.maps_path = maps_path
		self.files = self._list_files()
		self.files_df = self._prep_filelist()
		self._lagfire = lagfire
		self.df = self._to_df()
		self.timesteps = self._to_timestep()

	def _list_files( self ):
		'''
		new list files that can deal with the year sub-direcories 
		test change we are making to improve performance.
		'''
		import os
		files = [ os.path.join( root, i ) for root, subs, files in os.walk( self.maps_path ) \
				if len( files ) > 0 for i in files if i.endswith('.tif') ]
		return files
	def _prep_filelist( self ):
		'''
		convert listed files from `maps_path` to pandas.DataFrame object
		with the columns:
			* object: contains the result of alfresco_postprocessing.Filename 
					on each filename
			* year: year parsed from filename
			* replicate: replicate parsed from filename
			* variable: variable name parsed from filename
		
		Returns:
		--------
		pandas.DataFrame containing the Filename object and 
		related metadata attributes.
		'''
		files = [ Filename(i) for i in self.files ]
		df = pd.DataFrame([{'object':i,'year':i.year,'replicate':i.replicate, 'variable':i.variable} for i in files ])
		# sort by replicate and year
		df = df.sort_values(['replicate','year'], ascending=[1,1])
		return df
	def _to_df( self ):
		# convert to objects for easier parsing
		files = [ Filename( i ) for i in self.files ]
		# create an unpacked DataFrame with the file objects
		df = pd.DataFrame([{'object':i,'year':int(i.year),'replicate':int(i.replicate), 'variable':i.variable} for i in files ])
		# sort it
		df = df.sort_values(['variable','replicate','year'], ascending=[0,1,1])
		# make it into a dataframe wide-format
		df_wide = pd.DataFrame( { name:dat['object'].tolist() for name, dat in df.groupby( 'variable' ) } )
		# add in a MultiIndex that is useable
		index = pd.MultiIndex.from_tuples( df_wide.iloc[:, 0].apply( lambda x: (int(x.replicate), int(x.year) ) ) )
		df_wide.index = index
		variables = df_wide.columns		
		return df_wide
	def _lag_fire( self ):
		df = self.df
		firevars = [ 'FireScar','BurnSeverity' ]
		othervars = [ 'Age','Veg','BasalArea' ]
		replicates, years = df.index.levels
		fire = pd.concat( [ df[ v ].drop( years.min(), level=1 ) for v in firevars ], axis=1 )
		other = pd.concat( [ df[ v ].drop( years.max(), level=1 ) for v in othervars ], axis=1 )
		shifted = pd.concat( [fire.reset_index(drop=True), other.reset_index(drop=True)], axis=1 )
		# above the clean_df_wide is the straight-up and the shifted is the lagged
		# to get it into a format that is more useful for us lets do this:
		ts_list = [ TimeStep(i) for i in shifted.to_dict( orient='records' ) ]
		return ts_list
	def _nolag_fire( self ):
		df = self.df
		ts_list = [ TimeStep(i) for i in df.to_dict( orient='records' ) ]
		return ts_list
	def _to_timestep( self ):
		'''
		convert the files_df generated with `self._prep_filelist` to grouped
		alfresco_postprocessing.TimeStep objects.  These may be `lag`ged depending
		on lagfire boolean argument in `__init__`.  
		'''
		if self._lagfire == True:
			ts_list = self._lag_fire()
		elif self._lagfire == False:
			ts_list = self._nolag_fire()
		else:
			BaseException( 'lagfire must be boolean.' )
		return ts_list


class ObservedFileLister( FileLister ):
	def __init__( self, *args, **kwargs ):
		super( ObservedFileLister, self ).__init__( *args, **kwargs )
	
	def _prep_filelist( self ):
		'''
		convert listed files from `maps_path` to pandas.DataFrame object
		with the columns:
			* object: contains the result of alfresco_postprocessing.Filename 
					on each filename
			* year: year parsed from filename
			* variable: variable name parsed from filename
		
		Returns:
		--------
		pandas.DataFrame containing the Filename object and 
		related metadata attributes.
		'''
		files = [ ObservedFilename(i) for i in self.files ]
		df = pd.DataFrame([{'object':i,'year':i.year,'variable':i.variable} for i in files ])
		# sort by year
		df = df.sort_values(['year'], ascending=[1])
		return df
	def _to_df( self ):
		# convert to objects for easier parsing
		files = [ ObservedFilename( i ) for i in self.files ]
		# create an unpacked DataFrame with the file objects
		df = pd.DataFrame([{'object':i,'year':int(i.year), 'variable':i.variable} for i in files ])
		# sort it
		df = df.sort_values(['variable','year'], ascending=[0,1])
		# make it into a dataframe wide-format
		df_wide = pd.DataFrame( { name:dat['object'].tolist() for name, dat in df.groupby( 'variable' ) } )
		# add in a MultiIndex that is useable
		index = df_wide.iloc[:, 0].apply( lambda x: int(x.year) )
		df_wide.index = index
		variables = df_wide.columns
		return df_wide
	def _to_timestep( self ):
		'''
		convert the files_df generated with `self._prep_filelist` to grouped
		alfresco_postprocessing.TimeStep objects.  These may be `lag`ged depending
		on lagfire boolean argument in `__init__`.  
		'''
		if self._lagfire == True:
			ts_list = self._lag_fire()
		elif self._lagfire == False:
			ts_list = self._nolag_fire()
		else:
			BaseException( 'lagfire must be boolean.' )
		return ts_list

class Filename( object ):
	'''
	split filename into variable, year, replicate
	'''
	def __init__( self, fn ):
		self.fn = fn
		self.variable = None
		self.replicate = None
		self.year = None
		self._split()

	def _split( self, splitter='_' ):
		base, fn = os.path.split( self.fn )
		name, ext = os.path.splitext( fn )
		self.variable, self.replicate, self.year = name.split( splitter )

class ObservedFilename( object ):
	'''
	split filename into variable, year
	'''
	def __init__( self, fn ):
		self.fn = fn
		self.variable = None
		self.year = None
		self._split()

	def _split( self, splitter='_' ):
		base, fn = os.path.split( self.fn )
		name, ext = os.path.splitext( fn )
		self.variable = 'FireScar'
		self.year = name.split( splitter )[ -1 ]

# PYTHON2 VERSION
# class TimeStep( object ):
# 	def __init__( self, d ):
# 		'''
# 		convert dict of Filename objects in format:
# 		{ variable : <Filename>object }
# 		to a <TimeStep> object that is more easily query-able
# 		and contains more meta information about its inputs.
# 		'''
# 		self.__dict__ = d
# 		names = d.keys()
# 		# self.year = d[ names[0] ].year
# 		self.replicate = d[ names[0] ].replicate


# PYTHON3 VERSION
class TimeStep( object ):
	def __init__( self, d ):
		'''
		convert dict of Filename objects in format:
		{ variable : <Filename>object }
		to a <TimeStep> object that is more easily query-able
		and contains more meta information about its inputs.
		'''
		self.__dict__ = d.copy()
		names = list( d.keys() )
		# self.year = d[ names[0] ].year
		self.replicate = d[ names[0] ].replicate


# This class is currently not implemented and developing rapidly
class ObservedPostProcess( object ):
	'''
	run post-processing
	'''
	def __init__( self, maps_path, *args, **kwargs ):
		self.maps_path = maps_path
		self._list_files()
		
	def _list_files( self ):
		'''
		new list files that can deal with the year sub-direcories 
		test change we are making to improve performance.
		'''
		import os, glob
		self.file_list = glob.glob( os.path.join( self.maps_path, '*.tif' ) )

class TinyDBInsert:
	'''
	class for use in asyncronous parallel map
	of insertion of JSON record to TinyDB 
	'''
	def __init__( self, db ):
		'''
		take as input a path to an unused 
		output json location that you want to 
		instantiate and populate.
		'''
		import multiprocessing
		self.db = db
		self.lock = multiprocessing.Lock()
		self.count = 0

	def insert( self, record ):
		self.count += 1
		self.lock.acquire()
		self.db.insert( record )
		self.lock.release()

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
	import numpy as np
	# get all the records from the TinyDB storage solution
	records = db.all()
	replicates = np.unique( [ rec['replicate'] for rec in records ] )#.astype( np.int )
	# replicates.sort()
	# replicates = replicates.astype( str )

	# generate a nested dict (JSON) for a single metric
	metric_select = { replicate:{ record[ 'fire_year' ] : record[ metric_name ] \
			for record in records if record[ 'replicate' ] == replicate } \
			for replicate in replicates  }
	return metric_select

def metric_to_csvs_historical( db, metric_name, output_path, suffix=None ):
	'''
	output Historical Observed Fire Derived Summary Statistics to CSV files
	for ease-of-use with spreadsheet softwares.

	Arguments:
	----------

	db = [tinydb.TinyDB] open tinydb object from an ALFRESCO Post Processing run
	metric_name = [str] name of metric to extract and output to csv.
			supported types: 'avg_fire_size','number_of_fires',
							'all_fire_sizes','total_area_burned'
	output_path = [str] path to the folder where you want the output csvs to be 
							written to
	suffix = [str] underscore joined elements to identify output file groups

	Returns:
	--------
	[str] output_path 

	'''
	import pandas as pd
	import numpy as np
	import os

	metric_select = get_metric_json( db, metric_name )
	replicate = metric_select.keys()[0] # only one replicate (observed) for obs 
	years = metric_select[ replicate ].keys()
	startyear = str( min([ int(y) for y in years ]) )
	endyear =  str( max([ int(y) for y in years ]) )
	domains = metric_select[ replicate ][ years[0] ].keys()
	panel = pd.Panel( metric_select )

	for domain in domains:
		if suffix == None:
			output_filename = os.path.join( output_path, '_'.join([ 'firehistory', metric_name.replace('_',''), domain,\
												startyear, endyear ]) + '.csv' )
		else:
			output_filename = os.path.join( output_path, '_'.join([ 'firehistory', metric_name.replace('_',''), domain,\
												suffix, startyear, endyear ]) + '.csv' )

		panel_select = panel[ :, domain, : ]
		panel_select = panel_select.fillna( 0 ) # change NaNs to Zero
		panel_select.to_csv( output_filename, sep=',' )
	return 1

def metric_to_csvs( db, metric_name, output_path, suffix=None ):
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
	suffix = [str] underscore joined elements to identify output file groups

	Returns:
	--------
	[str] output_path 

	'''
	import pandas as pd
	import numpy as np
	import os
	# select the data we need from the TinyDB
	metric_select = get_metric_json( db, metric_name )
	replicates = metric_select.keys()
	column_order = np.array(replicates).astype( int )
	column_order.sort()
	column_order = column_order.astype( str )
	column_order_names = [ '_'.join(['rep',i]) for i in column_order ]
	years = metric_select[ replicates[0] ].keys()
	domains = metric_select[ replicates[0] ][ years[0] ].keys()

	# make a panel (replicates, domains, years)
	panel = pd.Panel( metric_select ) 
	startyear = min(years)
	endyear = max(years)

	for domain in domains:
		if metric_name not in ['veg_counts', 'severity_counts']: # firescar
			if suffix == None:
				output_filename = os.path.join( output_path, '_'.join([ 'alfresco', metric_name.replace('_',''), domain,\
													startyear, endyear ]) + '.csv' )
			else:
				output_filename = os.path.join( output_path, '_'.join([ 'alfresco', metric_name.replace('_',''), domain,\
													suffix, startyear, endyear ]) + '.csv' )

			panel_select = panel[ :, domain, : ]
			panel_select = panel_select[ column_order ]
			panel_select = panel_select.fillna( 0 ) # change NaNs to Zero
			panel_select.columns = column_order_names
			panel_select.to_csv( output_filename, sep=',' )

		elif metric_name == 'veg_counts': # veg
			df = panel[ :, domain, : ]
			vegtypes = sorted( df.ix[0,0].keys() )
			new_panel = pd.Panel( df.to_dict() )
			for vegtype in vegtypes:
				# subset the data again into vegetation types
				if suffix == None:
					output_filename = os.path.join( output_path, '_'.join([ 'alfresco', metric_name.replace('_',''),\
												domain, vegtype.replace(' ', ''), startyear, endyear ]) + '.csv' )
				else:
					output_filename = os.path.join( output_path, '_'.join([ 'alfresco', metric_name.replace('_',''),\
												domain, vegtype.replace(' ', ''), suffix, startyear, endyear ]) + '.csv' )

				# reorder the columns to 0-nreps !
				veg_df = new_panel[ :, vegtype, : ]
				veg_df = veg_df[ column_order ]
				veg_df.columns = column_order_names
				# deal with NaN's? !
				veg_df.fillna( 0 )
				veg_df.to_csv( output_filename, sep=',' )

		elif metric_name == 'severity_counts':
			burnseverity = { (rec[ 'replicate' ],rec[ 'fire_year' ]):pd.Series(rec[ 'severity_counts' ][ domain ]) for rec in db.all() }
			df = pd.concat( burnseverity ).astype( int ).unstack().fillna( 0 )
			if suffix == None:
				output_filename = os.path.join( output_path, '_'.join([ 'alfresco', metric_name.replace('_',''), domain,\
													startyear, endyear ]) + '.csv' )
			else:
				output_filename = os.path.join( output_path, '_'.join([ 'alfresco', metric_name.replace('_',''), domain,\
													suffix, startyear, endyear ]) + '.csv' )
			df.to_csv( output_filename, sep=',' )

	return 1


# RUN FOR NOW:
# maps_path = '/atlas_scratch/apbennett/Calibration/HighCalib/FMO_Calibrated/GISS-E2-R_rcp85_NoFMO/Maps'
# fl = FileLister( maps_path, lagfire=True )


