import matplotlib
matplotlib.use( 'Agg' )
import pandas as pd
import numpy as np
import alfresco_postprocessing as ap
import seaborn as sns

class Plot( object ):
	'''
	class for storing data attributes and methods to abstract some of the
	ugliness of plotting the ALFRESCO Post Processing outputs.
	'''
	def __init__( self, json_fn, model, scenario, *args, **kwargs ):
		'''
		Arguments:
		----------
		json_fn = [str] path to the alfresco_postprocessing output TinyDB JSON database file
		model = [str] name of the model being processed (used in naming)
		scenario = [str] name of the scenario being processed (used in naming)

		Returns:
		--------
		object of type alfresco_postprocessing.Plot
				
		'''
		from tinydb import TinyDB
		self.json_fn = json_fn
		self.db = TinyDB( self.json_fn )
		self.records = self.db.all()
		self.model = model
		self.scenario = scenario
		self.fire_years = self._get_fire_years()

		if 'av_year' in self.records[0].keys():
			self.av_years = self._get_av_years()
		
		self.replicates = self._get_replicates()
		self.domains = self._get_domains()

	def _get_fire_years( self ):
		years = np.unique( [ rec['fire_year'] for rec in self.records ] ).astype( np.int )
		years.sort()
		return years.astype( str )
	def _get_av_years( self ):
		years = np.unique( [ rec['av_year'] for rec in self.records ] ).astype( np.int )
		years.sort()
		return years.astype( str )
	def _get_replicates( self ):
		replicates = np.unique( [ rec['replicate'] for rec in self.records ] )
		replicates.sort()
		return replicates
	def _get_domains( self ):
		record = self.records[0]
		metric = record.keys()[0]
		return record[ metric ].keys()
	def get_metric_dataframes( self, metric_name ):
		'''
		output a dict of pandas.DataFrame objects representing the 
		data of type metric_name in key:value pairs of 
		domainname:corresponding_DataFrame

		Arguments:
		----------
		metric_name = [str] metric name to be converted to pandas DataFrame obj(s).

		Returns:
		--------
		dict of pandas DataFrame objects from the output alfresco TinyDB json file
		for the desired metric_name
		'''
		from collections import defaultdict
		metric_select = ap.get_metric_json( self.db, metric_name )
		panel = pd.Panel( metric_select )

		dd = defaultdict( lambda: defaultdict( lambda: defaultdict ) )
		for domain in self.domains:
			if metric_name != 'veg_counts': # fire
				dd[ domain ] = panel[ :, domain, : ]

			if metric_name == 'veg_counts': # veg
				df = panel[ :, domain, : ]
				vegtypes = sorted( df.ix[0,0].keys() )
				new_panel = pd.Panel( df.to_dict() )
				for vegtype in vegtypes:
					# subset the data again into vegetation types
					dd[ domain ][ vegtype ] = new_panel[ :, vegtype, : ]
		return dd

