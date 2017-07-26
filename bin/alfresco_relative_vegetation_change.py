#!/usr/bin/env python

# # calculate vegetation resilience counts through time
def get_rep_num( x ):
	'''return rep number from firescar filename'''
	base = os.path.basename( x )
	return base.split( '_' )[ 1 ]
def count_transitions( arr_list ):
	''' 
	takes list of numpy ndarrays of integers and returns the number of 
	shifts in values in the series. arr_list is expected to be in 
	chronological order.
	'''
	import numpy as np
	arr_list = np.array([ np.where( arr != 0, 1, 0 ) for arr in np.diff( np.array( arr_list ), axis=0 ) ])
	return np.sum( arr_list, axis=0 )
def open_raster( fn, band=1 ):
	''' remove mem leaks from stale file handles '''
	import rasterio
	with rasterio.open( fn ) as out:
		arr = out.read( band )
	return arr
def relative_veg_change( veg_list, ncpus=32 ):
	'''
	opens list of vegetation filenames into 2-d numpy
	ndarrays and counts the number of transitons in vegetation 
	occur by pixel through the series. 
	Arguments:
		veg_list:[list] list of paths to the vegetation output files
					from the ALFRESCO Fire Model. * expects filenames in 
					chronological order *
	Returns:
		2-D numpy.ndarray of transition counts across the list of 
		filenames passed.
	'''
	arr_list = mp_map( open_raster, veg_list, nproc=ncpus )
	return count_transitions( arr_list )
def main( args ):
	'''
	run relative flammability with the input args dict from argparse
	'''
	import numpy as np

	dirname, basename = os.path.split( ars.output_filename )
	if not os.path.exists( dirname ):
		os.makedirs( dirname )

	# list, sort, group by replicate
	veg_list = [ os.path.join( root, fn ) for root, subs, files in os.walk( args.maps_path ) for fn in files if 'Veg_' in fn and fn.endswith( '.tif' ) ]
	year_list = range( args.begin_year, args.end_year + 1 )
	veg_list = [ i for i in veg_list if int( os.path.basename( i ).split('_')[ len( os.path.basename( i ).split( '_' ) )-1 ].split( '.' )[0] ) in year_list ]
	veg_sorted = sorted( veg_list, key=lambda x: get_rep_num( x ) )
	veg_grouped = [ list( g ) for k, g in groupby( veg_sorted, key=lambda x: get_rep_num( x ) ) ]
	
	# calculate relative vegetation change -- parallel
	# final = mp_map( relative_veg_change, veg_grouped, nproc=int( args.ncpus ) )
	final = [ relative_veg_change( v, int(args.ncores) ) for v in veg_grouped ]
	final = np.sum( final, axis=0 ) / np.float( len(veg_list) )

	# set dtype to float32 and round it
	final = final.astype( np.float32 )
	final = np.around( final, 4 ) 

	# mask the data with the out-of-bounds of Veg --> 255
	with rasterio.open( veg_list[0] ) as rst:
		arr = rst.read(1)
		final[ arr == 255 ] = -9999

	# write it out
	meta = rasterio.open( veg_list[ 0 ] ).meta
	meta.update( compress='lzw', dtype=np.float32, crs={ 'init':'EPSG:3338' }, nodata=-9999 )
	# output_filename = os.path.join( args.output_path, 'alfresco_relative_vegetation_change_counts_' + args.model + '_' + args.scenario + '_' + str(args.begin_year) + '_' + str(args.end_year) + '.tif' )
	with rasterio.open( args.output_filename, 'w', **meta ) as out:
		out.write( final, 1 )
	return output_filename

