# how to get ratios from alfresco rasters:
import os, glob, rasterio
import pathos.multiprocessing as mp

# list the files:
maps_path = '/atlas_scratch/apbennett/Calibration/HighCalib/FMO_Calibrated/GISS-E2-R_rcp85_AltFMO/Maps'

files = [ os.path.join( root, i ) for root, subs, files in os.walk( maps_path ) \
			if len( files ) > 0 for i in files if 'Veg_' in i ]

rep_files = sorted( [ i for i in files if '_0_' in i ] )

# # VEGETATION MAP DEFAULT:
veg_name_dict = {1:'Black Spruce',
				2:'White Spruce',
				3:'Deciduous',
				4:'Shrub Tundra',
				5:'Graminoid Tundra',
				6:'Wetland Tundra',
				7:'Barren lichen-moss',
				8:'Temperate Rainforest'}

# conifers = [ 'Black Spruce','White Spruce' ]
# [ veg_name_dict[ key ] for key in veg_name_dict.keys() ]

# , group1=[1,2], group2=[1] 
def veg_ratio( veg ):
	var, rep, year = os.path.basename( veg ).split('.')[0].split( '_' )
	veg = rasterio.open( veg )
	arr = veg.read( 1 )
	conif, = arr[ (arr==1) | (arr==2) ].shape
	decid, = arr[ arr == 3 ].shape
	return (year,(conif / float(decid)))
	
if __name__ == '__main__':
	# run that
	pool = mp.Pool( 32 )
	ratios = pool.map( veg_ratio, rep_files )
	pool.close()
	pool.join()