def best_rep( modplot, obsplot, domain, method='spearman' ):
	'''
	calculate correlation between replicates and historical to find which one most
	highly correlates with the observed data series for the same timestep and temoral period.

	Arguments:
	----------
	modplot = [ alfresco_postprocessing.Plot ] modeled data input JSON records file
	obsplot = [ alfresco_postprocessing.Plot ] observed data input JSON records file
	domain = [ str ] the Name of the domain to use in determining the 'best' replicate
	method = [str] one of 'pearson', 'kendall', 'spearman'

	Returns:
	--------
	dict with the best replicate number as the key and the correlation value as the value/\.

	'''
	mod_tab_dict = modplot.get_metric_dataframes( 'total_area_burned' )
	mod_df = mod_tab_dict[ domain ]
	obs_tab_dict = obsplot.get_metric_dataframes( 'total_area_burned' )
	obs = obs_tab_dict[ domain ][ 'observed' ]
	years = obs.index
	mod_df = mod_df.ix[ years, : ]
	corr = pd.Series({i:mod_df[i].corr( obs, method=method ) for i in mod_df.columns })
	ind, = np.where( corr == corr.reset_index()[0].max() )
	return  corr[ ind ].to_dict()

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
	import os
	from matplotlib import pyplot as plt
	# import seaborn as sns

	# combine modeled and historical
	df = pd.concat( [observed, modeled_rep], axis=1 )
	sns.set_style( 'whitegrid', {'ytick.major.size': 7, 'xtick.major.size': 7} )
	my_colors = [ 'black', 'firebrick' ]
	
	plot_title = 'ALFRESCO Annual Area Burned 1950-2010 \n %s - Replicate %s' \
			% ( domain, replicate )
	
	figsize = ( 11, 8 )
	barwidth = 0.7
	x_tick_rotation = 0

	ax = df.plot( kind='bar', width=barwidth, color=my_colors, title=plot_title, figsize=figsize, rot=x_tick_rotation )
	ax.grid()

	# set the ticks to a better number of them
	n = 10 # every n ticks... from the existing set of all
	ticks = ax.xaxis.get_ticklocs()
	ticklabels = [ l.get_text() for l in ax.xaxis.get_ticklabels() ]
	ax.xaxis.set_ticks( ticks[::n] )
	ax.xaxis.set_ticklabels( ticklabels[::n] )
	ax.set_xlabel( 'year' )
	ax.set_ylabel( 'Area Burned (' + '$\mathregular{km^2}$' + ')' )
	sns.despine( )

	begin, end = year_range
	domain = domain.replace(' ', '')
	output_filename = os.path.join( output_path, '_'.join([ 'alfresco_annual_areaburned_bar', 'observed', \
											scenario, domain.replace(' ', ''), str(begin), str(end) ]) + '.png' )
	plt.savefig( output_filename )
	plt.close()
	return output_filename

def aab_barplot_factory( modplot, obsplot, output_path, replicate, year_range=(1950, 2010), *args, **kwargs ):
	'''
	function to build the needed output barplots
	'''
	# maybe pass this in the right way without the DB's?
	mod_dict = modplot.get_metric_dataframes( 'total_area_burned' )
	obs_dict = obsplot.get_metric_dataframes( 'total_area_burned' )
	begin, end = year_range
	years = [ str(i) for i in range( begin, end+1 ) ]

	for domain in modplot.domains: # using modeled domains, must be same in obs_dict
		mod = mod_dict[ domain ].loc[ years, str(replicate) ]
		mod.name = 'modeled'
		obs = obs_dict[ domain ].loc[ years, 'observed' ]
		_ = ap.aab_barplot( mod, obs, output_path, domain, replicate, modplot.model, modplot.scenario, year_range, *args, **kwargs )
	return 'success!'

