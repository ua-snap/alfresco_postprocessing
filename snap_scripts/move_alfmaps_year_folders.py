# move the files into year folders 
def move_files( fn, output_path ):
	dirname, basename = os.path.split( fn )
	print( 'moving: %s' % basename )
	rep, year = basename.split( '.' )[0].split( '_' )[-2:]
	new_path = os.path.join( output_path, year )

	try:
		if not os.path.exists( new_path ):
			os.makedirs( new_path )
	except:
		pass
	out_fn = os.path.join( new_path, basename )
	shutil.move( fn, out_fn )
	return out_fn

if __name__ == '__main__':
	# files to folders:
	import os, itertools, glob, shutil
	from pathos.mp_map import mp_map
	from functools import partial
	import argparse

	parser = argparse.ArgumentParser( description='move ALFRESCO Output GeoTiffs to yearly folders' )
	parser.add_argument( '-p', '--maps_path', action='store', dest='maps_path', type=str, help='path to ALFRESCO output Maps directory' )

	args = parser.parse_args()
	maps_path = args.maps_path

	# maps_path = '/atlas_scratch/apbennett/Calibration/HighCalib/FMO_Calibrated/GISS-E2-R_rcp85_AltFMO/Maps'
	variables = ['Age', 'Veg', 'FireScar', 'BasalArea', 'BurnSeverity'] # more can be added if they are needed. 
	out = [ i for i in itertools.product( [maps_path], variables ) ]

	# run
	for i in out:
		l = glob.glob( os.path.join( *i ) + '*.tif' )
		# run it in parallel:
		f = partial( move_files, output_path=maps_path )
		out_filenames = mp_map( f, sequence=l, nproc=32 )
