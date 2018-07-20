#!/usr/bin/env python

# # # # # # # # # # # # # 
# calculate the areas changed from forest to tundra between 2 alfresco output veg maps from 2 points in time
# # # # # # # # # # # # # 

def hex_to_rgb( hex ):
	'''
	borrowed and modified from Matthew Kramer's blog:
		http://codingsimplicity.com/2012/08/08/python-hex-code-to-rgb-value/
	function to take a hex value and convert it into an RGB(A) representation.
	This is useful for generating color tables for a rasterio GTiff from a QGIS 
	style file (qml).  Currently tested for the QGIS 2.0+ style version.
	arguments:
		hex = hex code as a string
	returns:
		a tuple of (r,g,b,a), where the alpha (a) is ALWAYS 1.  This may need
		additional work in the future, but is good for the current purpose.
		** we need to figure out how to calculate that alpha value correctly.
	'''
	hex = hex.lstrip( '#' )
	hlen = len( hex )
	rgb = [ int( hex[ i : i + hlen/3 ], 16 ) for i in range( 0, hlen, hlen/3 ) ]
	rgb.insert( len( rgb ) + 1, 1 )
	return rgb
def qml_to_ctable( qml ):
	'''
	take a QGIS style file (.qml) and converts it into a 
	rasterio-style GTiff color table for passing into a file.
	arguments:
		qml = path to a QGIS style file with .qml extension
	returns:
		dict of id as key and rgba as the values
	'''
	import xml.etree.cElementTree as ET
	tree = ET.ElementTree( file=qml  )
	return { int( i.get( 'value' ) ) : tuple( hex_to_rgb( i.get( 'color' ) ) ) for i in tree.iter( tag='item' ) }
def get_treeline_expansion( t1_arr, t2_arr, mask_arr=None, forest_values = [1,2,3] ):
	'''
	return the map displaying pixels that have converted 
	from a tundra class to a forest class between the 2 
	timesteps.

	aggregation_values are a dict with keys 1 (forest) and 2 (tundra),
		where they each have values of lists of integers that should be 
		aggegated to these super-classes.  The default is based on the 
		standard ALF Vegetation map classes.

	returns:
		ndarray (raster) with values for:
		255. out-of-bounds
		1. static tundra class
		2. static forest class
		3. shift tundra -> forest class
	'''
	out_arr = np.zeros_like( t1_arr )
	t1_mod = np.zeros_like( t1_arr )
	t2_mod = np.zeros_like( t2_arr )

	# basal area estimates for same period:

	for value in forest_values:
		t1_mod[ t1_arr == value ] = 1
		t2_mod[ t2_arr == value ] = 1
	
	out_arr[ (t1_mod == 1) ] = 1
	out_arr[ (t1_mod != 1) & (t2_mod == 1) ] = 2
	out_arr = np.ma.masked_array( out_arr, t1_arr.mask, copy=True )
	return out_arr


def get_treeline_expansion( t1_arr, t2_arr, mask_arr=None, forest_values = [1,2,3] ):
	'''
	return the map displaying pixels that have converted 
	from a tundra class to a forest class between the 2 
	timesteps.

	aggregation_values are a dict with keys 1 (forest) and 2 (tundra),
		where they each have values of lists of integers that should be 
		aggegated to these super-classes.  The default is based on the 
		standard ALF Vegetation map classes.

	returns:
		ndarray (raster) with values for:
		1. t1 forest extent
		2. t2 forest expanded
		255. out-of-bounds
	'''
	out_arr = np.zeros_like( t1_arr )
	t1_mod = np.zeros_like( t1_arr )
	t2_mod = np.zeros_like( t2_arr )

	for value in forest_values:
		t1_mod[ t1_arr == value ] = 1
		t2_mod[ t2_arr == value ] = 1
	
	out_arr[ (t1_mod == 1) ] = 1
	out_arr[ (t1_mod != 1) & (t2_mod == 1) ] = 2
	out_arr = np.ma.masked_array( out_arr, t1_arr.mask, copy=True )
	return out_arr

def get_basal_area_estimate( basal_area_arr, treeline_expand_arr, mask_arr=None ):
	out_arr = np.zeros_like( treeline_expand_arr, dtype=np.float32 )
	out_arr[ : ] = basal_area_arr[ : ]
	out_arr[ (treeline_expand_arr == 1) & (treeline_expand_arr == 2) ] = np.max( out_arr )
	return out_arr

if __name__ == '__main__':
	import os, glob, rasterio
	import numpy as np
	import pandas as pd

	input_path = '/big_scratch/apbennett/Calibration/FinalCalib/cccma_cgcm3_1.sresa1b/Maps'
	output_path = '/workspace/Shared/Tech_Projects/Alaska_IEM/project_data/ALFRESCO/post_processing_outputs/treeline_expansion'
	t1_fn = 'Veg_171_2014.tif'
	t2_fn = 'Veg_171_2100.tif'

	t1 = rasterio.open( os.path.join( input_path, t1_fn) )
	t2 = rasterio.open( os.path.join( input_path, t2_fn) )
	t1_arr = t1.read_band( 1 )
	t2_arr = t2.read_band( 1 )

	cmap = {0:(182, 185, 191, 1),
			1:(95, 135, 36, 1),
			2:(72, 55, 87, 1),
			255:(0,0,0,1)}

	meta = t1.meta
	meta.update( compress='lzw', nodata=255, crs={'init':'epsg:3338'} )

	output_filename = os.path.join( output_path, '_'.join([ 'alfresco_treeline_shift3', t1_fn[:-4], t2_fn[:-4]]) + '.tif' )

	with rasterio.open( output_filename, 'w', **meta ) as out:
		out.write_band( 1, get_treeline_expansion( t1_arr, t2_arr ).filled() )
		out.write_colormap( 1, cmap )

	# basal area
	# # this one is ridiculous as there is not a good way to display what we want to here in a raw GTiff.
	# #  what is a better move is an output of the above treeline expansion raster with all forest as boolean
	# #  regardless expansion and then overlay the basal area on top of it with some classification on the data.
	# # 	>> this is a visualization issue not a data issue and should be treated as such. (make output png composition?)
	treeline_expand_arr = rasterio.open( out.name ).read_band( 1 )
	basal_name = t2_fn.replace( 'Veg', 'BasalArea' ) 
	basal_area = rasterio.open( os.path.join( input_path, basal_name ) )
	basal_area_arr = basal_area.read_band( 1 )

	basal = get_basal_area_estimate( basal_area_arr, treeline_expand_arr )
	
	meta = basal_area.meta
	meta.update( compress='lzw', nodata=255, crs={'init':'epsg:3338'} )

	output_filename = os.path.join( output_path, '_'.join([ 'alfresco_treeline_basalarea', basal_name[:-4]]) + '.tif' )

	with rasterio.open( output_filename, 'w', **meta ) as out:
		out.write_band( 1, get_basal_area_estimate( basal_area_arr, treeline_expand_arr ).filled() )

	print( 'treeline expansion output raster %s :' % output_filename )

# # # TESTING AREA
# maybe something like this for the matplotlib output of the data we need? or do we say
# forget the visualization stuff and the user can overlay it themselves?
# from matplotlib import pyplot as plt
# forest_img = rasterio.open(  )
# forest_arr = forest_img.read_band( 1 )
# trans = forest_arr.transform
# extent = (trans[0], trans[0] + gtif.RasterXSize*trans[1],
#           trans[3] + gtif.RasterYSize*trans[5], trans[3])

# plt.imshow(forest_arr.transpose((1, 2, 0)), extent=extent)
# plt.show()