def vegcounts_lineplot( modeled, output_path, domain, model, scenario, vegtype, replicate, year_range, *args, **kwargs ):
	'''
	CONSIDERED UNDER DEVELOPMENT!

	function to build the needed output line plots depicting the vegetation counts 
	through time for each of the vegetation types.  This plot shows the "BEST" rep 
	in dark red, along with all other reps in light grey to give the user an idea of
	the spread of the data and where that best replicate lies in that mix.

	'''
	# order of imports is important here if using 'Agg'
	import os
	from matplotlib import pyplot as plt
	# import seaborn as sns
	import matplotlib.pyplot as plt
	import matplotlib.patches as mpatches

	# set style
	sns.set_style( 'whitegrid', {'ytick.major.size': 7, 'xtick.major.size': 7} )
	# setup -- should become overloaded args for control in the future
	figsize = (11, 8)
	begin, end = year_range
	years = [ str(i) for i in range(begin, end+1) ]
	df = modeled.loc[ years, : ] # this could morph into something that will handle df without row labels

	# plot the lines
	# plot_title = 'ALFRESCO Vegetation Annual Area Counts %s-%s \n %s \n %s ' % (str(begin), str(end), vegtype, domain.replace( '_', ' ' ) )
	plot_title = "ALFRESCO Vegetation Annual %s Coverage Area %s-%s \n %s \n %s" \
			% ( vegtype, str(begin), str(end), model.upper().replace( '_', ' ' ) \
			+ ' - ' + scenario.upper(), domain.replace( '_', ' ' ) )

	df.plot( title=plot_title, legend=False, color=['0.75'], figsize = figsize, grid=False )

	# add the mean across replicates line
	df_mean = df.apply( np.mean, axis=1 )
	df_mean.plot( color='black', legend=False, figsize = figsize, grid=False )

	# build a legend
	blk_patch = mpatches.Patch( color='black', label='Mean Across Replicates' )
	grey_patch = mpatches.Patch( color='0.75', label='All Replicates' )
	handles = [ blk_patch, grey_patch ]

	if replicate:
		df.loc[ :,str(replicate) ].plot( color='firebrick', legend=False, figsize = figsize, grid=False )
		label = 'replicate %s' % replicate
		red_patch = mpatches.Patch( color='firebrick', label=label )
		handles.append( red_patch )
	
	plt.legend( handles=handles, frameon=False )

	# axis labels
	plt.xlabel( 'year' )
	plt.ylabel( 'Area ' + vegtype + ' Cover ('+'$\mathregular{km^2}$' + ')' )

	# final prep and write it out
	sns.despine()
	output_filename = os.path.join( output_path, '_'.join([ 'alfresco_annual_areaveg_line', \
			model, scenario, vegtype.replace(' ', '' ), domain.replace(' ', '' ), str(begin), str(end) ]) + '.png' ) 
	plt.savefig( output_filename )
	plt.close()

def vegcounts_lineplot_factory( modplot, output_path, replicate=None, year_range=(1950, 2100), *args, **kwargs ):
	'''
	function to build the needed output barplots
	'''
	# maybe pass this in the right way without the DB's?
	metric = 'veg_counts'
	mod_dict = modplot.get_metric_dataframes( metric )
	begin, end = year_range
	years = [ str(i) for i in range( begin, end+1 ) ]

	for domain in modplot.domains: # using modeled domains, must be same in obs_dict
		vegtypes = mod_dict[ domain ].keys()
		for vegtype in vegtypes:
			mod = mod_dict[ domain ][ vegtype ].loc[ years, : ] #str(replicate)
			mod.name = 'modeled'
			_ = vegcounts_lineplot( mod, output_path, domain, modplot.model, modplot.scenario, vegtype, replicate, year_range )
	return 'success!'

