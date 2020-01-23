# Import modules
import arcpy
import getpass
import os
import glob
print('Hello ' + getpass.getuser() + ', starting data preparation...')


# Set up variables:
# DE05 variables
DE05_input = "C:/Temp/Assignment/Source Data/DE05 - Defects.xls/'DE05 - Defects$'"
DE05_event = "DE05_event"
DE05_lyr = "C:/Temp/Assignment/DE05.lyr"
DE05_fc = "C:/Temp/Assignment/DefectInspections.gdb/DE05"
DE05_filter = "C:/Temp/Assignment/DefectInspections.gdb/DE05v2"

# DE02 variables
DE02_input = "C:/Temp/Assignment/Source Data/DE02.xls/DE02$"
DE02 = "DE02_input" # feature class variable
Defect_gdb = "C:/Temp/Assignment/DefectInspections.gdb"

# Depots variables
Depots = "C:/temp/Assignment/Source Data/shapefiles/Depots.shp"
Depots_Catchment = "C:/temp/Assignment/DefectInspections.gdb/Depots_Catchment"

# Co-ordinate System
SpatialRef = "Coordinate Systems/Projected Coordinate Systems/National Grids/Europe/British National Grid.prj"

# Chart Network
Chart_Network = "C:/temp/Assignment/DefectInspections.gdb/ChartNetwork"



# Prevents geoprocessing operations automatically being added to the table of contents (if GIS users run script within MXD)
arcpy.env.addOutputsToMap = 0



# Import base data (Includes Chart Network and Depots):
# Set workspace to shapefile folder of source data 
arcpy.env.workspace = "C:/Temp/Assignment/Source Data/shapefiles"

# List all shapefiles (as feature class)
FCs=arcpy.ListFeatureClasses()

# Set Geoprocessing output overwrite to True
arcpy.env.overwriteOutput=True

# Loop through all shapefiles in folder (feature classes) and export them into Defect Inspections database
for fc in FCs:
    arcpy.FeatureClassToFeatureClass_conversion(fc,Defect_gdb,fc[:-4]) # -4 removes ".shp" suffix
    print("Import base data:" + fc[:-4] + " loaded into defect database")

# Import and process DE05 defects report:
# DE05 Process: Make XY Event Layer
arcpy.MakeXYEventLayer_management(DE05_input, "Easting", "Northing", DE05_event, SpatialRef)

# Set target workspace to GDB database
arcpy.env.workspace = Defect_gdb

# DE05 Process: Save To Layer File
arcpy.SaveToLayerFile_management(DE05_event, DE05_lyr)

# DE05 Process: Copy Features
arcpy.CopyFeatures_management(DE05_lyr, DE05_fc)

# DE05 Process: Create new version of feature class with SQL expression filter for completed and superseded defects
arcpy.Select_analysis(DE05_fc, DE05_filter, where_clause="Defect_Status <> 'COMPLETED' AND Defect_Status <> 'SUPERSEDED'")



# Create Catchment Areas:
# Set the extent environment to ensure catchment areas (created next) cover the entire network
arcpy.env.extent = arcpy.Extent(395000, 375000, 526000, 486000)

# Create Thiessen Polygons for Depots to create Depot catchment areas for full network coverage
# *Requires business analyst desktop extension*
arcpy.CreateThiessenPolygons_analysis(Depots, Depots_Catchment, fields_to_copy="ALL")



# Calculate the responsible depot for each defect repair, using depot catchment areas:
# Create polygons to points spatial join
DE05v3 = "C:/temp/Assignment/DefectInspections.gdb/DE05v3"
arcpy.SpatialJoin_analysis(DE05_filter, Depots_Catchment, DE05v3)

# Remove all unwanted fields automatically created from the spatial join
arcpy.DeleteField_management(DE05v3, drop_field="Join_Count;TARGET_FID;Input_FID;OBJECTID_1;Easting_1;Northing_1")

