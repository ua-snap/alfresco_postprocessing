from setuptools import setup

dependencies_list = ['numpy','scipy','rasterio','shapely','pandas','geopandas','tinydb','ujson']
#scripts_list = [	'bin/alfresco_aggregate_domains_json.py', 'bin/alfresco_fire_return_interval_estimate.py', \
#			'bin/alfresco_json_manipulation_historical.py', 'bin/alfresco_json_manipulation.py', \
#			'bin/alfresco_modify_postprocessing_colnames_historical.py', 'bin/alfresco_modify_postprocessing_csv_names.py', \
#			'bin/alfresco_postprocessing_historical.py', 'bin/alfresco_postprocessing_launcher.py', \
#			'bin/alfresco_postprocessing_plotting.py', 'bin/alfresco_postprocessing.py', 'bin/alfresco_relative_flammability.py', \
#			'bin/alfresco_relative_vegetation_change.py', 'bin/alfresco_treeline_expansion_raster.py'	]

classifiers = [ 	'Development Status :: 3 - Alpha',
			'Operating System :: POSIX :: Linux',
			'Environment :: Console',
			'Intended Audience :: Science/Research',
			'Intended Audience :: End Users/Desktop',
			'Topic :: Software Development :: Build Tools',
			'License :: OSI Approved :: MIT License',
			'Programming Language :: Python :: 2.7',
			'Natural Language :: English',
			'Operating System :: POSIX :: Linux',
			'Programming Language :: Python :: 2.7',
			'Topic :: Scientific/Engineering :: GIS',
			'Topic :: Scientific/Engineering :: Boreal Fire Dynamics Model'	]

setup(	name='alfresco_postprocessing',
		version='3.1',
		description='tool to return summaries of ALFRESCO Fire Dynamics Model output GeoTiff rasters',
		url='https://github.com/ua-snap/alfresco-calibration/alfresco_postprocessing',
		author='Michael Lindgren',
		author_email='malindgren@alaska.edu',
		license='MIT',
		packages=['alfresco_postprocessing'],
		install_requires=dependencies_list,
		zip_safe=False,
		include_package_data=True,
		#dependency_links=['https://github.com/uqfoundation/pathos'],
		#scripts=scripts_list,
		classifiers=classifiers	)