def aab_lineplot( modeled, observed, output_path, domain, model, scenario, replicates, year_range ):
	'''
	CONSIDERED UNDER DEVELOPMENT AND NON-WORKING!
	function to build the needed output plot for the cumulative area burned calibration plot
	'''
	# order of imports is important here if using 'Agg'
	import os
	from matplotlib import pyplot as plt
	# import seaborn as sns
	import matplotlib.pyplot as plt
	import matplotlib.patches as mpatches

	# setup -- should become overloaded args for control in the future
	figsize = (11, 8)
	begin, end = year_range
	years = [ str(i) for i in range(begin, end+1) ]
	
	# prep data
	mod_df = modeled.loc[ years, : ] # this could morph into something that will handle df without row labels
	mod_df_mean = mod_df.apply( np.mean, axis=1 )
	obs = observed.loc[ str(begin): ]

	# build plot
	sns.set_style( 'whitegrid', {'ytick.major.size': 7, 'xtick.major.size': 7} )
	ss = sns.axes_style()
	ss[ 'axes.grid' ] = False
	ss[ 'grid.color' ] = 'white'

	with ss:
		plot_title = 'ALFRESCO Annual Area Burned %d-%d \n %s \n %s' \
				% ( begin, end, model.upper().replace( '_', ' ' ) + ' - ' + scenario.upper(), domain )

		ax = mod_df.plot( legend=False, color=['0.75'], title=plot_title, figsize=figsize, grid=False )
		mod_df_mean.plot( legend=False, color='black', figsize=figsize, grid=False, ax=ax )
		obs.plot( legend=False, color='firebrick', figsize=figsize, grid=False, ax=ax )

		# axis labels
		plt.xlabel( 'year' )
		plt.ylabel( 'Area Burned ('+'$\mathregular{km^2}$'+')' )

		# build and display legend
		red_patch = mpatches.Patch( color='firebrick', label='Historical' )
		blk_patch = mpatches.Patch( color='black', label='Mean Across Replicates' )
		grey_patch = mpatches.Patch( color='0.75', label='All Replicates' )
		handles = [ red_patch, blk_patch, grey_patch ]

		# need to deal with representative replicates ?!?!
		# if replicates[0] != None:
		# 	mod_tab_best_bor = mod_tab_all[ '_'.join([ 'rep', str( best_rep_num_bor ) ])]
		# 	mod_tab_best_tun = mod_tab_all[ '_'.join([ 'rep', str( best_rep_num_tun ) ])]
		# 	mod_tab_best_bor.plot( legend=False, color='darkgreen', figsize=figsize )
		# 	mod_tab_best_tun.plot( legend=False, color='darkblue', figsize=figsize )
		# 	grn_patch = mpatches.Patch( color='darkgreen', label='Best Boreal Replicate' )
		# 	blu_patch = mpatches.Patch( color='darkblue', label='Best Tundra Replicate' )
		# 	_ = [ handles.append( i ) for i in [grn_patch, blu_patch] ]
		# 	plot_title = 'ALFRESCO Annual Area Burned %d-%d \n %s "Best" Boreal Replicate: %d \n "Best" Tundra Replicate: %d \n \
		#					Domain Number: %s' % ( begin, end, model + ' ' + scenario, best_rep_num_bor, best_rep_num_tun, domain )
		
		plt.legend( handles=handles, frameon=False, loc=2 )
		sns.despine()
		output_filename = os.path.join( output_path, '_'.join([ 'alfresco_annual_areaburned_line', model, scenario, domain.replace(' ', ''), str(begin), str(end) ]) + '.png' )
		plt.savefig( output_filename )
		plt.close()
	return 'success!'
	
def aab_lineplot_factory( modplot, obsplot, output_path, replicates=None, year_range=(1950,2100) ):
	# modeled, observed, output_path, domain, model, scenario, replicates=[None], year_range=(1950,2100)
	'''
	function to build the needed output barplots
	'''
	# maybe pass this in the right way without the DB's?
	metric = 'total_area_burned'
	mod_dict = modplot.get_metric_dataframes( metric )
	obs_dict = obsplot.get_metric_dataframes( metric )
	print(year_range)
	begin, end = year_range
	years = [ str(i) for i in range( begin, end+1 ) ]

	for domain in modplot.domains: # using modeled domains, must be same in obs_dict
		mod = mod_dict[ domain ].loc[ years, : ]
		mod.name = 'modeled'
		obs = obs_dict[ domain ].loc[ years ]
		_ = aab_lineplot( mod, obs, output_path, domain, modplot.model, modplot.scenario, replicates, year_range )
	return 'success!'

