#pre-processing of GRDC files into netCDF

import sys
import os

import re
import glob
import datetime
import calendar as cal
import netCDF4



def main():
    ###
    # get arguments. this should be:
    # 1. a directory with GRDC station data
    # 2. "daily" or "monthly" to indicatie what type of GRDC data
    # 3. a fileName of the netCDF file to save.
    # 4. a startDate provided in YYYY-MM-DD
    # 5. a endDate provided in YYYY-MM-DD
    ###


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

        
    #make a structure with all GRDC data within 
    # get GRDC attributes of all stations:
    GRDCData = readGRDC(inputLocation,timeType, startDate,endDate)

    #write GRDC data to NetCDF file
    writeNetCDF(outputFile, GRDCData, timeType)

#END OF MAIN


#reads GRDC files from location, select station data valid in date selection
#TODO add function to provide netCDF mask file and only provide stations that are within mask
def readGRDC(inputLocation, timeType, startDate=None,endDate=None):

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


            # get the timeStamps and actual data
            if nrMeasurements is not "NA":
                timeStamps=[]
                timeStampsEndInterval=[]
                dischargeData=[]
                for measurement in range(0, nrMeasurements):
                    rawLineSplit = allLines[41+measurement].split(";")
                    if timeType == "monthly":
                        timeStamp=datetime.datetime.strptime(str(rawLineSplit[0]),'%Y-%m-00')
                        if startDate == None or (startDate <= timeStamp and endDate >= timeStamp):
                            timeStamps.append(timeStamp)
                            timeStampsEndInterval.append(add_months(timeStamp, 1))
                        
                    elif timeType == "daily":
                        timeStamp = datetime.datetime.strptime(str(rawLineSplit[0]),'%Y-%m-%d')
                        if startDate == None or (startDate <= timeStamp and endDate >= timeStamp):
                            timeStamps.append(timeStamp)
                            timeStampsEndInterval.append(timeStamp + datetime.timedelta(days=1))
                    else:
                        print("wtf")
                        timeStamps.append(-1)
                        
                        
                    dischargeData.append(float(rawLineSplit[3]))

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

def writeNetCDF(outputFile, GRDCData, timeScale):
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




   


    varDischarge = cdf.createVariable( "discharge", 'f4', ['time','site',], zlib=True, fill_value=-999.000 )
    varDischarge.units = "m3/s"
    varDischarge.coordinates = "lat lon"
    varDischarge.cell_methods = "mean"


    istart = -999
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
            for dayIndex in range(daysSinceRefTime,daysSinceRefTimeEndInterval):
                vartime[dayIndex] = netCDF4.date2num( GRDCData["timeStamps"][stationID][timeCounter], reference_date, calendar='standard' )
                varDischarge[dayIndex, stationCounter] = GRDCData["dischargeData"][stationID][timeCounter]

        stationCounter = stationCounter + 1


    # works because:
    # timestep is a day
    # reference time is in 'days since'
    vartime[...] = range(0, len(vartime)-1) # * dt==1
    
    return 1


if __name__ == "__main__":
    main()