if __name__ == '__main__':
	from itertools import groupby
	import glob, os, sys, re, rasterio
	from pathos.mp_map import mp_map
	import numpy as np
	import scipy as sp
	import argparse
	# # # TESTING
	# # input args
	# input_path = '/atlas_scratch/apbennett/IEM_AR5/CCSM4_rcp45'
	# output_path = '/atlas_scratch/malindgren/ALFRESCO_IEM_DERIVED_DEC2016'
	# scenario = 'rcp45'
	# model = 'CCSM4'
	# script_path = '/workspace/UA/malindgren/repos/alfresco-calibration/alfresco_postprocessing/bin/alfresco_relative_vegetation_change.py'

	# ncpus = 50
	# begin_year = 1901
	# end_year = 1999
	
	# class hold:
	# 	def __init__( self, input_path, output_path, scenario, model, script_path, ncpus, begin_year, end_year):
	# 		self.input_path = input_path
	# 		self.output_path = output_path
	# 		self.scenario = scenario
	# 		self.model = model
	# 		self.script_path = script_path
	# 		self.ncpus = ncpus
	# 		self.begin_year = begin_year
	# 		self.end_year = end_year
				
	# args = hold( input_path, output_path, scenario, model, script_path, ncpus, begin_year, end_year )
	# # # END TESTING
	
	# parser = argparse.ArgumentParser( description='program to calculate Relative Vegetation Change from ALFRESCO Veg outputs' )
	# parser.add_argument( '-p', '--input_path', action='store', dest='input_path', type=str, help='path to ALFRESCO output Maps directory' )
	# parser.add_argument( '-o', '--output_path', action='store', dest='output_path', type=str, help='path to output directory' )
	# parser.add_argument( '-m', '--model', action='store', dest='model', type=str, help='model name' )
	# parser.add_argument( '-s', '--scenario', action='store', dest='scenario', type=str, help='scenario' )
	# parser.add_argument( '-n', '--ncpus', action='store', dest='ncpus', type=int, help='number of cores to utilize' )
	# parser.add_argument( '-by', '--begin_year', action='store', dest='begin_year', type=int, help='beginning year in the range' )
	# parser.add_argument( '-ey', '--end_year', action='store', dest='end_year', type=int, help='ending year in the range' )
	
	parser = argparse.ArgumentParser( description='program to calculate Relative Flammability from ALFRESCO' )
	parser.add_argument( '-p', '--maps_path', action='store', dest='maps_path', type=str, help='path to ALFRESCO output Maps directory' )
	parser.add_argument( '-o', '--output_filename', action='store', dest='output_filename', type=str, help='path to output directory' )
	parser.add_argument( '-nc', '--ncores', action='store', dest='ncores', type=int, help='number of cores' )
	parser.add_argument( '-by', '--begin_year', action='store', dest='begin_year', type=int, help='beginning year in the range' )
	parser.add_argument( '-ey', '--end_year', action='store', dest='end_year', type=int, help='ending year in the range' )


	args = parser.parse_args()
	_ = main( args )


# if __name__ == '__main__':
# 	from itertools import groupby
# 	import glob, os, sys, re, rasterio, collections
# 	input_path = '/big_scratch/apbennett/Calibration/FinalCalib/b1_rerun/miroc3_2_medres.sresb1/Maps'
# 	scenario = 'sresb1' 
# 	model = 'miroc3_2_medres'
# 	ncpus = '32'
# 	begin_year = '1901'
# 	end_year = '2100'
# 	output_path = '/atlas_scratch/malindgren'
# 	os.system ( 'python alfresco_relative_vegetation_change.py -p ' + \
# 		input_path + ' -o ' + output_path + ' -m ' + model + ' -s ' + \
# 		scenario + ' -n ' + str( ncpus ) + ' -by ' + begin_year + ' -ey ' + end_year )


