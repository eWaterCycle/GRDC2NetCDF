#!/usr/bin/env python
"""
TL:DR pre-processing of GRDC files into netCDF.

The function grdc2netcdf converts files from the Global Runoff Data Center (GRDC,
http://www.bafg.de/GRDC/EN/Home/homepage_node.html) into a NetCDF file. Required
inputs are:
inputLocation: a directory with GRDC station data
outputFile: a fileName of the netCDF file to save.
timeType: a string, either daily or monthly to indicatie what type of GRDC data
startDate: a startDate provided in YYYY-MM-DD
endDate: a endDate provided in YYYY-MM-DD
The resulting netCDF file will contain point-time series, ie. not a grid! 

This function was written as part of the eWaterCycle project (eWaterCycle.org).
In the eWaterCycle project, the output of this function is used to compare the fore-
casts of the eWaterCycle project to measured discharges. The comparison is done using
the Climate Data Operators (CDO) toolset (https://code.zmaw.de/projects/cdo).

This function is written by Rolf Hut (https://github.com/RolfHut/)
On this software, the Apache 2.0 license applies (http://www.apache.org/licenses/LICENSE-2.0)
with the addition that any scientific publication that uses this work, should cite it using
the following DOI: 
"""

import sys
import os

import re
import glob
import datetime
import calendar as cal
import netCDF4



def grdc2netcdf(inputLocation,outputFile,timeType,startDate,endDate):
    ###
    # get arguments. this should be:
    # inputLocation: a directory with GRDC station data
    # outputFile: a fileName of the netCDF file to save.
    # timeType: "daily" or "monthly" to indicatie what type of GRDC data
    # startDate: a startDate provided in YYYY-MM-DD
    # endDate: a endDate provided in YYYY-MM-DD
    ###




        
    #make a structure with all GRDC data within 
    # get GRDC attributes of all stations:
    GRDCData = read_grdc(inputLocation,timeType, startDate,endDate)

    #write GRDC data to NetCDF file
    write_netcdf(outputFile, GRDCData, timeType)

#END OF MAIN


