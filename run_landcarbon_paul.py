# * * * * * * * * * * * * * * * * * * * * * * * * * * *
# ALFRESCO POST-PROCESSING EXAMPLE -- SNAP
# * * * * * * * * * * * * * * * * * * * * * * * * * * *

import alfresco_postprocessing as ap
from tinydb import TinyDB, Query
import os
import itertools

# # input args
base_path = '/atlas_scratch/apbennett/IEM/FinalCalib'
ncores = 32
models = ['cccma_cgcm3_1', 'mpi_echam5']
scenarios = ['sresa1b', 'sresa2', 'sresb1']
maps_paths = [ os.path.join( base_path, '.'.join([m,s]), 'Maps' ) \
					for m,s in itertools.product( models, scenarios ) ]

# maps_path = '/atlas_scratch/apbennett/IEM/FinalCalib/cccma_cgcm3_1.sresa1b/Maps'
historical_maps_path = '/Data/Base_Data/ALFRESCO_formatted/ALFRESCO_Master_Dataset/ALFRESCO_Model_Input_Datasets/AK_CAN_Inputs/Fire'
subdomains_fn = '/workspace/Shared/Tech_Projects/AK_LandCarbon/project_data/extent_shapefiles/ak_3338.shp'
id_field = 'FIPS'
name_field = 'NAME'
output_base_path = '/atlas_scratch/malindgren/ak_landcarbon_duffy'

for model, scenario in itertools.product( models, scenarios ):
	print( '_'.join([model, scenario]) )
	output_path = os.path.join( output_base_path, '_'.join([model,scenario]) )
	if not os.path.exists( output_path ):
		os.makedirs( output_path )
	maps_path = os.path.join( base_path, '.'.join([model,scenario]), 'Maps' )
	mod_json_fn = os.path.join( output_path, 'ALF_PP_'+'.'.join([model,scenario])+'.json' )
	obs_json_fn = os.path.join( output_path, 'OBS_PP_'+'.'.join([model,scenario])+'.json' )
	suffix = '_'.join([model,scenario,'landcarbon_ak']) # some id for the output csvs --needs changing
	metrics = [ 'veg_counts','avg_fire_size','number_of_fires','all_fire_sizes','total_area_burned' ]

	# # PostProcess
	# alfresco output gtiffs
	pp = ap.run_postprocessing( maps_path, mod_json_fn, ncores, ap.veg_name_dict, subdomains_fn, id_field, name_field )

	# historical fire input gtiffs
	# pp_hist = ap.run_postprocessing_historical( historical_maps_path, obs_json_fn, ncores, ap.veg_name_dict, subdomains_fn, id_field, name_field)

	# # CSVs
	# modeled
	out = ap.to_csvs( pp, metrics, output_path, suffix, observed=False )
	pp.close() # close the database

	# historical
	metrics = [ 'avg_fire_size','number_of_fires','all_fire_sizes','total_area_burned' ]
	out = ap.to_csvs( pp_hist, metrics, output_path, suffix, observed=True )
	pp_hist.close()

# * * * * * * * * experimental * * * * * * * * * * * * * * * * * * * * * * * * * *
# # Plot
# build a plot object
modplot = ap.Plot( mod_json_fn, model='GISS-E2-R', scenario='rcp85' )
obsplot = ap.Plot( obs_json_fn, model='historical', scenario='observed' )

# annual area burned barplot
_ = aab_barplot_factory( modplot, obsplot, output_path, replicate, year_range )
aab_barplot_factory( modplot, obsplot, output_path, replicate, year_range=(1950, 2010) )



# # # PAUL PLOT: 

