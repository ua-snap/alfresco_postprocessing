# * * * * * * * * * * * * * * * * * * * * * * * * * * *
# ALFRESCO POST-PROCESSING EXAMPLE 
# * * * * * * * * * * * * * * * * * * * * * * * * * * *

import alfresco_postprocessing as ap
from tinydb import TinyDB, Query

# # input args
ncores = 32
maps_path = './Maps'
historical_maps_path = './Fire' # Data Drive
output_path = './'
mod_json_fn = os.path.join( output_path, 'ALF_TEST.json' )
obs_json_fn = os.path.join( output_path, 'OBS_TEST.json' )
subdomains_fn = './AOI_SERDP.shp'
id_field = 'OBJECTID_1'
name_field = 'Name'
suffix = 'GISS-E2-R_rcp85_NoFMO' # some id for the output csvs
metrics = [ 'veg_counts','avg_fire_size','number_of_fires','all_fire_sizes','total_area_burned' ]

# # PostProcess
# alfresco output gtiffs
pp = ap.run_postprocessing( maps_path, mod_json_fn, ncores, ap.veg_name_dict, \
														subdomains_fn, id_field, name_field )

# historical fire input gtiffs
pp_hist = ap.run_postprocessing_historical( historical_maps_path, obs_json_fn, ncores, \
											ap.veg_name_dict, subdomains_fn, id_field, name_field)

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
modplot = Plot( mod_json_fn, output_path, model='GISS-E2-R', scenario='rcp85' )
obsplot = Plot( obs_json_fn, output_path, model='historical', scenario='observed' )

# annual area burned barplot
_ = aab_barplot_factory( modplot, obsplot, output_path, replicate, year_range )
aab_barplot_factory( modplot, obsplot, output_path, replicate, year_range=(1950, 2010) )

