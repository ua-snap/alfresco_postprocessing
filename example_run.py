# * * * * * * * * * * * * * * * * * * * * * * * * * * *
# ALFRESCO POST-PROCESSING EXAMPLE 
# * * * * * * * * * * * * * * * * * * * * * * * * * * *

import alfresco_postprocessing as ap
import os

# # input args
ncores = 32
maps_path = './Maps' # alfresco output maps dir
historical_maps_path = './FireHistory'
subdomains_fn = './Domains/AOI_SERDP.shp'
id_field = 'OBJECTID_1'
name_field = 'Name'
output_path = './ALFRESCO_PP'
mod_json_fn = os.path.join( output_path, 'ALF.json' )
obs_json_fn = os.path.join( output_path, 'OBS.json' )
suffix = 'ModelName_scenario' # some id for the output csvs
metrics = [ 'veg_counts','avg_fire_size','number_of_fires','all_fire_sizes','total_area_burned' ]

# # PostProcess
# alfresco output gtiffs
pp = ap.run_postprocessing( maps_path, mod_json_fn, ncores, ap.veg_name_dict, subdomains_fn, id_field, name_field )

# historical fire input gtiffs
pp_hist = ap.run_postprocessing_historical( historical_maps_path, obs_json_fn, ncores, ap.veg_name_dict, subdomains_fn, id_field, name_field)

# # CSVs
# modeled
out = ap.to_csvs( pp, metrics, output_path, suffix, observed=False )
pp.close() # close the database

# historical
metrics = [ 'avg_fire_size','number_of_fires','all_fire_sizes','total_area_burned' ]
out = ap.to_csvs( pp_hist, metrics, output_path, suffix, observed=True )
pp_hist.close()

# * * * * * * * * PLOTTING * * * * * * * * * * * * * * * * * * * * * * * * * *

# build plot objects for comparison plots
modplot = ap.Plot( mod_json_fn, model='GISS-E2-R', scenario='rcp85' )
obsplot = ap.Plot( obs_json_fn, model='historical', scenario='observed' )

# annual area burned barplot
replicate = 0
ap.aab_barplot_factory( modplot, obsplot, output_path, replicate, year_range=(1950, 2010) )

# veg counts lineplots
ap.vegcounts_lineplot_factory( modplot, output_path, replicate, year_range=(1950, 2100))

# annual area burned lineplots
ap.aab_lineplot_factory( modplot, obsplot, output_path, model, scenario, replicates=[None], year_range=(1950, 2100) )
