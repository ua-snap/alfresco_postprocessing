# threshold table of counts greater or less than a given threshold fire size (pixels)
# TO RUN THIS BE SURE TO HAVE THE NEEDED PACAKGES tinydb, numpy, pandas
#  `pip install numpy tinydb pandas`

def get_all_fire_sizes( dat ):
	return [ rec['all_fire_sizes'] for rec in dat ]

def _update_cols( df, repnum ):
	columns = [x+'_rep{}'.format( str(repnum) ) for x in df.columns]
	df.columns = columns
	return df

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
	from collections import defaultdict
	
	# open the TinyDB output and make a list of the records
	dat = TinyDB( fn ).all()
	if 'year' in dat[0].keys():
		year_var = 'year'
	else:
		year_var = 'fire_year'
	
	years = [ int(rec[ year_var ]) for rec in dat ]	
	replicates = [ int(rec[ 'replicate' ]) for rec in dat ]
	midx = pd.MultiIndex.from_tuples( list( zip( replicates, years ) ) )
	
	# get all fire sizes from the json list...  --> TinyDB extracted
	afs = get_all_fire_sizes( dat )

	domains = afs[0].keys()
	dd = {}
	for domain in domains:
		below = []
		above = []
		for rec in afs:
			below = below + [np.where( np.array(rec[ domain ]) < threshold )[0].shape[0]]
			above = above + [np.where( np.array(rec[ domain ]) > threshold )[0].shape[0]]
		
		# make a dataframe for the domain
		columns = ['below_{}_{}'.format( threshold, domain ), 'above_{}_{}'.format( threshold, domain ) ]
		df = pd.DataFrame(list(zip( below, above )), columns=columns, index=midx )
		panel = df.to_panel() # make it wide-format
		# concat replicates to single DataFrame
		domain_df = pd.concat([ _update_cols( panel[ :, repnum, : ], repnum ) for repnum in np.unique( replicates ) ], axis=1 )
		dd[ domain ] = domain_df
	return dd

if __name__ == '__main__':
	import os
	import argparse

	parser = argparse.ArgumentParser( description='calculate number of fires with sizes above and below a given integer threshold. output as CSV(s)' )
	parser.add_argument( '-output_path', '--output_path', action='store', dest='output_path', type=str, help='path to output directory to dump csvs' )
	parser.add_argument( '-fn', '--fn', action='store', dest='fn', type=str, help='path to alfresco_postprocessing generated summary JSON' )
	parser.add_argument( '-t', '--threshold', action='store', dest='threshold', const=4, type=int, help='threshold value in number of pixels' )
	args = parser.parse_args()
	
	# unpack the args... this is tedious but easier
	fn = args.fn
	output_path = args.output_path
	threshold = args.threshold
	
	# run it
	df_dict = count_fire_sizes_annual( fn, threshold=threshold )

	# output to csv files
	for domain, df in df_dict.items():
		# if you want to write it out to a CSV, do something like this
		output_filename = os.path.join( output_path, 'annual_firesize_counts_threshold{}_{}.csv'.format(threshold, domain) )
		df.to_csv( output_filename, sep=',' )


# # TEST IT WITHOUT CLI
# fn = '/atlas_scratch/apbennett/IEM_AR5/CCSM4_rcp45/post/JSON/ALF_CCSM4_rcp45.json'
# output_path = '/atlas_scratch/malindgren/TEST_WINSLOW'
# threshold = 4
# # END TEST