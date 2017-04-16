# * * * * * * * * * * * * * * * * * * * * * * * * * * *
# ALFRESCO POST-PROCESSING EXAMPLE -- SNAP
# * * * * * * * * * * * * * * * * * * * * * * * * * * *
import alfresco_postprocessing as ap
import os

# # input args
ncores = 32
maps_path = '/atlas_scratch/apbennett/Calibration/HighCalib/FMO_Calibrated/GISS-E2-R_rcp85_NoFMO/Maps'
historical_maps_path = '/Data/Base_Data/ALFRESCO/ALFRESCO_Master_Dataset/ALFRESCO_Model_Input_Datasets/AK_CAN_Inputs/Fire'
subdomains_fn = '/workspace/Shared/Users/jschroder/ALFRESCO_SERDP/Data/Domains/AOI_SERDP.shp'
id_field = 'OBJECTID_1'
name_field = 'Name'
output_path = '/atlas_scratch/malindgren/TEST_WINSLOW'
mod_json_fn = os.path.join( output_path, 'ALF_TEST.json' )
obs_json_fn = os.path.join( output_path, 'OBS_TEST.json' )
suffix = 'GISS-E2-R_rcp85_NoFMO' # some id for the output csvs
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

# * * * * * * * * experimental * * * * * * * * * * * * * * * * * * * * * * * * * *
# # Plot
# build a plot object
modplot = ap.Plot( mod_json_fn, model='GISS-E2-R', scenario='rcp85' )
obsplot = ap.Plot( obs_json_fn, model='historical', scenario='observed' )

# annual area burned barplot
replicate = 0
ap.aab_barplot_factory( modplot, obsplot, output_path, replicate, year_range=(1950, 2010) )

# veg counts lineplots
ap.vegcounts_lineplot_factory( modplot, output_path, replicate, year_range=(1950, 2100))

# annual area burned lineplots
ap.aab_lineplot_factory( modplot, obsplot, output_path, model, scenario, replicates=[None], year_range=(1950, 2100) )


# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
# test DIRECTORIES and junk.  temporary.
# maps_path = '/atlas_scratch/apbennett/IEM/FinalCalib/cccma_cgcm3_1.sresa1b/Maps'
# maps_path = '/atlas_scratch/malindgren/sort_maps_path/cccma_cgcm3_1.sresa1b/Maps'
#'/workspace/Shared/Users/jschroder/ALFRESCO_SERDP/Data/Domains/newfmo.shp' 
# '/atlas_scratch/malindgren/test_stuff/raster_subdomains_test.tif' 
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