# Rename new field for responsible depot for each defect repair
arcpy.AlterField_management(DE05v3, field="DEPOT", new_field_name="Responsible_Depot")

# Testing that Responsible_Depot field has been successfully created:
if len(arcpy.ListFields(DE05v3, "Responsible_Depot"))>0:
    print ("Responsible depot field successfully created")
else:
    print("Creating responsible depot field unsuccessful")



# Create Section, Chainage and Distance fields via linear referencing.  
# New fields will be created: 
# Section = Network reference 
# Chainage = Direction of travel distance from start of section
# DISTANCE = Defect location offset +/- from network
Section_ref = "FEATURE_LA" # Set section reference field variable
Search_dist = "50 Meters" # Maximum search distance variable
Linear_ref = "C:/temp/Assignment/DefectInspections.gdb/DE05RouteAnalysis" # Set linear referencing variable
Props = "Section POINT Chainage" # Set properties variable for new fields
arcpy.LocateFeaturesAlongRoutes_lr(DE05v3, Chart_Network, Section_ref, Search_dist, Linear_ref, Props,
									route_locations="FIRST", distance_field="DISTANCE", zero_length_events="ZERO", in_fields="NO_FIELDS",
									m_direction_offsetting="M_DIRECTON") # M direction offsets (direction of travel +/-) for calculating cross sectional position (XSP) later
# Linear referencing is required when carrying out repairs, operatives will not recognise/interpret XY co-ords.
# Operatives can look up section names on the produced output drawings and nodes painted on the road for start points of each chart section, to identify defect locations.

# Join newly created linear referencing table fields to defects feature class:
arcpy.JoinField_management(DE05v3, in_field="OBJECTID", join_table=Linear_ref, join_field="INPUTOID", fields="Section;Chainage;Distance")

# Testing that Section field has been successfully created:
if len(arcpy.ListFields(DE05v3, "Section"))>0:
    print ("Section field successfully created")
else:
    print("Creating section field unsuccessful")

# Testing that Chainage field has been successfully created:
if len(arcpy.ListFields(DE05v3, "Chainage"))>0:
    print ("Chainage field successfully created")
else:
    print("Creating chainage field unsuccessful")

# Testing that Distance field has been successfully created:
if len(arcpy.ListFields(DE05v3, "Distance"))>0:
    print ("Distance field successfully created")
else:
    print("Creating distance field unsuccessful")


# Calculate XSP:
# Join No_of_Lane field from ChartNetwork to defects feature class. This will be used in XSP calculations.
arcpy.JoinField_management(DE05v3, in_field="Section", join_table="ChartNetwork", join_field="FEATURE_LA", fields="No_of_Lane")

