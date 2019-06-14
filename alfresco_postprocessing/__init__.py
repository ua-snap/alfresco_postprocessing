# * * * * * * * * * * * * * * * * * * * * * * * * * * *
# ALFRESCO POST-PROCESSING INITIALIZATION FILE
# * * * * * * * * * * * * * * * * * * * * * * * * * * *

# read in local libarary elements
from alfresco_postprocessing.dataset import *
from alfresco_postprocessing.metrics import *
from alfresco_postprocessing.postprocess import *
from alfresco_postprocessing.plot import *
import alfresco_postprocessing as ap

# other libs (external and stdlib)
import os, glob, rasterio, ujson
import numpy as np
from functools import partial


# # VEGETATION MAP DEFAULT:
veg_name_dict = {0: 'No Veg',
				1: 'Tundra',
				2: 'Black Spruce',
				3: 'White Spruce',
				4: 'Deciduous',
				5: 'Shrub Tundra',
				6: 'Graminoid Tundra',
				7: 'Wetland Tundra',
				8: 'Barren Lichen-Moss',
				9: 'Temperate Rainforest'}

# # UTILITY FUNCTIONS -- Run PostProcess
def	open( alf_fn, sub_domains=None, observed=False ):
	'''
	open an alfresco output/input dataset and give a subdomains object as arg2 if desired
	if data represents observed alfresco input FireHistory data, then set observed to 
	True (default: False)

	Arguments:
	----------
	alf_fn = [str] path to an ALFRESCO Fire Dynamics Model output (or sometimes input) raster.
	sub_domains = an object of one of three types for different scenarios. 
		typically this is created with read_subdomains
	observed = [bool] if alf_fn points to a FireHistory file then set observed=True.
		default:False (not observed, or ALFRESCO model output)

	Returns:
	--------
	object of type AlfrescoDataset or ObservedDataset depending on the input fn and 
	observed argument.

	'''
	switch = { False: AlfrescoDataset, True: ObservedDataset }
	return switch[ observed ](fn=alf_fn, sub_domains=sub_domains)

def read_subdomains( subdomains_fn=None, rasterio_raster=None, id_field=None, name_field=None, 
	id_name_dict=None, background_value=None ):
	'''
	handle different sub_domains use-cases.
	'''
	if subdomains_fn != None:
		if ( subdomains_fn.endswith('.shp') ):
			subs = SubDomains( subdomains_fn=subdomains_fn, rasterio_raster=rasterio_raster, \
							id_field=id_field, name_field=name_field )
		else:
			subs = SubDomainsRaster( subdomains_fn=subdomains_fn, rasterio_raster=rasterio_raster, \
							background_value=background_value, id_name_dict=id_name_dict )
	elif subdomains_fn == None:
		subs = FullDomain( rasterio_raster=rasterio_raster, background_value=None ) # hardwired at None for now
	else:
		AttributeError( 'subdomains_fn must be a valid shape filename, raster filename, or None' )
	return subs


# ACTUAL RUN STUFF
def _open_tinydb( out_json_fn ):
	'''
	open a tinydb database file (JSON) on disk at the 
	location input. This function will also remove the 
	database if it exists on disk.

	Arguments:
	----------
	out_json_fn = [str] path to the json file to be generated.

	Returns:
	--------
	tinydb.TinyDB object pointing to a JSON file at the location
	provided in out_json_fn.

	'''
	from tinydb import TinyDB
	if os.path.exists( out_json_fn ):
		os.unlink( out_json_fn )
	return TinyDB( out_json_fn )

def _run_historical( fn, sub_domains=None, *args, **kwargs ):
	'''
	a quick and dirty method of performing the historical observed
	burned boolean raster GTiffs used as inputs to the ALFRESCO Fire
	Dynamics Model.

	Arguments:
	----------
	fn = [str] path to FireHistory GTiff for a single year used as input
		to ALFRESCO.
	sub_domains = an object of one of three types for different scenarios. 
		typically this is created with read_subdomains

	Returns:
	--------
	dict with keys for each metric, replicate, and year with values that 
	are returned for each. Subdomains are contained nested within these 
	key:value pairs.

	'''
	ds_fs = ap.open( fn, sub_domains=sub_domains, observed=True )
	out_dd = {}
	fire = Fire( ds_fs )
	out_dd.update( replicate=ds_fs.replicate,
					fire_year=ds_fs.year,
					all_fire_sizes=fire.all_fire_sizes,
					avg_fire_size=fire.avg_fire_size,
					number_of_fires=fire.number_of_fires,
					total_area_burned=fire.total_area_burned )
	return out_dd

