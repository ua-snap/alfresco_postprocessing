# BOXPLOT ALF TAB
import pandas as pd
import numpy as np
import matplotlib, os
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from matplotlib import ticker
import matplotlib.lines as mlines
import matplotlib.patches as mpatches


# update rcParams:
from matplotlib import rcParams
rcParams['xtick.direction'] = 'out'
rcParams['ytick.direction'] = 'out'

# futures:
obs = '/atlas_scratch/malindgren/ak_landcarbon_duffy/Fire_Acreage_Thoman.csv'
obs_df = pd.read_csv( obs, sep=',', index_col=0 )
obs_df = obs_df.loc[ 1950:2015, : ]
obs_df = obs_df.reset_index()
obs_df['km'] = (obs_df.Acreage * 0.00404686)

tab = '/atlas_scratch/malindgren/ak_landcarbon_duffy/cccma_cgcm3_1_sresa1b/total_area_burned/alfresco_totalareaburned_Alaska_cccma_cgcm3_1_sresa1b_landcarbon_ak_1900_2100.csv'
df = pd.read_csv( tab, sep=',', index_col=0 )
df = df.loc[ 1950:2015, : ]

# RAW AND DIRTY MPL
dfd = df.T.to_dict( orient='list' )
dat = [ np.array(dfd[i]) for i in df.T.columns ]
figsize = (14, 9)

# Create a figure instance
fig = plt.figure( 1, figsize=figsize )
# Create an axes instance
ax = fig.add_subplot( 111 )

# setup spines
ax.spines[ "top" ].set_visible( True ) 
ax.spines[ "bottom" ].set_visible( True )
ax.spines[ "right" ].set_visible( True )
ax.spines[ "left" ].set_visible( True )

# box configs
boxprops = dict( linestyle='-', linewidth=0.6, color='black' )
whiskerprops = dict( linestyle='-', linewidth=0.6, color='black' )
capprops = dict( linestyle='-', linewidth=0.6, color='black' )
medianprops = dict( linestyle='-', linewidth=0.6, color='DarkBlue' )

# plot it using base matplotlib's boxplot function... -- Full range 
whis = [5,95] # 'range'
bp = plt.boxplot( dat, notch=True, whis=whis, showfliers=False, \
			boxprops=boxprops, whiskerprops=whiskerprops, \
			capprops=capprops, medianprops=medianprops, patch_artist=True )

## change outline color, fill color and linewidth of the boxes
for box in bp['boxes']:
    # change outline color
    # box.set( color='#7570b3', linewidth=2)
    # change fill color
    box.set( facecolor='lightgrey' )

# # overplot with black 5-95 percentiles 
# whis = [5,95]
# whiskerprops = dict( linestyle='-', linewidth=0.5, color='black' )
# capprops = dict( linestyle='', linewidth=0.5, color='black' )
# plt.boxplot( dat, notch=True, whis=whis, showfliers=False, \
# 			boxprops=boxprops, whiskerprops=whiskerprops, \
# 			capprops=capprops, medianprops=medianprops,   )


# ax, bp = df.T.plot.box( ax=ax, return_type='both', grid=False, figsize=figsize, whis=(5,95), widths=0.75, showfliers=False, sym='', rot=45, notch=True, color=color )
markersize = 60 # default:20
plt.scatter( range(1,len(obs_df.Year.tolist())+1), obs_df.km.tolist(), zorder=10, marker='*', s=markersize, color='DarkRed' )

ax.get_xaxis().tick_bottom()
ax.get_yaxis().tick_left()

plt.xlabel( 'Year' )
plt.ylabel( 'Area Burned (km2)' )

# TITLE and stuff.
nreps = len( df.columns )
domain = 'Alaska Statewide'

# plot_title = 'ALFRESCO Annual Area Burned 1950-2015 \n %s - %s Replicates ' \
# 		% ( domain, nreps )
# plt.title( plot_title )

