# * * * * * * * * * * * * * * * * * * * * * * * * * * *
# ALFRESCO POST-PROCESSING EXAMPLE 
# * * * * * * * * * * * * * * * * * * * * * * * * * * *

import alfresco_postprocessing as ap
import os
import numpy as np

# # input args
ncores = 64
historical_maps_path = '/Data/Base_Data/ALFRESCO/AK_CAN_ALF_fires_geotiffs/files'
subdomains_fn = '/workspace/Shared/Tech_Projects/ALF_JFSP/project_data/shapefiles/combined_boreal_firemgmtzones_alfpp.shp'
id_field = 'OBJECTID'
name_field = 'Name'
metrics = [ 'veg_counts','avg_fire_size','number_of_fires','all_fire_sizes','total_area_burned','severity_counts' ]
base_path = '/big_scratch/shiny/Runs_Statewide/paul.duffy@neptuneinc.org'
base_path2 = '/atlas_scratch/apbennett/JFSP'
out_path = '/workspace/Shared/Tech_Projects/ALF_JFSP/project_data/ALFRESCO_PostProcessing/FireManagementZones' # this is the base out dir
treatment_groups = ['cru_tx0','gcm_tx0','gcm_tx1','gcm_tx2']

log = []
for group in treatment_groups:
	treatment = group.split('_')[-1]
	print('running treatment group: {}'.format(group))

	if treatment == 'tx2':
		alf_runs = os.listdir(os.path.join(base_path2, treatment))
	else:
		alf_runs = os.listdir(os.path.join(base_path, group))
	
	for run_name in alf_runs:
		print('	postprocessing alfresco group: {}'.format(run_name))
		treatment_name,scenario,model = run_name.split('_')

		if treatment == 'tx2':
			maps_path = os.path.join(base_path2, treatment, run_name, 'Maps')
		else:
			maps_path = os.path.join(base_path, group, run_name, 'Maps')

		output_path = os.path.join(out_path, group, run_name)
		suffix = run_name # some id for the output csvs

		# print out the treatment and maps_paths to be sure it is right:
		print('treatment:{}\nmaps_path:{}\nshapefile:{}\noutput_path:{}\n\n '.format(treatment, maps_path, subdomains_fn,output_path))
		log.append('treatment:{}\nmaps_path:{}\nshapefile:{}\noutput_path:{}\n\n '.format(treatment, maps_path, subdomains_fn,output_path))

		if not os.path.exists( output_path ):
			_ = os.makedirs( output_path )

		# json_names
		mod_json_fn = os.path.join( output_path, 'ALF.json' )
		obs_json_fn = os.path.join( output_path, 'OBS.json' )

		# # PostProcess
		# alfresco output gtiffs
		pp = ap.run_postprocessing( maps_path, mod_json_fn, ncores, ap.veg_name_dict, subdomains_fn, id_field, name_field )

		# historical fire input gtiffs
		# pp_hist = ap.run_postprocessing_historical( historical_maps_path, obs_json_fn, ncores, ap.veg_name_dict, \
		# 											subdomains_fn, id_field, name_field)

		pp_hist = ap.run_postprocessing_historical(maps_path=historical_maps_path, out_json_fn=obs_json_fn, ncores=ncores, 
													subdomains_fn=subdomains_fn, id_field=id_field, name_field=name_field,
													id_name_dict=ap.veg_name_dict)
		# # CSVs
		# modeled
		out = ap.to_csvs( pp, metrics, output_path, suffix, observed=False )
		pp.close() # close the database

		# historical
		historical_metrics = [ 'avg_fire_size','number_of_fires','all_fire_sizes','total_area_burned' ]
		out = ap.to_csvs( pp_hist, historical_metrics, output_path, suffix, observed=True )
		pp_hist.close()

		# * * * * * * * * PLOTTING * * * * * * * * * * * * * * * * * * * * * * * * * *

		# build plot objects for comparison plots
		modplot = ap.Plot( mod_json_fn, model=run_name, scenario=scenario )
		obsplot = ap.Plot( obs_json_fn, model='historical', scenario='observed' )
		
		# [NEW]
		obs_fire_years = obsplot.fire_years
		mod_fire_years = modplot.fire_years
		fire_years = np.concatenate([obs_fire_years,mod_fire_years]).astype(int)
		begin_range, end_range = fire_years.min(), fire_years.max()
		# [end NEW]

		# annual area burned barplot
		replicate = 0
		if scenario == 'historical':
			# ap.aab_barplot_factory( modplot, obsplot, output_path, replicate, year_range=(1950, 2010) )
			ap.aab_barplot_factory( modplot, obsplot, output_path, replicate, year_range=(1950, 2010) )

		# veg counts lineplots
		ap.vegcounts_lineplot_factory( modplot, output_path, replicate, year_range=(1950, end_range))

		# annual area burned lineplots
		ap.aab_lineplot_factory( modplot, obsplot, output_path, replicates=None, year_range=(1950, end_range) )

# write log to a logfile for transparency:
with open(os.path.join(out_path, 'logfile_postprocessing.txt'), 'w') as f:
	f.writelines(log)