def _run_timestep( timestep, sub_domains, veg_name_dict, *args, **kwargs ):
	'''
	workhorse function that takes a dict of style {variable_name:path_to_file.tif}
	for all files in a single timestep that are to be used in calculation.

	This is where we would add new things to be added into the output JSON, like
	new classes for working with Age, Burn Severity, or interactions to name a 
	few.

	Arguments:
	----------
	timestep = [alfresco_postprocessing.TimeStep] timestep object with 
	timestep_fn_dict = [dict] dictionary that stores the filenames for all variables
		in a given timestep. In {variable_name:filename_string} pairs
	sub_domains = [alfresco_postprocessing.SubDomains] subdomains object as read using
		ap.read_subdomains( ) to return a common data type for all different flavors 
		of inputs used as subdomains.

	Returns:
	--------
	dict with keys for each metric, replicate, and year with values that are returned
	for each.  Subdomains are contained nested within these key:value pairs.

	'''
	# open the data we need -- add more reads here and then add in the
	# class instantiation with them below
	ds_fs = ap.open( timestep.FireScar.fn, sub_domains=sub_domains )
	ds_veg = ap.open( timestep.Veg.fn, sub_domains=sub_domains )
	# ds_age = ap.open( timestep.Age.fn, sub_domains=sub_domains )
	ds_burnseverity = ap.open( timestep.BurnSeverityHistory.fn, sub_domains=sub_domains )
	
	out_dd = {}
	# fire 
	fire = Fire( ds_fs )
	out_dd.update( replicate=ds_fs.replicate,
					fire_year=ds_fs.year,
					all_fire_sizes=fire.all_fire_sizes,
					avg_fire_size=fire.avg_fire_size,
					number_of_fires=fire.number_of_fires,
					total_area_burned=fire.total_area_burned )
	# veg
	veg = Veg( ds_veg, veg_name_dict )
	out_dd.update( av_year=ds_veg.year, veg_counts=veg.veg_counts )

	# age -- not yet implemented
	# age = Age()

	burnseverity = BurnSeverityHistory( ds_burnseverity )
	out_dd.update( severity_counts=burnseverity.severity_counts )
	return out_dd

def _get_stats( timesteps, db, sub_domains, ncores, veg_name_dict ):
	from tinydb import TinyDB
	import multiprocessing
	from functools import partial
	
	# instantiate a pool of workers
	pool = multiprocessing.Pool( processes=ncores, maxtasksperchild=4 )

	# run parallel map using multiprocessing 
	f = partial( _run_timestep, sub_domains=sub_domains, veg_name_dict=veg_name_dict )
	out = pool.map( f, timesteps )
	pool.close()
	db.insert_multiple( out )
	del out
	return db

def run_postprocessing_historical( maps_path, out_json_fn, ncores, subdomains_fn=None, id_field=None, name_field=None, background_value=0, id_name_dict=None ):
	import glob, os
	import multiprocessing
	file_list = glob.glob( os.path.join( maps_path, '*.tif' ) )
	db = _open_tinydb( out_json_fn )
	rst = rasterio.open( file_list[0] )
	sub_domains = read_subdomains( subdomains_fn=subdomains_fn, rasterio_raster=rst, id_field=id_field, name_field=name_field, background_value=0, id_name_dict=id_name_dict )

	pool = multiprocessing.Pool( processes=ncores, maxtasksperchild=4 )
	# run parallel map using multiprocessing 
	f = partial( _run_historical, sub_domains=sub_domains, id_name_dict=id_name_dict )
	out = pool.map( f, file_list )
	pool.close()
	db.insert_multiple( out )
	del out
	return db

# THIS FUNCTION NEEDS CHANGING SINCE WE NO LONGER USE THE NAME PostProcess, nor do we access the raster file in that same way.
# IT IS BETTER SUITED TO BEING PULLED FROM THE FIRST OF THE TimeStep objects.
def run_postprocessing( maps_path, out_json_fn, ncores, veg_name_dict, subdomains_fn=None, \
	id_field=None, name_field=None, background_value=0, lagfire=False, id_name_dict=None ): # background value is problematic
	db = ap._open_tinydb( out_json_fn )
	fl = FileLister( maps_path, lagfire=lagfire )
	# open a template raster
	rst = rasterio.open( fl.files[0] )
	sub_domains = read_subdomains( subdomains_fn=subdomains_fn, rasterio_raster=rst, \
					id_field=id_field, name_field=name_field, background_value=0, id_name_dict=id_name_dict )
	ts_list = fl.timesteps
	# fn_list = [ dict(i) for i in fn_list ]
	return _get_stats( ts_list, db, sub_domains, ncores, veg_name_dict ) # WATCH THIS!!!!!

def _to_csv( db, metric_name, output_path ):
		return metric_to_csvs( db, metric_name, output_path )

def to_csvs( db, metrics, output_path, suffix='', observed=False ):
	'''
	output a list of metrics to CSV files from an ALFRESCO Post Processing 
	derived TinyDB holding summary stats.

	Arguments:
	----------
	db = [tinydb.TinyDB] ALFRESCO Post Processing derived output summary stats database
		created following post processing of the outputs.
	metrics = [list] strings representing the metrics to be output to CSV from the 
		db. 
	output_path = [str] path to the output path to store the generated CSV files.
	suffix = [str] default:'' string identifier to put in the output filenames.
	observed = [bool] set to True if it is an observed dataset based TinyDB output,
		default: False for a standard output ALFRESCO Dataset based TinyDB output. 

	Returns:
	--------
	1 if succeeds.  with the side-effect of writing CSV files to disk.

	'''
	import os
	out = []
	# switch to deal with diff groups in a cleaner way.
	switch = { True:metric_to_csvs_historical, False:metric_to_csvs }
	for metric_name in metrics:
		out_path = os.path.join( output_path, metric_name.replace(' ', '' ) )
		if not os.path.exists( out_path ):
			os.makedirs( out_path )
		out.append( switch[observed]( db, metric_name, out_path, suffix ) )
	return output_path