#reads GRDC files from location, select station data valid in date selection
#TODO add function to provide netCDF mask file and only provide stations that are within mask
def read_grdc(inputLocation, timeType, startDate=None,endDate=None):
    #this function is based on earlier work by Edwin Sutanudjaja from Utrecht University.
    # https://github.com/edwinkost/discharge_analysis_IWMI

    if (startDate != None) and (endDate != None):
        startDate = datetime.datetime.strptime(str(startDate),'%Y-%m-%d')
        endDate   = datetime.datetime.strptime(str(  endDate),'%Y-%m-%d')
 
    # initiating a dictionary that will contain all GRDC attributes:
    attributeGRDC = {}
    #
    # initiating keys in GRDC dictionary 
    grdc_dict_keys = \
            ["id_from_grdc",                 
            "grdc_file_name",               
            "river_name",                   
            "station_name",                 
            "country_code",                 
            "grdc_catchment_area_in_km2",   
            "grdc_latitude_in_arc_degree",  
            "grdc_longitude_in_arc_degree",
            "unit",
            "dataSetContent",
            "timeStamps",
            "timeStampsEndInterval",
             "dischargeData"]
    
    #initially, set everything to empty
    for key in grdc_dict_keys: attributeGRDC[key] = {}

    #make a list of all files to process
    searchString = str(inputLocation) + '/*'
    print(searchString)
    fileList = glob.glob(searchString)

    #loop through all files
    for fileName in fileList:
        print fileName

        # read the file
        f = open(fileName) ; allLines = f.read() ; f.close()

        # split the content of the file into several lines
        allLines = allLines.replace("\r","") 
        allLines = allLines.split("\n")

        # get grdc ids (from files) and check their consistency with their file names  
        id_from_file_name =  int(os.path.basename(fileName).split(".")[0])
        id_from_grdc = None
        if id_from_file_name == int(allLines[ 8].split(":")[1].replace(" ","")):
            id_from_grdc = int(allLines[ 8].split(":")[1].replace(" ",""))
        else:
            print("GRDC station "+str(id_from_file_name)+" ("+str(fileName)+") is NOT used.")

        if id_from_grdc != None:

            # initiate the dictionary values for each station (put all values to "NA")
            for key in attributeGRDC.items(): 
                attributeGRDC[key[0]][str(id_from_grdc)] = "EMPTY"

            # make sure the station has coordinate:
            grdc_latitude_in_arc_degree  = float(allLines[12].split(":")[1].replace(" ",""))
            grdc_longitude_in_arc_degree = float(allLines[13].split(":")[1].replace(" ",""))

            # get the catchment area (unit: km2)
            try:
                grdc_catchment_area_in_km2 = float(allLines[14].split(":")[1].replace(" ",""))
                if grdc_catchment_area_in_km2 <= 0.0:\
                   grdc_catchment_area_in_km2  = "NA" 
            except:
                grdc_catchment_area_in_km2 = "NA"

            # get the river name
            try:
                river_name = str(allLines[ 9].split(":")[1].replace(" ",""))
                river_name = re.sub("[^A-Za-z]", "_", river_name)
            except:
                river_name = "NA"

            # get the station name
            try:
                station_name = str(allLines[10].split(":")[1].replace(" ",""))
                station_name = re.sub("[^A-Za-z]", "_", station_name)
            except:
                station_name = "NA"

            # get the country code
            try:
                country_code = str(allLines[11].split(":")[1].replace(" ",""))
                country_code = re.sub("[^A-Za-z]", "_", country_code)
            except:
                country_code = "NA"

            # get the units
            #try:
            units = str(allLines[22].split(":")[1].replace(" ",""))
            units = re.sub("[^A-Za-z]", "_", units)
            ## except:
            ##     units = "NA"

            # get the dataSetContent (ie. what kind of data is in the file, usually monthly or daily discharge data)
            try:
                dataSetContent = str(allLines[20].split(":")[1].replace(" ",""))
            except:
                dataSetContent = "NA"

            
            # get the number of measurements
            try:
                nrMeasurements = int(str(allLines[38].split(":")[1].replace(" ","")))
            except:
                nrMeasurements = "NA"

            print(nrMeasurements)

            timeStamps=[]
            timeStampsEndInterval=[]
            dischargeData=[]

            # get the timeStamps and actual data
            if nrMeasurements is not "NA":
                for measurement in range(0, nrMeasurements):
                    rawLineSplit = allLines[41+measurement].split(";")
                    if timeType == "monthly":
                        timeStamp=datetime.datetime.strptime(str(rawLineSplit[0]),'%Y-%m-00')
                        if startDate == None or (startDate <= timeStamp and endDate >= timeStamp):
                            timeStamps.append(timeStamp)
                            timeStampsEndInterval.append(add_months(timeStamp, 1))
                            dischargeData.append(float(rawLineSplit[3]))
                        
                    elif timeType == "daily":
                        timeStamp = datetime.datetime.strptime(str(rawLineSplit[0]),'%Y-%m-%d')
                        if startDate == None or (startDate <= timeStamp and endDate >= timeStamp):
                            timeStamps.append(timeStamp)
                            timeStampsEndInterval.append(timeStamp + datetime.timedelta(days=1))
                            dischargeData.append(float(rawLineSplit[3]))
                    else:
                        print("wtf")
                        timeStamps.append(-1)

            if timeStamps is not []:
                attributeGRDC["timeStamps"][str(id_from_grdc)] = timeStamps
                attributeGRDC["timeStampsEndInterval"][str(id_from_grdc)] = timeStampsEndInterval
                attributeGRDC["dischargeData"][str(id_from_grdc)] = dischargeData

                attributeGRDC["id_from_grdc"][str(id_from_grdc)]                 = id_from_grdc
                attributeGRDC["grdc_file_name"][str(id_from_grdc)]               = fileName
                attributeGRDC["river_name"][str(id_from_grdc)]                   = river_name
                attributeGRDC["station_name"][str(id_from_grdc)]                 = station_name
                attributeGRDC["country_code"][str(id_from_grdc)]                 = country_code
                attributeGRDC["grdc_latitude_in_arc_degree"][str(id_from_grdc)]  = grdc_latitude_in_arc_degree 
                attributeGRDC["grdc_longitude_in_arc_degree"][str(id_from_grdc)] = grdc_longitude_in_arc_degree
                attributeGRDC["grdc_catchment_area_in_km2"][str(id_from_grdc)]   = grdc_catchment_area_in_km2
                attributeGRDC["unit"][str(id_from_grdc)]                         = units
                attributeGRDC["dataSetContent"][str(id_from_grdc)]               = dataSetContent
            
            

    return attributeGRDC

