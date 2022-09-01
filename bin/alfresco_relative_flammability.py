"""Compute relative flammability from FireScar ALFRESCO maps
Note - this script relies on a specific file organization structure
"""

import argparse
import os

# potential fix for "OpenBLAS blas_thread_init: pthread_create failed for thread . of 64: Resource temporarily unavailable" warnings
os.environ["OPENBLAS_NUM_THREADS"] = "1"
import time
import multiprocessing as mp
from functools import partial
from multiprocessing import set_start_method
import numpy as np
import pandas as pd
import rasterio


def get_repnum(fn):
    """
    based on the current ALFRESCO FireScar naming convention,
    return the replicate number
    """
    return os.path.basename(fn).split("_")[-2]


def read_ignition_arr(fn, band=3, masked=False):
    """Read a raster band and return ignition arr"""
    with rasterio.open(fn) as out:
        arr = out.read(band, masked=masked)
    return np.where(arr >= 0, 1, 0)


def run_group(group):
    group_arr = np.array([read_ignition_arr(fn) for fn in group])
    group_sum = np.sum(group_arr, axis=0)
    return group_sum


def chunk_groups(group_list, n=50):
    """Split a list of filepath groups into smaller groups"""

    def chunk(l, n):
        # looping till length l
        for i in range(0, len(l), n):
            yield l[i : i + n]

    new_groups = []
    for group in group_list:
        new_groups.extend(chunk(group, n))

    return new_groups


def sum_firescars(firescar_list, ncores):
    # groupby the replicate number
    firescar_series = pd.Series(firescar_list)
    repgrouper = firescar_series.apply(get_repnum)
    firescar_groups = [j.tolist() for i, j in firescar_series.groupby(repgrouper)]

    # Pool.map() is locking up with larger groups for some reason,
    # try splitting into smaller groups to improve success
    if len(firescar_groups[0]) > 50:
        firescar_groups = chunk_groups(firescar_groups, 50)

    print("running firescar groups summation")

    with mp.Pool(ncores) as pool:
        repsums = pool.map(run_group, firescar_groups)
    print("firescar groups summation done. summing all groups")
    sum_arr = np.sum(np.array(repsums), axis=0)
    print("firescar summation done")
    return sum_arr


def relative_flammability(
    firescar_list,
    output_filename,
    mask_arr,
    mask_value,
    ncores,
    crs=None,
):
    """
    run relative flammability.
    Arguments:
        firescar_list = [list] string paths to all GeoTiff FireScar outputs to be processed
        output_filename = [str] path to output relative flammability filename to be generated.
                        * only GTiff supported. *
        ncores = [int] number of cores to use if None multiprocessing.cpu_count() used.
        mask_arr = [numpy.ndarray] numpy ndarray with dimensions matching the rasters' arrays
                    listed in firescar_list and masked where 1=dontmask 0=mask (this is opposite
                    numpy mask behavior, but follows common GIS patterns ) * THIS MAY CHANGE. *
        crs=[dict] rasterio-compatible crs dict object i.e.: {'init':'epsg:3338'}

    Returns:
        output_filename, with the side effect of the relative flammability raster being written to
        disk in that location.
    """
    tmp_rst = rasterio.open(firescar_list[0])

    out = sum_firescars(firescar_list, ncores=ncores)

    # calculate the relative flammability -- and fill in the mask with -9999
    relative_flammability = out.astype(np.float32) / len(firescar_list)

    if mask_arr is not None:
        relative_flammability[mask_arr == 0] = mask_value

    meta = tmp_rst.meta
    meta.update(compress="lzw", count=1, dtype="float32", nodata=mask_value)

    if crs:
        meta.update(crs=crs)

    try:
        dirname = os.path.dirname(output_filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
    except:
        pass

    with rasterio.open(output_filename, "w", **meta) as out_rst:
        tags = tmp_rst.tags()

        # Replace replicate info with a more general description for aggregate
        # GeoTIFFs.
        tags["TIFFTAG_IMAGEDESCRIPTION"] = "Values represent flammability."

        out_rst.update_tags(**tags)
        out_rst.write(np.around(relative_flammability, 4), 1)

    return output_filename


if __name__ == "__main__":
    # values - keep for reference
    # maps_path = '/atlas_scratch/apbennett/IEM_AR5/GFDL-CM3_rcp60/Maps'
    # output_filename = '/workspace/Shared/Users/malindgren/TEST_ALF/alf_relflam_test_1900_1999.tif'
    # ncores = 32
    # begin_year = 1900
    # end_year = 1999

    # track time
    tic = time.perf_counter()

    parser = argparse.ArgumentParser(
        description="program to calculate Relative Flammability from ALFRESCO"
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

    maps_path = args.maps_path
    output_filename = args.output_filename
    ncores = args.ncores
    begin_year = args.begin_year
    end_year = args.end_year

    # list the rasters we are going to use here
    firescar_list = [
        os.path.join(root, fn)
        for root, subs, files in os.walk(maps_path)
        for fn in files
        if "FireScar_" in fn and fn.endswith(".tif")
    ]

    year_list = range(begin_year, end_year + 1)
    firescar_list = [
        i
        for i in firescar_list
        if int(
            os.path.basename(i)
            .split("_")[len(os.path.basename(i).split("_")) - 1]
            .split(".")[0]
        )
        in year_list
    ]

    # mask -- get from the Veg file of firescar_list[0]
    mask = rasterio.open(firescar_list[0].replace("FireScar_", "Veg_")).read_masks(1)
    mask = (mask == 255).astype(int)
    mask_value = -9999

    # this might help prevent mp.Pool from getting stuck?
    set_start_method("spawn")
    # run relative flammability
    relflam_fn = relative_flammability(
        firescar_list,
        output_filename,
        mask,
        mask_value,
        ncores,
        crs={"init": "epsg:3338"},
    )

    print(f"Relative flammability computed, results written to {output_filename}")
    print(f"Elapsed time: {round((time.perf_counter() - tic) / 60, 1)}m")