# Set local variables
fieldName = "XSP"
expression = "CalcXSP(!Distance!, !No_of_Lane!)"
# Set If Elif Else statement as a string variable
XSPcodeblock = """
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
arcpy.AddField_management(DE05v3, fieldName, "STRING")
 
# Calculate XSP from variables
arcpy.CalculateField_management(DE05v3, fieldName, expression, "PYTHON_9.3", XSPcodeblock) # Insert If Elif Else statement string into python codeblock

# Delete unwanted fields following analysis
arcpy.DeleteField_management(DE05v3, drop_field="No_of_Lane;Distance")

# Testing that XSP field has been successfully created:
if len(arcpy.ListFields(DE05v3, "XSP"))>0:
    print ("XSP field successfully created")
else:
    print("Creating XSP field unsuccessful")



# Import and process DE02 defects report:
# DE02 Process: Table to Table
arcpy.TableToTable_conversion(DE02_input, Defect_gdb, "DE02")



# Link the two reports/feature classes:
# Create relationship class between 'DE05' feature class and 'DE02' table with additional inspection information
DE02_fc = "C:/Temp/Assignment/DefectInspections.gdb/DE02" # Create DE02 feature class variable
relClass = "DefectInspections.gdb/DefectsRel"
forLabel = "Attributes from DE02"
backLabel = "Attributes and Features from DE05"
primaryKey = "Defect_Id"
foreignKey = "Defect_Id"
arcpy.CreateRelationshipClass_management(DE05v3, DE02_fc, relClass, "SIMPLE", forLabel, 
					      backLabel, "NONE", "ONE_TO_MANY", 
					     "NONE", primaryKey, foreignKey)


# Add and Calculate field for setting the Display Expression field for GIS end users
# The display expression defaults to the first field of string type that contains the text "name"
# More info: https://desktop.arcgis.com/en/arcmap/10.3/manage-data/tables/understanding-the-display-expression-for-a-field.htm
# DE05:
arcpy.AddField_management(DE05v3, "Display_Name", "STRING")
arcpy.CalculateField_management(DE05v3, "Display_Name", "\"DE05: \" & [Defect_Id]")
# DE02:
arcpy.AddField_management(DE02_fc, "Display_Name", "STRING")
arcpy.CalculateField_management(DE02_fc, "Display_Name", "\"DE02: \" & [Defect_Id]")


print("Data analysis complete. Beginning data display exports...")



# Displaying the Data to non-GIS users:
# Dissolve network on site name, to use as a data driven attribute
# Set local variables
Network_Dissolve = "C:/temp/Assignment/DefectInspections.gdb/NetworkDissolve"
Dissolve_Field = "SITE_NAME"
# Run Dissolve tool
arcpy.Dissolve_management(Chart_Network, Network_Dissolve, Dissolve_Field)



# Produce PNG outputs for non-GIS users/operatives (originally tried PDFs, but PNG exports completed quicker during testing):
# Data Driven pages are used based on SITE_NAME field
# Set MXD template for data driven pages 
mxd = arcpy.mapping.MapDocument("C:/temp/Assignment/Data Driven Template/Defects Data.mxd")

# Clear existing files in output folder
files = glob.glob(r'C:/temp/Assignment/outputPNGS/*')
for f in files:
    os.remove(f)

# Loop through data driven pages (37 in total), exporting each with specific page number and title
for pageNum in range(1, mxd.dataDrivenPages.pageCount + 1):  
  mxd.dataDrivenPages.currentPageID = pageNum # Page number ID to be input into file name 
  print "Exporting page {0} of {1}".format(str(mxd.dataDrivenPages.currentPageID), str(mxd.dataDrivenPages.pageCount))
  pageName = mxd.dataDrivenPages.pageRow.SITE_NAME # Enables title to be input into file name
  arcpy.mapping.ExportToPNG(mxd, "C:/temp/Assignment/outputPNGs/Page" + str(pageNum) + " - " + pageName + ".PNG", resolution=200) 
del mxd

print("Thank you " + getpass.getuser() + ", your output maps are saved in the following location: " + "C:/temp/Assignment/outputPNGs")



# Export new processed data into Excel for non-GIS users, split by responsible depot:
# Create variable for Excel outputs
Depot_xls = "C:/temp/Assignment/outputExcel/"

# Create variable for DefectbyDepot gdb
Depot_gdb = "C:/Temp/Assignment/DefectByDepot.gdb"

# Set target workspace to Depot GDB database
arcpy.env.workspace = Depot_gdb

# Split defect feature class into separate responsible depot feature classes
# I originally tried to acheive this through the arcpy.SplitByAttributes_analysis tool. I believe there might be a bug with using this tool in arcpy?
print("Splitting defects feature class by responsible depot...")
arcpy.Select_analysis(DE05v3, "Ainley_Top", where_clause="Responsible_Depot = 'Ainley Top'")
arcpy.Select_analysis(DE05v3, "Aston", where_clause="Responsible_Depot = 'Aston'")
arcpy.Select_analysis(DE05v3, "Birdwell", where_clause="Responsible_Depot = 'Birdwell'")
arcpy.Select_analysis(DE05v3, "Broughton", where_clause="Responsible_Depot = 'Broughton'")
arcpy.Select_analysis(DE05v3, "Low_Marishes", where_clause="Responsible_Depot = 'Low Marishes'")
arcpy.Select_analysis(DE05v3, "Normanton", where_clause="Responsible_Depot = 'Normanton'")
arcpy.Select_analysis(DE05v3, "Shillinghill", where_clause="Responsible_Depot = 'Shillinghill'")
arcpy.Select_analysis(DE05v3, "South_Cave", where_clause="Responsible_Depot = 'South Cave'")
arcpy.Select_analysis(DE05v3, "Sprotborough", where_clause="Responsible_Depot = 'Sprotborough'")
arcpy.Select_analysis(DE05v3, "Tingley", where_clause="Responsible_Depot = 'Tingley'")
arcpy.Select_analysis(DE05v3, "West_Cowick", where_clause="Responsible_Depot = 'West Cowick'")

# List all feature classes in Depot gdb
DepotFCs=arcpy.ListFeatureClasses()

# Loop through all depot feature classes and export them to excel output folder
for Depotfc in DepotFCs:
    print("Exporting " + Depotfc + "defect spreadsheet to: " + "C:/temp/Assignment/outputExcel")
    arcpy.TableToExcel_conversion(Depotfc,Depot_xls + Depotfc + "_Defects.xls")



# Run testing on created field values:
# Responsible_Depot
print("Testing for missing Responsible_Depot values:")
with arcpy.da.SearchCursor(DE05v3, ("Defect_Id", "Responsible_Depot")) as cursor:
    for row in cursor:
        if not filter(None, row[1]):
            print "{} ----> EMPTY VALUE FOUND!".format(row[0])
        # This can be uncommented to print all successfully populated values:
        #else:
            #print "Defect_Id: " + str(row[0]) + " ----> " + str(row[1])
print("Testing for missing Responsible_Depot values completed")

# Section
print("Testing for missing Section values:")
with arcpy.da.SearchCursor(DE05v3, ("Defect_Id", "Section")) as cursor:
    for row in cursor:
        if not filter(None, row[1]):
            print "{} ----> EMPTY VALUE FOUND!".format(row[0])
        # This can be uncommented to print all successfully populated values:
        #else:
            #print "Defect_Id: " + str(row[0]) + " ----> " + str(row[1])
print("Testing for missing Section values completed")

# Chainage
print("Testing for missing Chainage values:")
with arcpy.da.SearchCursor(DE05v3, ("Defect_Id", "Chainage")) as cursor:
    for row in cursor:
        if row[1] is None: # "if not filter" did not work on integer data type
            print "{} ----> EMPTY VALUE FOUND!".format(row[0])
        # This can be uncommented to print all successfully populated values:
        #else:
            #print "Defect_Id: " + str(row[0]) + " ----> " + str(row[1])
print("Testing for missing Chainage values completed")


# XSP
print("Testing for missing XSP values:")
with arcpy.da.SearchCursor(DE05v3, ("Defect_Id", "XSP")) as cursor:
    for row in cursor:
        if not filter(None, row[1]):
            print "{} ----> EMPTY VALUE FOUND!".format(row[0])
        # This can be uncommented to print all successfully populated values:
        #else:
            #print "Defect_Id: " + str(row[0]) + " ----> " + str(row[1])
print("Testing for missing XSP values completed")



# Delete superseded feature classes and tables:
# Create list of superseded fc/tables
Delete_SS = [DE05_lyr, DE05_fc, DE05_filter, Linear_ref]
# Loop through list, deleting the files that are matched
for fc_SS in Delete_SS:
    print("Deleting superseded data: " + fc_SS)
    if arcpy.Exists(fc_SS):
        arcpy.Delete_management(fc_SS)