def add_months(sourcedate,months):
    """ add number of months to a datetime object. stolen from
    # http://stackoverflow.com/questions/4130922/how-to-increment-datetime-month-in-python
    """
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month / 12
    month = month % 12 + 1
    day = min(sourcedate.day,cal.monthrange(year,month)[1])
    return datetime.datetime(year,month,day,sourcedate.hour,sourcedate.minute)

def write_netcdf(outputFile, GRDCData, timeScale):
    """using a structure with GRDCData, create a netCDF file with time-series-objects"""

    reference_date = "days since 1850-01-01 00:00"
    #remove old file
    if os.path.isfile(outputFile):
        os.remove(outputFile)

    cdf = netCDF4.Dataset(outputFile, format="NETCDF4", mode="w", clobber=False )
    dimdev = cdf.createDimension( "site", size=len(GRDCData["id_from_grdc"]) )
    dimtime = cdf.createDimension( "time",   size=None )
    
    varlat = cdf.createVariable( "lat", 'f4', ['site'], zlib = True )
    varlat.units = "degrees_north"

    varlon = cdf.createVariable( "lon", 'f4', ['site'], zlib = True )
    varlon.units = "degrees_east"

    vartime = cdf.createVariable( "time", 'i4', ["time",] , fill_value=-999, zlib = True )
    vartime.units = reference_date
    vartime.calendar = "standard"

    startDate=[]
    endDate=-1850*365 #jan first of year zero


    for stationID in GRDCData["id_from_grdc"]:
        startDate = min(startDate,int(netCDF4.date2num( GRDCData["timeStamps"][stationID][0], reference_date, calendar='standard' )))
        endDate = max(endDate,int(netCDF4.date2num( GRDCData["timeStampsEndInterval"][stationID][-1], reference_date, calendar='standard' )))
    vartime[...] = range(startDate, endDate) # * dt==1
    print(startDate)
    print(endDate)

    varDischarge = cdf.createVariable( "discharge", 'f4', ['time','site',], zlib=True, fill_value=-999.000 )
    varDischarge.units = "m3/s"
    varDischarge.coordinates = "lat lon"
    
    print "Creating new file"

    stationCounter = 0

    for stationID in GRDCData["id_from_grdc"]:

        #add station meta-data
        print(stationID)

        varlat[stationCounter] =  GRDCData["grdc_latitude_in_arc_degree"][stationID]
        varlon[stationCounter] =  GRDCData["grdc_longitude_in_arc_degree"][stationID]
        

        for timeCounter in range(0,len(GRDCData["dischargeData"][stationID])):

            #add measurement and timestamp
            daysSinceRefTime = int(netCDF4.date2num( GRDCData["timeStamps"][stationID][timeCounter], reference_date, calendar='standard' ))
            daysSinceRefTimeEndInterval = int(netCDF4.date2num( GRDCData["timeStampsEndInterval"][stationID][timeCounter], reference_date, calendar='standard' ))
            for dayIndex in range(daysSinceRefTime - startDate,daysSinceRefTimeEndInterval - startDate):
                varDischarge[dayIndex, stationCounter] = GRDCData["dischargeData"][stationID][timeCounter]

        stationCounter = stationCounter + 1

    
    return 1


if __name__ == "__main__":
    argument = sys.argv
    print(argument)
    print(argument[1])
    #check for right number of arguments
    if len(argument) == 6:
        startDate = argument[4]
        endDate = argument[5]
    elif len(argument) == 4:
        startDate = None
        endDate = None
    else:
        print("wrong number of arguments")
        sys.exit()

    #two mandatory arguments
    inputLocation = argument[1]
    outputFile = argument[3]
    timeType = argument[2]
    
    grdc2netcdf(inputLocation,outputFile,timeType,startDate,endDate)