def aab_barplot( modeled_rep, observed, output_path, domain, replicate, model, scenario, year_range, *args, **kwargs ):
	'''
	Plot Annual Area Burned Barplot for a single moeled replicate output and the 
	historical observed rasterized fire perimeter data used as input to the ALFRESCO
	Fire Dynamics Model.  These inputs should be pre-massaged into the formats stated by 
	the arguments below to ensure that the plots are returned as expected.

	Arguments:
	----------
	modeled_rep = [pandas.Series] where the index is years and the data represent a single
					representative replicate to be compared to the historical observed record
					for the same temporal period.
	observed = [pandas.Series] where the index is years and the data represent total area burned 
					for each timestep, to be compared to the modeled representative replicate for 
					the same temporal period.
	output_path = [str] path to output directory
	domain = [str] name of the domain -- for plot title 
	replicate = [str] number of the replicate -- for the plot title
	model = [str] model name -- for the plot title
	scenario = [str] scenario name -- for the plot title
	year_range = [tuple of int] 2 element tuple like ( begin_year, end_year ) default: (1950:2010)

	Returns:
	--------
	the path to the plot that was just written to disk with the side-effect of a plot being written to disk.

	'''
	# order of imports is important here if using 'Agg'
	import matplotlib, os
	matplotlib.use('Agg')
	from matplotlib import pyplot as plt
	import seaborn as sns

	# combine modeled and historical
	df = pd.concat( [observed, modeled_rep], axis=1 )
	sns.set_style( 'whitegrid', {'ytick.major.size': 7, 'xtick.major.size': 7} )
	my_colors = [ 'black', 'firebrick' ]
	
	plot_title = 'ALFRESCO Annual Area Burned 1950-2010 \n %s - %s\n %s - Replicate %s' \
			% ( model, scenario, domain, replicate )
	
	figsize = ( 11, 8 )
	barwidth = 0.7
	x_tick_rotation = 0

	ax = df.plot( kind='bar', width=barwidth, colors=my_colors, title=plot_title, figsize=figsize, rot=x_tick_rotation )
	ax.grid()

	# set the ticks to a better number of them
	n = 10 # every n ticks... from the existing set of all
	ticks = ax.xaxis.get_ticklocs()
	ticklabels = [ l.get_text() for l in ax.xaxis.get_ticklabels() ]
	ax.xaxis.set_ticks( ticks[::n] )
	ax.xaxis.set_ticklabels( ticklabels[::n] )
	ax.set_xlabel( 'year' )
	# ax.set_ylabel( 'Area Burned (' + '$\mathregular{km^2}$' + ')' )
	ax.set_ylabel( 'Area Burned (ha)' )
	sns.despine( )

	begin, end = year_range
	domain = domain.replace(' ', '')
	output_filename = os.path.join( output_path, '_'.join([ 'alfresco_annual_areaburned_bar', model, \
											scenario, domain.replace(' ', ''), str(begin), str(end) ]) + '.png' )
	plt.savefig( output_filename )
	plt.close()

# out = {}
# for root, subs, files in os.walk( '/atlas_scratch/malindgren/ak_landcarbon_duffy/' ):
# 	if len( files ) > 0:
# 		for fn in files:
# 			if 'alfresco_totalareaburned_Alaska_' in fn:
# 				out[  ] = fn

# IEM Best Replicate: 171
obs = pd.read_csv( '/atlas_scratch/malindgren/ak_landcarbon_duffy/Fire_Acreage_Thoman.csv', index_col=0 )
# its in acres, so lets convert to hectares? or is it in Hectares? -- ask Angie
obs_ha = obs.Acreage * 0.404686
obs_ha = obs_ha.ix[ 1950:2010 ]
obs_ha.name = 'observed'

for model in models:
	for scenario in scenarios:
		fn = os.path.join('/atlas_scratch/malindgren/ak_landcarbon_duffy', '_'.join([model,scenario]), 'total_area_burned', 'alfresco_totalareaburned_Alaska_'+'_'.join([model,scenario])+ '_landcarbon_ak_1900_2100.csv' )
		mod = pd.read_csv( fn, index_col=0 )
		mod_rep = mod[ 'rep_171' ]
		# convert to hectares from sq. km.
		mod_ha = mod_rep * 100
		mod_ha = mod_ha.ix[ 1950:2010 ]
		mod_ha.name = 'modeled'

		# plot that
		domain = 'Alaska'
		replicate = '171'
		year_range = (1950, 2010)
		aab_barplot( mod_ha, obs_ha, output_path, domain, replicate, model, scenario, year_range )

#Duffy plot issues:
# title ok
# km2 --> hA ok

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
# test DIRECTORIES and junk.  temporary.
# maps_path = '/atlas_scratch/apbennett/IEM/FinalCalib/cccma_cgcm3_1.sresa1b/Maps'
# maps_path = '/atlas_scratch/malindgren/sort_maps_path/cccma_cgcm3_1.sresa1b/Maps'
#'/workspace/Shared/Users/jschroder/ALFRESCO_SERDP/Data/Domains/newfmo.shp' 
# '/atlas_scratch/malindgren/test_stuff/raster_subdomains_test.tif' 
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 