# # # example
# import os
# models = [ 'gfdl_cm2_1', 'miroc3_2_medres', 'ukmo_hadcm3' ] # 'cccma_cgcm3_1', 'mpi_echam5'
# scenarios = [ 'sresa1b', 'sresa2','sresb1' ]
# year_ranges = [ ('1900', '1999'), ('2000', '2099'), ('1900', '2100') ]
# ncpus = 20
# for model in models:
# 	print( 'MODEL : %s' % model )
# 	for scenario in scenarios:
# 		for year_range in year_ranges:
# 			print( '  SCENARIO : %s' % scenario )
# 			if scenario == 'sresb1': # b1_rerun
# 				input_path = os.path.join( '/big_scratch/apbennett/Calibration/FinalCalib/b1_rerun', model + '.' + scenario, 'Maps' )
# 			else:
# 				input_path = os.path.join( '/big_scratch/apbennett/Calibration/FinalCalib', model + '.' + scenario, 'Maps' )
# 			output_path = os.path.join( '/workspace/Shared/Tech_Projects/Alaska_IEM/project_data/ALFRESCO/post_processing_outputs/relative_vegetation_change_counts', year_range[0] + '_thru_' + year_range[1] )
# 			if not os.path.exists( output_path ):
# 				os.system( 'mkdir -p ' + output_path )
# 			os.system( 'python /big_scratch/malindgren/ALFRESCO_PostProcessing/alfresco-calibration/alfresco_relative_vegetation_change.py -p ' + input_path + ' -o ' + output_path + ' -m ' + model + ' -s ' + scenario + ' -n ' + str( ncpus ) + ' -by ' + year_range[0] + ' -ey ' + year_range[1] )
# 			# os.system( 'python /workspace/UA/malindgren/repos/alfresco-calibration/alfresco_relative_vegetation_change.py -p ' + input_path + ' -o ' + output_path + ' -m ' + model + ' -s ' + scenario + ' -n ' + str( ncpus ) + ' -by ' + year_range[0] + ' -ey ' + year_range[1] )

# # example clip the maps to the iem domain
# import os, glob, sys
# cutline_iem = '/workspace/Shared/Tech_Projects/Alaska_IEM/project_data/ALFRESCO/aiem_domain_fixed/AIEM_domain.shp'
# base_path = '/workspace/Shared/Tech_Projects/Alaska_IEM/project_data/ALFRESCO/post_processing_outputs/relative_vegetation_change_counts'
# models = [ 'cccma_cgcm3_1', 'mpi_echam5' ]
# time_slices = os.listdir( base_path )
# for model in models:
# 	for time_slice in time_slices:
# 		l = glob.glob( os.path.join( base_path, time_slice, '*' + model + '*.tif' ) )
# 		output_path = os.path.join( base_path, time_slice, 'iem' )
# 		if not os.path.exists( output_path ):
# 			os.system( 'mkdir -p ' + output_path )

# 		for in_rst in l:
# 			print 'clipping ' + in_rst
# 			out_rst = os.path.join( output_path, os.path.basename( in_rst ).replace( '.tif', '_iem.tif' ) )
# 			os.system( 'gdalwarp -overwrite -q -tr 1000 1000 -t_srs EPSG:3338 -co "COMPRESS=LZW" -cutline ' + cutline_iem + ' -crop_to_cutline -of GTiff ' + in_rst + ' ' + out_rst )

# # # mask it
# import os, glob, sys, rasterio
# cutline_iem = '/workspace/Shared/Tech_Projects/Alaska_IEM/project_data/ALFRESCO/aiem_domain_fixed/AIEM_domain.shp'
# base_path = '/workspace/Shared/Tech_Projects/Alaska_IEM/project_data/ALFRESCO/post_processing_outputs/relative_vegetation_change_counts'
# models = [ 'cccma_cgcm3_1', 'mpi_echam5' ]
# time_slices = [ i for i in os.listdir( base_path ) if '.' not in i ]
# mask = rasterio.open( '/workspace/Shared/Tech_Projects/Alaska_IEM/project_data/ALFRESCO/aiem_domain_fixed/AIEM_domain.tif' )
# mask_arr = mask.read_band( 1 )
# for model in models:
# 	for time_slice in time_slices:
# 		input_path = os.path.join( base_path, time_slice, 'iem' )
# 		output_path = input_path.replace( 'iem', 'iem_masked' )
	
# 		if not os.path.exists( output_path ):
# 			os.system( 'mkdir -p ' + output_path )
	
# 		l = glob.glob( os.path.join( input_path, '*_iem.tif' ) )
# 		for in_rst in l:
# 			print( 'masking %s' % os.path.basename( in_rst ) )
# 			rst = rasterio.open( in_rst )
# 			arr = rst.read_band( 1 )
# 			meta = rst.meta
# 			meta.update( compress='lzw', nodata=255 )
# 			arr[ mask_arr < 1 ] = 255

# 			masked = np.ma.masked_where( mask_arr < 1, arr )
# 			output_filename = in_rst.replace( 'iem', 'iem_masked' )

# 			with rasterio.open( output_filename, 'w', **meta ) as out:
# 				out.write_band( 1, masked )