def cab_lineplot( modeled, observed, output_path, domain, model, scenario, replicates=[None], year_range=(1950,2100), *args, **kwargs ):
	'''
	function to build the needed output plot for the cumulative area burned calibration plot
	'''
	# order of imports is important here if using 'Agg'
	import os
	from matplotlib import pyplot as plt
	# import seaborn as sns
	import matplotlib.pyplot as plt
	import matplotlib.patches as mpatches

	# setup -- should become overloaded args for control in the future
	figsize = (11, 8)
	begin, end = year_range
	years = [ str(i) for i in range(begin, end+1) ]
	
	# prep data
	mod_df = modeled.loc[ years, : ] # this could morph into something that will handle df without row labels
	mod_df = mod_df.apply( np.cumsum, axis=0 )
	mod_df_mean = mod_df.apply( np.mean, axis=1 )
	obs = observed.loc[ str(begin): ]
	obs = obs.apply( np.cumsum )

	# build plot
	sns.set_style( 'whitegrid', {'ytick.major.size': 7, 'xtick.major.size': 7} )
	my_colors = [ 'black', 'DarkRed' ]

	plot_title = 'ALFRESCO Cumulative Sum of Annual Area Burned %d-%d \n %s \n %s' \
		% ( begin, end, model.upper().replace( '_', ' ' ) + ' - ' + scenario.upper(), domain )

	mod_df.plot( legend=False, color=['0.75'], title=plot_title, figsize=figsize, grid=False )
	mod_df_mean.plot( legend=False, color='black', figsize=figsize, grid=False )
	obs.plot( legend=False, color='indianred', grid=False )
	
	# axis labels
	plt.xlabel( 'year' )
	plt.ylabel( 'Area Burned ('+'$\mathregular{km^2}$' + ')' )

	# build and display legend
	red_patch = mpatches.Patch( color='indianred', label='Historical' )
	blk_patch = mpatches.Patch( color='black', label='Mean Across Replicates' )
	grey_patch = mpatches.Patch( color='0.75', label='All Replicates' )
	handles = [ red_patch, blk_patch, grey_patch ]

	# if replicates[0] != None:
	# 	mod_tab_best_bor.plot( legend=False, color='darkgreen', figsize=figsize )
	# 	mod_tab_best_tun.plot( legend=False, color='darkblue', figsize=figsize )
	# 	grn_patch = mpatches.Patch( color='darkgreen', label='Best Boreal Replicate' )
	# 	blu_patch = mpatches.Patch( color='darkblue', label='Best Tundra Replicate' )
	# 	plot_title = 'ALFRESCO Cumulative Area Burned %d-%d \n %s "Best" Boreal Replicate: %d \n "Best" Tundra Replicate: %d \n Domain Number: %s' \
	# 						% ( begin, end, model + ' ' + scenario, best_rep_num_bor, best_rep_num_tun, domain )

	plt.legend( handles=handles, frameon=False, loc=2 )
	# final prep and write it out
	sns.despine()
	output_filename = os.path.join( output_path, '_'.join([ 'alfresco_cumsum_areaburned_line', model, scenario, domain.replace(' ', ''), str(begin), str(end) ]) + '.png' )
	plt.savefig( output_filename )
	plt.close()
	return 'success!'

def cab_lineplot_factory( modplot, obsplot, output_path, model, scenario, replicates=[None], year_range=(1950, 2100), *args, **kwargs ):
	'''
	function to build the needed output barplots
	'''
	# maybe pass this in the right way without the DB's?
	metric = 'total_area_burned'
	mod_dict = modplot.get_metric_dataframes( metric )
	obs_dict = obsplot.get_metric_dataframes( metric )
	begin, end = year_range
	years = [ str(i) for i in range( begin, end+1 ) ]

	for domain in modplot.domains: # using modeled domains, must be same in obs_dict
		mod = mod_dict[ domain ].loc[ years, : ]
		mod.name = 'modeled'
		obs = obs_dict[ domain ].loc[ years ]
		_ = cab_lineplot( mod, obs, output_path, domain, model, scenario, replicates, year_range )
	return 'success!'

