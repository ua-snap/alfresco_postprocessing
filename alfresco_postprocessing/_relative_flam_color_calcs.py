# this is something that should be added to the relative flammability code
# snippet base as a possible way to remove some of the less desirable flammable
# areas that make it hard to differentiate hi/lo regions.

def return_median_thresh( nyears=200, nreps=200, min_fri=100 ):
	'''
	based on a number of years, replicates, and minimum fire return interval
	calculate a median threshold value to do a simple cut on the data at the midpoint of 
	possible values.  This will hopefully remove pixels that burn less than 50% of the
	time, which can be viewed as less flammable.
	'''
	ntotal = nyears * nreps
	burn_potential = nyears ) / min_fri
	burn_total = burn_potential * nreps
	max_index = burn_total / ntotal
	return max_index / 2

# maybe we should look at the relative falmmaility 