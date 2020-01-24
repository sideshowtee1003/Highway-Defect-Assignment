# Import modules
import arcpy
import getpass
import os
import glob
import time


# Create time variable
startTime = time.time()


print('Hello ' + getpass.getuser() + ', starting data preparation...')

# Set up variables:
# de05 variables
de05Input = "C:/Temp/Assignment/Source Data/de05 - Defects.xls/'de05 - Defects$'"
de05Event = "de05Event"
de05Lyr = "C:/Temp/Assignment/de05.lyr"
de05fc = "C:/Temp/Assignment/DefectInspections.gdb/de05"
de05Filter = "C:/Temp/Assignment/DefectInspections.gdb/de05v2"

# de02 variables
de02Input = "C:/Temp/Assignment/Source Data/de02.xls/de02$"
de02 = "de02Input" # feature class variable
defectGdb = "C:/Temp/Assignment/DefectInspections.gdb"

# Depots variables
depots = "C:/temp/Assignment/Source Data/shapefiles/depots.shp"
depotsCatchment = "C:/temp/Assignment/DefectInspections.gdb/depotsCatchment"

# Co-ordinate System
spatialRef = "Coordinate Systems/Projected Coordinate Systems/National Grids/Europe/British National Grid.prj"

# Chart Network
chartNetwork = "C:/temp/Assignment/DefectInspections.gdb/ChartNetwork"



# Prevents geoprocessing operations automatically being added to the table of contents (if GIS users run script within MXD)
arcpy.env.addOutputsToMap = 0



# Import base data (Includes Chart Network and depots):
# Set workspace to shapefile folder of source data 
arcpy.env.workspace = "C:/Temp/Assignment/Source Data/shapefiles"

# List all shapefiles (as feature class)
FCs=arcpy.ListFeatureClasses()

# Set Geoprocessing output overwrite to True
arcpy.env.overwriteOutput=True

# Loop through all shapefiles in folder (feature classes) and export them into Defect Inspections database
for fc in FCs:
    arcpy.FeatureClassToFeatureClass_conversion(fc,defectGdb,fc[:-4]) # -4 removes ".shp" suffix
    print("Import base data:" + fc[:-4] + " loaded into defect database")


print("Importing defect data...")
# Import and process de05 defects report:
# de05: Create XY event layer from de05 report
arcpy.MakeXYEventLayer_management(de05Input, "Easting", "Northing", de05Event, spatialRef)

# Set target workspace to GDB database
arcpy.env.workspace = defectGdb

# de05: Convert de05 report To Layer File
arcpy.SaveToLayerFile_management(de05Event, de05Lyr)

# de05: Copy features from de05 layer file to feature class
arcpy.CopyFeatures_management(de05Lyr, de05fc)

# de05: Create new version of de05 feature class with SQL expression filter for completed and superseded defects
arcpy.Select_analysis(de05fc, de05Filter, where_clause="Defect_Status <> 'COMPLETED' AND Defect_Status <> 'SUPERSEDED'")
print("Defect data imported and filtered to outstanding")


print("Starting data analysis...")
# Create depot catchment areas:
# Set the extent environment to ensure catchment areas (created next) cover the entire network (default setting didnt cover all network)
arcpy.env.extent = arcpy.Extent(395000, 375000, 526000, 486000)

# Create Thiessen Polygons for depots to create depot catchment areas for full network coverage
# *Requires business analyst desktop extension*
arcpy.CreateThiessenPolygons_analysis(depots, depotsCatchment, fields_to_copy="ALL")



# Calculate the responsible depot for each defect repair, using depot catchment areas:
# Create polygons to points spatial join
de05v3 = "C:/temp/Assignment/DefectInspections.gdb/de05v3"
arcpy.SpatialJoin_analysis(de05Filter, depotsCatchment, de05v3)

# Remove all unwanted fields automatically created from the spatial join
arcpy.DeleteField_management(de05v3, drop_field="Join_Count;TARGET_FID;Input_FID;OBJECTID_1;Easting_1;Northing_1")

# Rename new field for responsible depot for each defect repair
arcpy.AlterField_management(de05v3, field="DEPOT", new_field_name="Responsible_Depot")

# Testing: Responsible_Depot field has been successfully created:
if len(arcpy.ListFields(de05v3, "Responsible_Depot"))>0:
    print ("Responsible depot field successfully created")
