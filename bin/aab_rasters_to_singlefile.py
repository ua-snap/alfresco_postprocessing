# method to aggregate area burned across all raster years
def open_raster( fn, band ):
	with rasterio.open(fn) as rst:
		arr = rst.read(band)
	return arr

def burn_year( fn, band, out_arr, nodata ):
	arr = open_raster(fn,band)
	out_arr[arr != nodata] = arr[arr != nodata]

if __name__ == '__main__':
	import os, glob, rasterio
	import numpy as np

	# directory storing the FireScar data
	maps_path = './Maps'
	repnum = 1 # toss in the replicate number here to use in filename filtering.

	# lets list all of the firescars
	files = sorted([os.path.join(r,fn) for r,s,files in os.walk(maps_path) 
						for fn in files if 'FireScar_{}_'.format(repnum) in fn])

	# make an empty array of the same shape as the rasters
	with rasterio.open( files[0]) as tmp:
		out_arr = np.zeros(shape=tmp.shape, dtype=np.int)
		nodata = tmp.nodata
		meta = tmp.meta.copy()
		meta.update(compress='lzw')

	# process in serial (this could be modified to be parallel and much faster)
	_ = [ burn_year(fn, 1, out_arr, nodata) for fn in files ]

	# write it out to disk as annuals {not run}
	out_fn = 'alfresco_aab_annual_scars.tif'
	with rasterio.open( out_fn, 'w', **meta ) as out:
		out.write( out_arr, 1 )

	# make decadals...
	out_arr_decadal = np.zeros_like(out_arr)
	years = np.unique(out_arr)
	years = years[years != 0].astype(str)
	decades = [ int(year[:3]+'0') for year in years ]
	for year,decade in zip(years,decades):
		out_arr_decadal[ out_arr == int(year) ] = decade

	# write it out to disk as decadals {not run}
	out_fn = 'alfresco_aab_decadal_scars.tif'
	with rasterio.open( out_fn, 'w', **meta ) as out:
		out.write( out_arr_decadal, 1 )
