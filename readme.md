# ALFRESCO Post-Processing

**version 3.1**

**Python Module for calculating summary statistics across the Geospatial Raster (GeoTiff) outputs from the [ALFRESCO Fire Dynamics Model](https://www.snap.uaf.edu/projects/alfresco-habitat)**

### Installation:

#### Install Python on Atlas Cluster
you will need Python 2.7.11+ (this is an old tool) to run this code as it currently stands. To install it on Atlas follow [these instructions](https://github.com/ua-snap/alfresco_postprocessing/How_To_Install_and_Use_Python2_on_Atlas.md)

#### Clone the repository from github
```sh
git clone git@github.com:ua-snap/alfresco_postprocessing.git
cd alfresco_postprocessing
```

### Use Python2 to make a virtual environment
```sh
~/.localpython/bin/virtualenv venv --python=~/.localpython/bin/python2.7
source ~/venv/bin/activate
```

[note]: external package dependencies:
rasterio requires: `gdal` library development bindings for your system.

```bash
# make sure that NumPy is installed first due to some dependency weirdness
pip install numpy

# install the packages needed to run alfresco_postprocessing by installing everything in the 
# repo's `requirements.txt` file
pip install -r requirements.txt
```

#### Install `alfresco_postprocessing`
```sh
python setup.py install
```
if you experience issues with using different branches, you will need to `git checkout <branch>` first, then `pip uninstall alfresco_postprocessing` if it has already been installed, followed by a re-install using the repo's `setup.py` file like the above command. I have also had luck (in the past) installing from `pip install --upgrade git+git://github.com/ua-snap/alfresco_postprocessing@master`, but YMMV.


### Basic Usage:

Once successfully installed package usage looks something like this:

```python
# * * * * * * * * * * * * * * * * * * * * * * * * * * *
# ALFRESCO POST-PROCESSING EXAMPLE 
# * * * * * * * * * * * * * * * * * * * * * * * * * * *

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
metrics = [ 'veg_counts','avg_fire_size','number_of_fires','all_fire_sizes','total_area_burned','severity_counts' ]

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

# * * * * * * * * PLOTTING * * * * * * * * * * * * * * * * * * * * * * * * * *

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
the new `Plot` object generated above named `pp` contains a [TinyDB](https://tinydb.readthedocs.org/en/latest/) database as an attribute `db`, which sorts the data in a JSON file on disk, but allows for simple querying if desired by the end user.  Currently, we are using this internally as a simple and straightforward way to store the output data as json records which minimizes somewhat painful nesting utilized in older versions.


A Query example would look something like this:
```python
# using data from above in continuation
# how many records are in it?
len( pp.db )

# query a specific replicates values
User = Query()
queried_json = pp.db.search(User.replicate == '99')

# dump to the screen to prove it worked it is a list of dicts
print queried_json

# a way to get to all the records of the database as a list, which makes working with the data
# much easier, this will do it
records = pp.db.all()
```

It is also useful to compute 'best replicates', which is not easy given the close relationship of each of the future realizations (replicates), but a simple and way that is rife with problems is to do the following:

```python

if __name__ == '__main__':
	from alfresco_postprocessing import *
	import os

	# alfpp generated json files
	modeled_json = 'alf.json'
	observed_json = 'obs.json'

	# plot objects:
	modplot = Plot( modeled_json, 'model', 'scenario' )
	obsplot = Plot( observed_json, 'model', 'scenario' )

	# calc best rep -- returns:{ replicate:correlation value }
	best_rep( modplot, obsplot, domain, method='spearman' )

```

### ALFRESCO Data Output Descriptions:

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
* BurnSeverity - Burn severity levels for each fire patch in an ALFRESCO Output FireScar file.

* BasalArea - [not yet supported]

Summary statistics can also be calculated across a set of sub-domains within the Area of Interest (AOI)
for more localized summary statistics results.




_TODO: add information about CLI binaries that are distributed with this package for relative veg, flammability, and more._