else:
    print("Creating responsible depot field unsuccessful")



# Create Section, Chainage and Distance fields via linear referencing.  
# New fields will be created: 
# Section = Network reference 
# Chainage = Direction of travel distance from start of section
# DISTANCE = Defect location offset +/- offset from network line geometry
sectionRef = "FEATURE_LA" # Set section reference field variable
searchDist = "50 Meters" # Maximum search distance variable
linearRef = "C:/temp/Assignment/DefectInspections.gdb/de05RouteAnalysis" # Set linear referencing variable
props = "Section POINT Chainage" # Set properties variable for new fields
arcpy.LocateFeaturesAlongRoutes_lr(de05v3, chartNetwork, sectionRef, searchDist, linearRef, props,
									route_locations="FIRST", distance_field="DISTANCE", zero_length_events="ZERO", in_fields="NO_FIELDS",
									m_direction_offsetting="M_DIRECTON") # M direction offsets (direction of travel +/-) for calculating cross sectional position (XSP) later
# Linear referencing is required when carrying out repairs, operatives will not recognise/interpret XY co-ords.
# Operatives can look up section names on the produced output drawings and nodes painted on the road for start points of each chart section, to identify defect locations.

# Join newly created linear referencing table fields to defects feature class:
arcpy.JoinField_management(de05v3, in_field="OBJECTID", join_table=linearRef, join_field="INPUTOID", fields="Section;Chainage;Distance")



# Testing: Section field has been successfully created:
if len(arcpy.ListFields(de05v3, "Section"))>0:
    print ("Section field successfully created")
else:
    print("Creating section field unsuccessful")

# Testing: Chainage field has been successfully created:
if len(arcpy.ListFields(de05v3, "Chainage"))>0:
    print ("Chainage field successfully created")
else:
    print("Creating chainage field unsuccessful")

# Testing: Distance field has been successfully created:
if len(arcpy.ListFields(de05v3, "Distance"))>0:
    print ("Distance field successfully created")
else:
    print("Creating distance field unsuccessful")



# Calculate XSP:
# Join No_of_Lane field from ChartNetwork to defects feature class. This will be used in XSP calculations.
arcpy.JoinField_management(de05v3, in_field="Section", join_table="ChartNetwork", join_field="FEATURE_LA", fields="No_of_Lane")

# Set local variables
fieldName = "XSP"
expression = "CalcXSP(!Distance!, !No_of_Lane!)"
# Create CalcXSP function and set If Elif Else statement as a string variable. 
# The function uses the following assumptions: Hard shoulder exists everywhere, hard shoulder width = 3.3m, lane width = 3.6m
# No_of_Lane field is used to check how many lanes are present at that network location
xspCodeblock = """
def CalcXSP(Distance, No_of_Lane):
    if (Distance > 0 and Distance <= 3.3):
        return "Hard Shoulder"
    elif (Distance <= 0 and Distance >= -3.6):
        return "Lane 1"
    elif ('Distance < -3.6 and Distance >= -7.2' and No_of_Lane != "1L"):
        return "Lane 2"
    elif ('Distance < -7.2 and Distance >= -10.8' and 'No_of_Lane != "1L" and No_of_Lane != "2L"'):
        return "Lane 3"
    elif ('Distance < -10.8 and Distance >= -14.4' and 'No_of_Lane != "1L" and No_of_Lane != "2L" and No_of_Lane != "3L"'):
        return "Lane 4"
    else:
        return "Off Carriageway" """

# Create XSP field
arcpy.AddField_management(de05v3, fieldName, "STRING")
 
# Calculate XSP from previously defined variables
arcpy.CalculateField_management(de05v3, fieldName, expression, "PYTHON_9.3", xspCodeblock) # Insert If Elif Else statement string into python codeblock positional arg

# Delete unwanted fields following analysis
arcpy.DeleteField_management(de05v3, drop_field="No_of_Lane;Distance")

# Testing that XSP field has been successfully created:
if len(arcpy.ListFields(de05v3, "XSP"))>0:
    print ("XSP field successfully created")
else:
    print("Creating XSP field unsuccessful")



# Import and process de02 defects report:
# de02: Table to Table, xls to gdb
arcpy.TableToTable_conversion(de02Input, defectGdb, "de02")



