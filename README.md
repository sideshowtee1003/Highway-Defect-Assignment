# Python: Highways Defect Assignment and Automation

- This project aims to provide complete automation to A-One+/ Highways England's defect inspection data.
- This software was produced specifically for non-GIS users, however GIS users can also make good use.
- No GUI or toolbox has been produced for this software, as the majority of end users will have no specialist GIS and programming skills, knowledge or software.
- This software is to be fully automated (without anyone clicking a button) through windows task scheduler, providing end users with spatial and non-spatial outputs.
	- This provides massive company benefits by enabling the time saved to be spent by GIS and non-GIS users on alternate projects.
	- No specialist skills or software are required, as this automation will be run through A-One+/Highways GIS server, for end users.
- Outputs will be produced every day, with a constant refresh of data. This is necessary as A-One+/Highways England inspectors, inspect the network and capture data daily.
- Previously, there was poor visibilility of outstanding defects that require repair, poor assignment of maintenance depot responsiblity and lack of helpful location data for non-GIS users.
- Defect data is originally captured via x/y British National Grid co-ordinates:
	- However, within highways maintenance, the operatives carrying out repair, will not understand x/y locations on site.
	- This software sets out to assign these defects by network linear referencing, produce user friendly maps, to help operatives locate and prioritise these defects easily.
	- Linear referencing for highway maintenance includes:
		- Section: Network reference for specific section (marked by dotted paint on the roads)
		- Chainage: the distance (from direction of travel) from the start of the network section to the defect location.
		- Distance/offset: the distance in metres that the defect is located from the chart network sphapefile geometry.
		- XSP: (Cross sectional position) of the defect on the carriageway. Calulated from distance/offset and carriageway structure (number of lanes etc).
			- This cannot be 100% accurate, due to accuracy of the source data available: GPS coordinates, location of network strings (approx lane 1 left road marking) etc.
			- There are also limitations and assumptions made:
				- Hard shoulder exists network wide (lack of data to tell us otherwise)
				- Hard shoulder width = the average standard, 3.3m (lack of data to tell us otherwise)
				- Lane width = the average standard, 3.6m (lack of data to tell us otherwise)
- The software will also assign each defect to a specific depot, splitting the workload by geography.
- Spatial, user friendly map exports and non-spatial, processed, defect attribute exports are produced by this software.
- Databases, relationships, attribute & symbology configuration is also produced, to benefit GIS users aswell as non-GIS users.


## Getting Started and Installation

 - When developing this software, Python 2.7 was utilised as part of ArcMap 10.6, therefore this is recommended when running the code.
 - ArcGIS business analyst desktop extension is required for the thiessen polygon functionality within the code to work.
 - Running the Python files via double clicking the .bat files is recommended (or .py if your machine uses version 2.7 by default). However, they can be run by alternate methods, such as within an MXD.
 - When running via the .bat file. The main script takes approximately 4 minutes to run.
 - The following libraries are required for the code to work:
	- arcpy
	- os
	- glob
	- getpass
	
	
## Contents of GitHub directory

- The following includes a list of all files included within the GitHub repository for the software:
	- .gitattributes (default GitHub file)
	- LICENSE (GNU General Public License)
	- README.md (this documentation)
	- Script.py (python script containing the code for reading, processing and displaying spatial and non spatial data for defects and depots)
	- Run Script.bat (bat file, recommended to be used to run the above python script)
	- testing.py (a standalone python script, enabled to be run independantly, for testing purposes of fields and values. This same funcationality is found in "Script.py")
	- Run testing.bat (bat file, recommended to be used to run the above python testing script)
	- Run Readme.txt (brief readme info for running .bat files)
	- Defects Data.mxd (mapping document that the python code uses to set the data driven templates for data export display)
	- DefectInspections.gdb (file gdb where defect inspection datasets are stored and processed)
	- DefectByDepot.gdb (file gdb where depot specific, outstanding defect feature classes are stored)
	- Scheduler.bat (.bat file to be used within windows task scheduler, for fully autmomated daily workflow)
	- Scheduler Readme.txt (a brief note for task scheduler)
	- ScheduleTask.JPG (screenshot demonstrating windows task scheduler set up)
	- outputExcel (file directory used to store excel spreadsheet outputs)
	- outputPNGs (file directory used to store PNG map outputs)
	- Source Data, which includes the following:
		- DE05 - Defects.xls
		- DE02.xls
		- ChartNetwork.shp
		- Depots.shp
		

## Running the model

- For testing/marking purposes, running the python files via double clicking the .bat files is recommended.
	- In reality, these will be run automatically via windows task scheduler on the A-One+/Highways England's GIS server, producing automated daily outputs for non-GIS end users.
- For testing/marking purposes, all files taken from github repository should adhere to the set file hierarchy and be saved in the following location: C:\temp\Assignment
	- In reality, all files will be saved on the A-One+/Highways England's GIS server.
	
	
## The Model: Behind the Scenes

- The code will read in the source data, listed in the contents.
- The code will create and calculate new fields for a newly created outstanding defect feature class: Responsible_Depot, Display_Name, Section, Chainage, XSP.
- Thiessen polygons will be used to create depot catchment areas, which are joined to the new defect feature class.
- Database relationships are set up between the DE02 and DE05 reporting information.
- The code uses data driven pages to produce maps by specific site locations (37 in total, to cover the whole network)
- Non-spatial, processed excel spreadsheets are produced to accompany spatial outputs, split by responsible depot.

	
	
## Testing

- Automated testing is set up in the code to ensure the software is working and processing data as expected. If running manually, testing will be printed to the console.
- A standalone testing.py script is included if wanting to run field and value tests independant of main code (However, these same tests are included in the main code).
	- All newly created fields are tested within the code to ensure they have been successfully/unsuccessfully created.
	- All newly created values are tested within the code to ensure they have been successfully/unsuccessfully created.
- The main script testing and independant testing script differ slightly, as the main script has certain elements of the code, commented out.
	- The main script will only print tests for value checks, if it fails to find a value (missing attribute)
	- The independant testing script will print all tests for value checks, whether it finds a value or not.
	
## License

This project is licensed under the GNU License - see the LICENSE file in the following location for details: https://github.com/sideshowtee1003/Agent-Based-Modelling/blob/master/LICENSE


## Author

- **Thomas Coleman** : 
	-(https://github.com/sideshowtee1003) GitHub Profile Page