def cab_vs_fs_lineplot( modeled, observed, output_path, domain, model, scenario, replicates=[None], year_range=(1950,2100), *args, **kwargs ):
	'''
	UNDER DEVELOPMENT AND NON-WORKING
	'''
	# order of imports is important here if using 'Agg' backend
	import matplotlib, os
	matplotlib.use('Agg')
	from matplotlib import pyplot as plt
	# import seaborn as sns
	import matplotlib.pyplot as plt
	import matplotlib.patches as mpatches

	# setup -- should become overloaded args for control in the future
	figsize = (11, 8)
	begin, end = year_range
	years = [ str(i) for i in range(begin, end+1) ]

	# # prep data 
	# modeled
	df_list = []
	for col in modeled.columns:
		mod_sorted = sorted( [ j for i in  modeled[ col ] for j in i ] )
		mod_cumsum = np.cumsum( mod_sorted )
		replicate = [ col for i in range( len( mod_sorted ) ) ]
		df_list.append( pd.DataFrame( {'mod_sorted':mod_sorted, 'mod_cumsum':mod_cumsum, 'replicate':replicate} ) )

	# melt the ragged arrays with a concat -- dirty way
	mod_melted = pd.concat( df_list )

	# observed
	obs_sorted = sorted([ j for i in observed.iloc[:,0] for j in i ])
	obs_cumsum = np.cumsum( obs_sorted )
	obs_df = pd.DataFrame({ 'obs_sorted':obs_sorted, 'obs_cumsum':obs_cumsum })

	# # plot
	sns.set_style( 'white', {'ytick.major.size': 7, 'xtick.major.size': 7} )
	sns.set( rc={'figure.figsize':figsize} )

	# plt.plot( best_rep_bor['fires'], best_rep_bor['cumsum'], sns.xkcd_rgb['dark blue'] )
	# plt.plot( best_rep_tun['fires'], best_rep_tun['cumsum'], sns.xkcd_rgb['dark green'] )
	mod_melted.groupby( 'replicate' ).apply( lambda x: plt.plot( x['mod_sorted'], x['mod_cumsum'], sns.xkcd_rgb['greyish'] ) )
	plt.plot( obs_df['obs_sorted'], obs_df['obs_cumsum'], sns.xkcd_rgb['indian red'] )

	# legend
	red_patch = mpatches.Patch( color=sns.xkcd_rgb['indian red'] , label='Historical' )
	grn_patch = mpatches.Patch( color=sns.xkcd_rgb['dark green'] , label='Best Boreal Replicate' )
	blu_patch = mpatches.Patch( color=sns.xkcd_rgb['dark blue'], label='Best Tundra Replicate' )
	grey_patch = mpatches.Patch( color=sns.xkcd_rgb['greyish'], label='All Replicates' )
	plt.legend( handles=[ red_patch, grn_patch, blu_patch, grey_patch ], frameon=False, loc=0 )

	# save
	sns.despine()
	output_filename = os.path.join( output_path, '_'.join([ 'alfresco_cab_vs_fs', model, scenario, domain, str(begin), str(end) ]) + '.png' )
	plt.savefig( output_filename )
	plt.close()

def cab_vs_fs_lineplot_factory( modplot, obsplot, output_path, model, scenario, replicates=[None], year_range=(1950, 2100), *args, **kwargs ):
	'''
	UNDER DEVELOPMENT AND NON-WORKING
	'''
	metric = 'all_fire_sizes'
	# maybe pass this in the right way without the DB's?
	mod_dict = modplot.get_metric_dataframes( metric )
	obs_dict = obsplot.get_metric_dataframes( metric )

	begin, end = year_range
	years = [ str(i) for i in range( begin, end+1 ) ]

	for domain in modplot.domains: # using modeled domains, must be same in obs_dict
		mod = mod_dict[ domain ].loc[ years, : ]
		obs = obs_dict[ domain ].loc[ str(begin): ]
		mod.name = 'modeled'
		obs.name = 'observed'
		_ = cab_vs_fs_lineplot( mod, obs, output_path, domain, model, scenario, replicates=[None], year_range=(1950,2100) )
	return 'success!'


# if __name__ == '__main__':
# 	# out_path
# 	output_path = '/atlas_scratch/malindgren/calib_experiment'
	
# 	# get some plot information:
# 	out_json_fn = '/atlas_scratch/malindgren/calib_experiment/OBS_TEST.json'
# 	obsplot = ap.Plot( out_json_fn, model='historical', scenario='observed' )
# 	out_json_fn = '/atlas_scratch/malindgren/calib_experiment/ALF_TEST.json'
# 	modplot = ap.Plot( out_json_fn, model='GISS-E2-R', scenario='rcp85' )

# 	_ = aab_barplot_factory( modplot, obsplot, output_path, replicate, year_range )
# 	aab_barplot_factory( modplot, obsplot, output_path, replicate, year_range=(1950, 2010) )