# Link the two reports/feature classes for GIS users:
# Create relationship class between 'de05' feature class and 'de02' table, which contains additional inspection information
# The relationship is one to many because there may be multiple de02 rows per de05 feature.
de02FC = "C:/Temp/Assignment/DefectInspections.gdb/de02" # Create de02 feature class variable
relClass = "DefectInspections.gdb/DefectsRel"
forLabel = "Attributes from de02" # Sets de02 relationship label when inspecting features in GIS software
backLabel = "Attributes and Features from de05" # Sets de05 relationship label when inspecting features in GIS software
primaryKey = "Defect_Id"
foreignKey = "Defect_Id"
arcpy.CreateRelationshipClass_management(de05v3, de02FC, relClass, "SIMPLE", forLabel, 
					      backLabel, "NONE", "ONE_TO_MANY", 
					     "NONE", primaryKey, foreignKey)



# Add and Calculate field for setting the Display expression field for GIS end users
# The display expression defaults to the first field of string type that contains the text "name"
# More info: https://desktop.arcgis.com/en/arcmap/10.3/manage-data/tables/understanding-the-display-expression-for-a-field.htm
# de05:
arcpy.AddField_management(de05v3, "Display_Name", "STRING")
arcpy.CalculateField_management(de05v3, "Display_Name", "\"de05: \" & [Defect_Id]")
# de02:
arcpy.AddField_management(de02FC, "Display_Name", "STRING")
arcpy.CalculateField_management(de02FC, "Display_Name", "\"de02: \" & [Defect_Id]")

print("Data analysis complete. Beginning data display exports...")



# Displaying the Data to non-GIS users:
# Dissolve network on site name, to use as a data driven attribute
# Set local variables
networkDissolve = "C:/temp/Assignment/DefectInspections.gdb/NetworkDissolve"
dissolveField = "SITE_NAME"
# Run Dissolve tool
arcpy.Dissolve_management(chartNetwork, networkDissolve, dissolveField)

# Produce PNG outputs for non-GIS users/operatives:
# Data Driven pages are used based on SITE_NAME field
# Set MXD template for data driven pages 
mxd = arcpy.mapping.MapDocument("C:/temp/Assignment/Data Driven Template/Defects Data.mxd")

# Clear existing, superseded files in output folder
files = glob.glob("C:/temp/Assignment/outputPNGS/*")
for f in files:
    os.remove(f)

# Loop through data driven pages (37 in total), exporting each with specific page number and title
for pageNum in range(1, mxd.dataDrivenPages.pageCount + 1):  
  mxd.dataDrivenPages.currentPageID = pageNum # Page number ID to form part of file name
  print "Exporting page {0} of {1}".format(str(mxd.dataDrivenPages.currentPageID), str(mxd.dataDrivenPages.pageCount)) # Print for each loop item
  pageName = mxd.dataDrivenPages.pageRow.SITE_NAME # SITE_NAME attribute to form part of file name
  # Export to png at below file location (originally tried PDFs, but PNG exports completed quicker during testing)
  arcpy.mapping.ExportToPNG(mxd, "C:/temp/Assignment/outputPNGs/Page" + str(pageNum) + " - " + pageName + ".PNG", resolution=200) 
del mxd

print("Thank you " + getpass.getuser() + ", your output maps are saved in the following location: " + "C:/temp/Assignment/outputPNGs")



# Export new processed data into Excel for non-GIS users, split by responsible depot:
# Create variable for Excel outputs
depotXls = "C:/temp/Assignment/outputExcel/"

# Create variable for DefectbyDepot gdb
depotGdb = "C:/Temp/Assignment/DefectByDepot.gdb"

# Set target workspace to Depot GDB database
arcpy.env.workspace = depotGdb

