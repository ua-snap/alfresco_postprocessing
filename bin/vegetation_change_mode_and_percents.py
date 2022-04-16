import argparse
import glob
import os
import time
from itertools import groupby
import rasterio
import numpy as np
from pathos.mp_map import mp_map
from scipy import stats


def get_rep_num(x):
    base = os.path.basename(x)
    return base.split("_")[1]


def open_raster(fn, band=1):
    with rasterio.open(fn) as out:
        arr = out.read(band)
    return arr


def main(args):
    dirname, basename = os.path.split(args.output_filename)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    # list, sort, group by replicate
    veg_list = [
        os.path.join(root, fn)
        for root, subs, files in os.walk(args.maps_path)
        for fn in files
        if "Veg_" in fn and fn.endswith(".tif")
    ]
    year_list = range(args.begin_year, args.end_year + 1)
    veg_list = [
        i
        for i in veg_list
        if int(
            os.path.basename(i)
            .split("_")[len(os.path.basename(i).split("_")) - 1]
            .split(".")[0]
        )
        in year_list
    ]
    veg_sorted = sorted(veg_list, key=lambda x: get_rep_num(x))
    veg_grouped = [
        list(g) for k, g in groupby(veg_sorted, key=lambda x: get_rep_num(x))
    ]

    print("Calculating mode and percentages of vegetation data", flush=True)
    tic = time.perf_counter()

    # Read raster data from each file into a list of a list of 2D arrays.
    # The first-level list stores the replicates for each year.
    # The second-level list stores the rasters for each year's replicates.
    # The rasters are 2D grids of x/y coordinates and vegetation type value.
    raster_data = [mp_map(open_raster, v, nproc=int(args.ncores)) for v in veg_grouped]

    # Turn list of list of 2D arrays into 4D array with axes:
    # Axis 0: years
    # Axis 1: replicates
    # Axis 2: y
    # Axis 3: x
    # Return value shape (with 10 years and 200 replicates): 10, 200, 2100, 3650
    hypercube = np.array(raster_data)

    # Reorder axes so years (0) and replicates (1) can be combined next.
    # Return value shape: 2100, 3650, 10, 200
    hypercube = hypercube.transpose(2, 3, 0, 1)

    # Use the reshape function to convert 4D array into a 3D array with year
    # and replicate data combined into one axis. Reshape effectively unwraps
    # the data into a 1D array, then wraps it back up into the provided
    # dimensions. The -1 arguments means "combine all remaining axes into one".
    # Return value shape: 2100, 3650, 2000
    cube = hypercube.reshape(hypercube.shape[0], hypercube.shape[1], -1)
    del hypercube
    del raster_data

    # Create 2D array of x, y, and mode of vegetation type.
    mode_results = stats.mode(cube, axis=2)
    mode_grid = np.asarray(mode_results[0])
    mode_grid = mode_grid.reshape(mode_grid.shape[0], -1)
    mode_grid = mode_grid.astype(np.float32)

    # Mask the data with the out-of-bounds (255).
    with rasterio.open(veg_list[0]) as rst:
        arr = rst.read(1)
        mode_grid[arr == 255] = -9999

    meta = rasterio.open(veg_list[0]).meta
    meta.update(
        compress="lzw", dtype=np.float32, crs={"init": "EPSG:3338"}, nodata=-9999
    )

    dirname = os.path.dirname(args.output_filename)
    mode_dir = dirname + "/mode"
    percent_dir = dirname + "/percent"

    for dir in [mode_dir, percent_dir]:
        if not os.path.exists(dir):
            os.mkdir(dir)

    basename = os.path.basename(args.output_filename)
    filename = mode_dir + "/" + basename

    print(f"Writing results to {filename}", end="...", flush=True)
    with rasterio.open(filename, "w", **meta) as out:
        out.write(mode_grid, 1)

    # Create list of eight 2D arrays, one 2D array for each vegetation type.
    # Each 2D array is x, y, and percentage presence of that vegetation type.
    percentages = np.zeros((cube.shape[0], cube.shape[1]), dtype=np.float32)
    for veg_type in range(0, 9):
        for y in range(cube.shape[0]):
            sums = np.sum(np.where(cube[y] == veg_type, 1, 0), axis=1)
            percentages[y] = np.true_divide(sums, cube.shape[2]).astype(np.float32)
        splitext = os.path.splitext(basename)
        filename = percent_dir + "/" + splitext[0] + "_" + str(veg_type) + splitext[1]
        print(f"Writing results to {filename}", end="...", flush=True)

        with rasterio.open(veg_list[0]) as rst:
            arr = rst.read(1)
            percentages[arr == 255] = -9999

            meta = rasterio.open(veg_list[0]).meta
            meta.update(
                compress="lzw", dtype=np.float32, crs={"init": "EPSG:3338"}, nodata=-9999
            )

        with rasterio.open(filename, "w", **meta) as out:
            out.write(percentages, 1)

    print(f"done, total time: {round((time.perf_counter() - tic) / 60, 1)}m")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="program to calculate mode and percentage vegetation types from ALFRESCO"
    )
    parser.add_argument(
        "-p",
        "--maps_path",
        action="store",
        dest="maps_path",
        type=str,
        help="path to ALFRESCO output Maps directory",
    )
    parser.add_argument(
        "-o",
        "--output_filename",
        action="store",
        dest="output_filename",
        type=str,
        help="path to output directory",
    )
    parser.add_argument(
        "-nc",
        "--ncores",
        action="store",
        dest="ncores",
        type=int,
        help="number of cores",
    )
    parser.add_argument(
        "-by",
        "--begin_year",
        action="store",
        dest="begin_year",
        type=int,
        help="beginning year in the range",
    )
    parser.add_argument(
        "-ey",
        "--end_year",
        action="store",
        dest="end_year",
        type=int,
        help="ending year in the range",
    )

    args = parser.parse_args()
    _ = main(args)
