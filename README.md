# Search Index Parent

## Description
The Search Index Parent is a Python script designed to create and manage `search_index.xml` files for the current working directory (CWD) and the first level of subdirectories ("Parent" folders). It processes various file types including PDF, text, and log files, extracting their contents and creating XML files for easy search functionality. The script generates an accumulated `search_index.xml` file in the root directory (CWD) that includes all information from the `search_index.xml` files in the subdirectories.

## Features
- Processes PDF files and extracts text content.
- Processes text and log files, including their contents in the search index.
- Creates `search_index.xml` files for each directory and subdirectory.
- Generates an accumulated `search_index.xml` file in the root directory, aggregating all subdirectory indices.
- Includes versioning for better management and tracking.

## Usage

### Production
For production use:
1. Place the executable file in the base directory of the project you are processing.
   - For example, to use this for a "Closeout", place the executable file in the `Docs\` folder of the Auto play media studio project.
2. Run the executable file.
3. Ensure that there are no `search_index.xml` files already present in the directories, as this version does not delete any existing `search_index.xml` files and will append results to any existing file.
4. Upon successful completion, remove the executable file and the log file from the directory.

### Author
- Steve Fisher, MySmartPlans.com
- Email:steve.fisher@mysmartplans.com