# Split defect feature class into separate responsible depot feature classes
# I originally tried to acheive this through the arcpy.SplitByAttributes_analysis tool. I believe there might be a bug with using this tool in arcpy?
print("Splitting defects feature class by responsible depot...")
arcpy.Select_analysis(de05v3, "Ainley_Top", where_clause="Responsible_Depot = 'Ainley Top'")
arcpy.Select_analysis(de05v3, "Aston", where_clause="Responsible_Depot = 'Aston'")
arcpy.Select_analysis(de05v3, "Birdwell", where_clause="Responsible_Depot = 'Birdwell'")
arcpy.Select_analysis(de05v3, "Broughton", where_clause="Responsible_Depot = 'Broughton'")
arcpy.Select_analysis(de05v3, "Low_Marishes", where_clause="Responsible_Depot = 'Low Marishes'")
arcpy.Select_analysis(de05v3, "Normanton", where_clause="Responsible_Depot = 'Normanton'")
arcpy.Select_analysis(de05v3, "Shillinghill", where_clause="Responsible_Depot = 'Shillinghill'")
arcpy.Select_analysis(de05v3, "South_Cave", where_clause="Responsible_Depot = 'South Cave'")
arcpy.Select_analysis(de05v3, "Sprotborough", where_clause="Responsible_Depot = 'Sprotborough'")
arcpy.Select_analysis(de05v3, "Tingley", where_clause="Responsible_Depot = 'Tingley'")
arcpy.Select_analysis(de05v3, "West_Cowick", where_clause="Responsible_Depot = 'West Cowick'")

# List all feature classes in Depot gdb
depotFCs=arcpy.ListFeatureClasses()

# Loop through all depot feature classes and export them to excel output folder
for depotFC in depotFCs:
    print("Exporting " + depotFC + " defect spreadsheet to: " + "C:/temp/Assignment/outputExcel")
    arcpy.TableToExcel_conversion(depotFC,depotXls + depotFC + "_Defects.xls")



# Testing: Responsible_Depot created field values. Are any missing/empty?
print("Testing for missing Responsible_Depot values:")
with arcpy.da.SearchCursor(de05v3, ("Defect_Id", "Responsible_Depot")) as cursor:
    for row in cursor:
        # The filter function, filters each element of Responsible_Depot/row[1] field, testing if true or not.
        # Using "not" filter inverts this function. 
        # "None" tests empty/missing fields
        if not filter(None, row[1]):
            print "{} ----> EMPTY VALUE FOUND!".format(row[0])
        # This can be uncommented to print all successfully populated values:
        #else:
            #print "Defect_Id: " + str(row[0]) + " ----> " + str(row[1])
print("Testing for missing Responsible_Depot values completed")

# Testing: Section created field values. Are any missing/empty?
print("Testing for missing Section values:")
with arcpy.da.SearchCursor(de05v3, ("Defect_Id", "Section")) as cursor:
    for row in cursor:
        if not filter(None, row[1]):
            print "{} ----> EMPTY VALUE FOUND!".format(row[0])
        # This can be uncommented to print all successfully populated values:
        #else:
            #print "Defect_Id: " + str(row[0]) + " ----> " + str(row[1])
print("Testing for missing Section values completed")

# Testing: Chainage created field values. Are any null?
print("Testing for missing Chainage values:")
with arcpy.da.SearchCursor(de05v3, ("Defect_Id", "Chainage")) as cursor:
    for row in cursor:
        if row[1] is None: # "if not filter" did not work on double data type
            print "{} ----> EMPTY VALUE FOUND!".format(row[0])
        # This can be uncommented to print all successfully populated values:
        #else:
            #print "Defect_Id: " + str(row[0]) + " ----> " + str(row[1])
print("Testing for missing Chainage values completed")

# Testing: XSP created field values. Are any missing/empty?
print("Testing for missing XSP values:")
with arcpy.da.SearchCursor(de05v3, ("Defect_Id", "XSP")) as cursor:
    for row in cursor:
        if not filter(None, row[1]):
            print "{} ----> EMPTY VALUE FOUND!".format(row[0])
        # This can be uncommented to print all successfully populated values:
        #else:
            #print "Defect_Id: " + str(row[0]) + " ----> " + str(row[1])
print("Testing for missing XSP values completed")



# Delete superseded feature classes and tables:
# Create list of superseded fc/tables
deleteSS = [de05Lyr, de05fc, de05Filter, linearRef]
# Loop through list, deleting the files that are matched
for fcSS in deleteSS:
    print("Deleting superseded data: " + fcSS) # Print each deleted featureclass/table
    if arcpy.Exists(fcSS):
        arcpy.Delete_management(fcSS)

# Print time taken to run the script
print("Workflow complete in ", time.time() - startTime, " seconds")
