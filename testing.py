import arcpy
import getpass
print('Hello ' + getpass.getuser() + ', beginning field and values test...')


# Set feature class variable
DE05v3 = r"C:/temp/Assignment/DefectInspections.gdb/DE05v3"



# Testing that Responsible_Depot field has been successfully created:
if len(arcpy.ListFields(DE05v3, "Responsible_Depot"))>0:
    print ("Responsible depot field successfully created")
else:
    print("Creating responsible depot field unsuccessful")

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

# Testing that XSP field has been successfully created:
if len(arcpy.ListFields(DE05v3, "XSP"))>0:
    print ("XSP field successfully created")
else:
    print("Creating XSP field unsuccessful")



# Run testing on created field values:
# Responsible_Depot
print("Testing for missing Responsible_Depot values:")
with arcpy.da.SearchCursor(DE05v3, ("Defect_Id", "Responsible_Depot")) as cursor:
    for row in cursor:
        if not filter(None, row[1]):
            print "{} ----> EMPTY VALUE FOUND!".format(row[0])
        # This can be commented out to prevent all successfully populated values from printing:
        else:
            print "Defect_Id: " + str(row[0]) + " ----> " + str(row[1])
print("Testing for missing Responsible_Depot values completed")

# Section
print("Testing for missing Section values:")
with arcpy.da.SearchCursor(DE05v3, ("Defect_Id", "Section")) as cursor:
    for row in cursor:
        if not filter(None, row[1]):
            print "{} ----> EMPTY VALUE FOUND!".format(row[0])
        # This can be commented out to prevent all successfully populated values from printing:
        else:
            print "Defect_Id: " + str(row[0]) + " ----> " + str(row[1])
print("Testing for missing Section values completed")

# Chainage
print("Testing for missing Chainage values:")
with arcpy.da.SearchCursor(DE05v3, ("Defect_Id", "Chainage")) as cursor:
    for row in cursor:
        if row[1] is None: # "if not filter" did not work on integer data type
            print "{} ----> EMPTY VALUE FOUND!".format(row[0])
        # This can be commented out to prevent all successfully populated values from printing:
        else:
            print "Defect_Id: " + str(row[0]) + " ----> " + str(row[1])
print("Testing for missing Chainage values completed")

# XSP
print("Testing for missing XSP values:")
with arcpy.da.SearchCursor(DE05v3, ("Defect_Id", "XSP")) as cursor:
    for row in cursor:
        if not filter(None, row[1]):
            print "{} ----> EMPTY VALUE FOUND!".format(row[0])
        # This can be commented out to prevent all successfully populated values from printing:
        else:
            print "Defect_Id: " + str(row[0]) + " ----> " + str(row[1])
print("Testing for missing XSP values completed")