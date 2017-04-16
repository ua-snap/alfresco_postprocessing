## ALFRESCO Post-Processing
--------------------------
**version 3.1** Experimental Version

**Python Module for calculating summary statistics across the Geospatial Raster (GeoTiff) outputs from the ALFRESCO Fire Dynamics Model [snap.uaf.edu](www.snap.uaf.edu)**


#### ALFRESCO output data descriptions:

* Age - raster map time series at an annual timestep and contains for each pixel, its age
in years.

* Veg - raster map time series at an annual timestep and contains for each pixel, a 
categorical variable representing a landcover class.  Land cover classes
transition over time due to disturbances (fire).
```
Internal Vegetation Class Dictionary:
	1.) 'Black Spruce'
	2.) 'White Spruce'
	3.) 'Deciduous'
	4.) 'Shrub Tundra'
	5.) 'Graminoid Tundra'
	6.) 'Wetland Tundra'
	7.) 'Barren lichen-moss'
	8.) 'Temperate Rainforest
```
* FireScar - A 3-banded raster map at an annual timestep.
```
band descriptions:
	1.) identifies each pixel as the year since last burn.
	2.) identifies each fire patch with a unique integer value patch count begins at 1.
	3.) boolean value (0,1) where a fire's ignition point is 1.
```
* BurnSeverity - [not yet supported]

* BasalArea - [not yet supported]

Summary statistics can also be calculated across a set of sub-domains within the Area of Interest (AOI)
for more localized summary statistics results.

#### Installation:

external package dependencies:
rasterio requires: `gdal` library development bindings for your system.

```bash
# make sure that NumPy is installed first due to some dependency weirdness
pip install numpy
pip install git+https://github.com/ua-snap/alfresco-postprocessing/tree/alfresco_postprocessing
```

#### Basic Usage:

once installed package use looks something like this:

```python
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

# * * * * * * * * experimental * * * * * * * * * * * * * * * * * * * * * * * * * *
# # Plot
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

```
the new object generated above named `pp` is a [TinyDB](https://tinydb.readthedocs.org/en/latest/) database, which sorts the data in a JSON file on disk, but allows for simple querying if desired by the end user.  Currently, we are using this internally as a simple and straightforward way to store the output data as json records which minimizes somewhat painful nesting utilized in older versions.


A Query example would look something like this:
```python
# using data from above in continuation
# how many records are in it?
len( pp )

# query a specific replicates values
User = Query()
queried_json = db.search(User.replicate == '99')

# dump to the screen to prove it worked it is a list of dicts
print queried_json
```

