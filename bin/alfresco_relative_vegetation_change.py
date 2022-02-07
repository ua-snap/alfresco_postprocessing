"""calculate vegetation resilience counts through time"""

import argparse
import os
import rasterio
import numpy as np
from itertools import groupby
from pathos.mp_map import mp_map


def get_rep_num(x):
    """return rep number from firescar filename"""
    base = os.path.basename(x)
    return base.split("_")[1]


def count_transitions(arr_list):
    """
    takes list of numpy ndarrays of integers and returns the number of
    shifts in values in the series. arr_list is expected to be in
    chronological order.
    """
    arr_list = np.array(
        [np.where(arr != 0, 1, 0) for arr in np.diff(np.array(arr_list), axis=0)]
    )
    return np.sum(arr_list, axis=0)


def open_raster(fn, band=1):
    """read a raster band with rasterio"""
    with rasterio.open(fn) as out:
        arr = out.read(band)
    return arr


def relative_veg_change(veg_list, ncpus=32):
    """
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
    """
    arr_list = mp_map(open_raster, veg_list, nproc=ncpus)
    return count_transitions(arr_list)


def main(args):
    """
    run relative flammability with the input args dict from argparse
    """
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

    # calculate relative vegetation change -- parallel
    # final = mp_map( relative_veg_change, veg_grouped, nproc=int( args.ncpus ) )
    final = [relative_veg_change(v, int(args.ncores)) for v in veg_grouped]
    final = np.sum(final, axis=0) / np.float(len(veg_list))

    # set dtype to float32 and round it
    final = final.astype(np.float32)
    final = np.around(final, 4)

    # mask the data with the out-of-bounds of Veg --> 255
    with rasterio.open(veg_list[0]) as rst:
        arr = rst.read(1)
        final[arr == 255] = -9999

    # write it out
    meta = rasterio.open(veg_list[0]).meta
    meta.update(
        compress="lzw", dtype=np.float32, crs={"init": "EPSG:3338"}, nodata=-9999
    )

    with rasterio.open(args.output_filename, "w", **meta) as out:
        out.write(final, 1)
    return args.output_filename


if __name__ == "__main__":
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
    _ = main(args)
