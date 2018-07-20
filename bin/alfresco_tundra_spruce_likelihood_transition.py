# 0. Load veg input map layer. (With use of veg input map, all years can be processed independently.)
# # special case --> consider after normal use-case is complete.

# 1. For a single year, load all reps' basal area maps and veg maps.

def prep_basalarea( ts, vegmap ):
	arr = rasterio.open( ts.fn ).read( 1 )
	# set to zero all data != Tundra ... classes 4/5/6...
	arr[ np.where((vegmap != 4) & (vegmap != 5) & (vegmap != 6)) ] = 0
	return arr

def prep_veg( ts, vegmap ):
	arr = rasterio.open( ts.fn ).read( 1 )
	# set to zero all data != Tundra ... classes 4/5/6...
	arr[ np.where((arr != 4) & (arr != 5) & (arr != 6)) ] = 0
	arr[ arr > 0 ] = 1
	return arr

def basal_across_reps( group, vegmap, output_path ):
	import numpy as np
	import rasterio, os

	group_id, group = group

	basal_ts_list = group[ group['variable']=='BasalArea' ].object.tolist()
	veg_ts_list = group[ group['variable']=='Veg' ].object.tolist()

	# we may need to maintain the year information here...
	prepped_basal = [ prep_basalarea( ts, vegmap ) for ts in basal_ts_list ]
	prepped_veg = [ prep_veg( ts, vegmap ) for ts in veg_ts_list ]

	del basal_ts_list, veg_ts_list

	processed = []
	for basal, veg in zip( prepped_basal, prepped_veg ):
		out_arr = np.zeros_like( basal )
		out_arr[ np.where( (veg == 1) & (basal > 0) ) ] = basal[ np.where( (veg == 1) & (basal > 0) ) ]
		processed = processed + [ out_arr ]

	del prepped_veg, prepped_basal
	basalavg = np.mean( processed, axis=0 )

	del processed

	with rasterio.open( ts.fn ) as rst:
		meta = rst.meta
	
	del rst

	if 'transform' in meta.keys():
		meta.pop( 'transform' )

	meta.update( compress='lzw', count=1, crs={'init':'epsg:3338'}, dtype='float32', nodata=-9999 )

	output_filename = os.path.join( output_path, 'alfresco_basalchange_acrossreps_{}.tif'.format( group_id ) )
	with rasterio.open( output_filename, 'w', **meta ) as out:
		basalavg[ vegmap == 255 ] = -9999
		out.write( basalavg.astype( np.float32 ), 1 )

	return output_filename
	

if __name__ == '__main__':
	import os, rasterio
	import numpy as np
	from alfresco_postprocessing import FileLister, veg_name_dict
	from functools import partial
	from pathos.mp_map import mp_map

	# inputs
	vegmap_fn = '/atlas_scratch/ALFRESCO/ALFRESCO_Master_Dataset/ALFRESCO_Model_Input_Datasets/AK_CAN_Inputs/Landcover/LandCover_alf_2005.tif'
	vegmap = rasterio.open( vegmap_fn ).read( 1 )

	# crop vegmap for use with IEM-based ALF outputs... <<<- this is a hack for working with the SERDP outputs as a TEST
	vegmap = vegmap[:2100, :3650]

	alf_dir = '/big_scratch/apbennett/ALFRESCO_Projects/SERDP/GFDL-CM3.rcp85/Maps'
	files = FileLister( alf_dir )
	timesteps = files.timesteps

	grouped_years = [ i for i in files.files_df.groupby( 'year' ) ]
	
	output_path = '/workspace/Shared/Users/malindgren/basal_across_reps'
	run = partial( basal_across_reps, vegmap=vegmap, output_path=output_path )
	done = mp_map( run, grouped_years, nproc=15 )



# 2. In basal area maps, ignore any cells that were not originally tundra in the veg input map (i.e., set to zero).

# 3. For cells which were tundra in the veg input map:
#     A. Retain the basal area score (1-20) for current veg map tundra cells which have such a basal area map score.
#     B. If no score is present set basal area map cell to zero if still a tundra cell in the current veg map; set it to 20 if currently a spruce cell.

# 4. Average basal area maps across reps, rescale to [0, 1] or [0, 100], optionally round off.

# Result: One map of likelihood/probability of transition per year.
