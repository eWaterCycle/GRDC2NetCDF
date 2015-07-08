# GRDC2NetCDF
Python code to convert Global Runoff Data Center (GRDC) files to NetCDF

The resulting netCDF file will contain point-time series, ie. not a grid! This is
according to the NetCDF CF conventions.

This function was written as part of the eWaterCycle project (http://eWaterCycle.org).
In the eWaterCycle project, the output of this function is used to compare the fore-
casts of the eWaterCycle project to measured discharges. The comparison is done using
the Climate Data Operators (CDO) toolset (https://code.zmaw.de/projects/cdo).

This function is written by Rolf Hut (https://github.com/RolfHut/)
On this software, the Apache 2.0 license applies (http://www.apache.org/licenses/LICENSE-2.0)
with the addition that any scientific publication that uses this work, should cite it using
the following DOI: 