# here is the really really hacky way to set the darn xaxis labels in the non-standard way we 
# would like.  Where we have the first and last years present regardless of interval.
years = df.index.tolist() # all labels
# # set the labels with the years
ax.xaxis.set_ticklabels( years )

# plt.setp( ax.get_xticklabels(), visible=False ) # turn all labels off
# locs = ax.get_xticklabels()[::5] # list the ones to turn on
# last = ax.get_xticklabels()[-1]
# locs.append( last )
# plt.setp( locs, visible=True, rotation='vertical' ) # set every 5th to on

# # # A NEW WAY TO DEAL WITH TICKS
# minor_locator = AutoMinorLocator()
# ax.xaxis.set_minor_locator( minor_locator )

# majorLocator = ticker.MultipleLocator( 5 )
# # majorFormatter = ticker.FormatStrFormatter( '%d' )
minorLocator = ticker.MultipleLocator( 1 )
# ax.xaxis.set_major_locator( majorLocator )
ax.xaxis.set_minor_locator( minorLocator )

# ax.xaxis.set_major_formatter( majorFormatter )
# for the minor ticks, use no labels; default NullFormatter


# # #  END A NEW WAY TO DEAL WITH TICKS

# # ********
# majorLocator   = ticker.MultipleLocator(5)
# majorFormatter = ticker.FormatStrFormatter('%d')
# minorLocator   = ticker.MultipleLocator(1)

# labels = years[::5]
# labels.append( 2009 )

# majorLocator   = ticker.FixedLocator( labels[::5] )
# # minorLocator   = ticker.FixedLocator(np.linspace(19,41,23))

# ax.xaxis.set_major_locator(majorLocator)
# ax.xaxis.set_major_formatter(majorFormatter)
# ax.xaxis.set_minor_locator(minorLocator)


# ********
# FROM plot.py

n = 5 # every n ticks... from the existing set of all
ticks = ax.xaxis.get_ticklocs()
ticklocs = ticks[::n]
ticklocs = np.append( ticklocs, ticks[-1] )
ax.xaxis.set_ticks( ticklocs )
# ticks.append( ticks[-1]-1 ) # add back in the last year -- 2009
ticklabels = [ years[i-1] for i in ticklocs ]
# ticklabels = [ l.get_text() for l in ax.xaxis.get_ticklabels() ][::n]
ticklabels.append( years[-1] )

# update the size of the ticks
ax.tick_params( size=8 )

# ax.xaxis.set_ticks(  )
ax.xaxis.set_ticklabels( ticklabels )
ax.set_xlabel( 'Year', fontsize=13 )
ax.set_ylabel( 'Area Burned (' + '$\mathregular{km^2}$' + ')', fontsize=13 )

# we need a dynamic way to set the yaxis lims.  Le
begin, end = ax.get_ylim()
ax.set_ylim( 0, 30000 )

# make the ticks be comma-style for thousands
ax.get_yaxis().set_major_formatter(
    matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

# Update the size of the tick labels
plt.setp( ax.get_xticklabels(), fontsize=12 )
plt.setp( ax.get_yticklabels(), fontsize=12 )

# LEGEND IT UP!
# whiskers = mlines.Line2D( [], [], color='black', markersize=15, marker='', label='data range (whiskers)' )
# median = mlines.Line2D( [], [], color='DarkBlue', markersize=15, marker='', label='median line' )
# obs = plt.Line2D((0,1),(0,0), color='DarkRed', marker='*', linestyle='', markeredgecolor='DarkRed', label='observed' )
# plt.legend( handles=[obs], numpoints=1, fontsize='x-small' ) # they didnt want a legend

# save it out
# plt.savefig( '/atlas_scratch/malindgren/ak_landcarbon_duffy/alfresco_aab_boxplot_LandCarbon_AK_1950_2015_v2.png', dpi=600 )
plt.savefig( '/workspace/UA/malindgren/alfresco_aab_boxplot_LandCarbon_AK_1950_2015_v3.png', dpi=600 )
plt.close()

