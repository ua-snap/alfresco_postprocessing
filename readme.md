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


standard python package installation:

```bash
git clone git@github.com:ua-snap/alfresco-calibration.git
cd alfresco-calibration/
git checkout alfresco-postprocessing # currently the devel branch
cd alfresco_postprocessing/
python setup.py install
```

or the super-simple `pip` way:
```bash
pip install git+https://github.com/ua-snap/alfresco-calibration/tree/alfresco-postprocessing/alfresco_postprocessing
```

It is hightly reccomended to install python *without* `sudo`.  A very simple way of doing this (ymmv) is highlighted [here](https://github.com/EarthScientist/etc/blob/master/Python_without_root "EarthScientist's ETC repo"). 


#### Basic Usage:

once installed package use looks something like this:

```python

# import library
import alfresco_postprocessing as ap
from tinydb import TinyDB, Query

# input args
ncores = 32
maps_path = './Maps'
subdomains_fn = './subdomains.shp'
id_field = 'ID'
name_field = 'Name'
out_json_fn = './output.json'
metrics = [ 'veg_counts','avg_fire_size','number_of_fires','all_fire_sizes','total_area_burned' ]

# PostProcess using shapefile-derived rasterized subdomains.
pp = ap.run_postprocessing( maps_path, out_json_fn, ncores, subdomains_fn, id_field, name_field )

# Output to CSV files for researcher ease-of-use
suffix = 'model_name' # some id for the output csvs
output_path = './output_csvs'
_ = ap.to_csvs( pp, metrics, output_path, suffix )

# close the database
pp.close() 
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

#### Docs
very new and not complete.

There is simple [documentation](http://ua-snap.github.io/alfresco-calibration) which is auto-generated and not nearly complete, but evolving daily. Any help with documentation is more than welcomed and appreciated.  :)

