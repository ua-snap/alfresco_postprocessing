# threshold table of counts greater or less than a given threshold fire size (pixels)
# TO RUN THIS BE SURE TO HAVE THE NEEDED PACAKGES tinydb, numpy, pandas
#  `pip install numpy tinydb pandas`

def get_all_fire_sizes( dat ):
	return [ rec['all_fire_sizes'] for rec in dat ]

def count_fire_sizes_annual( fn, threshold=4 ):
	''' 
	ARGUMENTS:
	----------
	fn = [str] path to the ALFRESCO Post Processing output JSON file
	threshold = [int] number of pixels	

	RETURNS:
	--------
	PANDAS DataFrame with columns [ 'count_below', 'count_above' ] and
	index of 'years'

	'''
	from tinydb import TinyDB
	import pandas as pd
	import numpy as np
	
	# open the TinyDB output and make a list of the records
	dat = TinyDB( fn ).all()
	if 'year' in dat[0].keys():
		year_var = 'year'
	else:
		year_var = 'fire_year'
	
	years = [ rec[ year_var ] for rec in dat ]	
	replicates = [ rec[ 'replicate' ] for rec in dat ]
	midx = pd.MultiIndex.from_tuples( list( zip( replicates, years ) ) )
	
	# get all fire sizes from the json list...  --> TinyDB extracted
	afs = get_all_fire_sizes( dat )

	domains = afs[0].keys()
	domains_outputs = []
	for domain in domains:
		below = []
		above = []
		for rec in afs:
			below = below + [np.where( np.array(rec[ domain ]) < threshold )[0].shape[0]]
			above = above + [np.where( np.array(rec[ domain ]) > threshold )[0].shape[0]]
		
		# make a dataframe for the domain
		columns = ['below_{}_{}'.format( threshold, domain ), 'above_{}_{}'.format( threshold, domain ) ]
		df = pd.DataFrame(list(zip( below, above )), columns=columns, index=midx )
		# NEW shit.
		dfs = df.unstack()
		above = dfs['above'].T
		below = dfs['above'].T
		# END NEW 
		
		domains_outputs = domains_outputs + [ df ]
	return pd.concat( domains_outputs )

if __name__ == '__main__':
	# modeled ALF outputs
	# fn = '/atlas_scratch/malindgren/TEST_WINSLOW/ALF_TEST.json'
	fn = '/atlas_scratch/apbennett/IEM_AR5/CCSM4_rcp45/post/JSON/ALF_CCSM4_rcp45.json'
	# observed ALF outputs
	# fn = '/atlas_scratch/malindgren/TEST_WINSLOW/OBS_TEST.json'
	df = count_fire_sizes_annual( fn, threshold=4 )

	# if you want to write it out to a CSV, do something like this
	output_filename = '/path/to/output_csv_file.csv'
	df.to_csv( output_filename, sep=',' )
