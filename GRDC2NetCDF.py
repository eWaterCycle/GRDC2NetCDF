#pre-processing of GRDC files into netCDF

import sys
import os
import re
import glob
import datetime

import netCDF4 as nc


#reads GRDC files from location, select station data valid in date selection
#TODO add function to provide netCDF mask file and only provide stations that are within mask
def readGRDC(inputLocation,startDate=None,endDate=None):

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
                dischargeData=[]
                for measurement in range(0, nrMeasurements):
                    rawLineSplit = allLines[41+measurement].split(";")
                    
                    if dataSetContent == "MEANMONTHLYDISCHARGE":
                        timeStamps.append(datetime.datetime.strptime(str(rawLineSplit[0]),'%Y-%m-00'))
                        
                    elif dataSetContent == "MEANDAILYDISCHARGE":
                        timeStamps.append(datetime.datetime.strptime(str(rawLineSplit[0]),'%Y-%m-%d'))
                    else:
                        timeStamps.append(-1)
                        print("Unknown dataSet type")
                        
                    dischargeData.append(float(rawLineSplit[2]))

                attributeGRDC["timeStamps"][str(id_from_grdc)] = timeStamps
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
            

            print("GRDC station "+str(id_from_file_name)+" ("+str(fileName)+") is used.")



    return attributeGRDC



def writeNetCDF(outputFile, GRDCData):
    #using a structure with GRDCData, create a netCDF file with time-series-objects

    return 1










# get arguments. this should be:
# 1. a directory with GRDC station data
# 2. a fileName of the netCDF file to save.
# 3. a startDate provided in YYYY-MM-DD
# 4. a endDate provided in YYYY-MM-DD


argument = sys.argv
print(argument)
print(argument[1])
#check for right number of arguments
if len(argument) == 5:
    startDate = argument[3]
    endDate = argument[4]
elif len(argument) == 3:
    startDate = None
    endDate = None
else:
    print("wrong number of arguments")
    sys.exit()

#two mandatory arguments
inputLocation = argument[1]
outputFile = argument[2]
print(type(inputLocation))
#make a structure with all GRDC data within 
# get GRDC attributes of all stations:
GRDCData = readGRDC(inputLocation,startDate,endDate)

writeNetCDF(outputFile, GRDCData)

  
