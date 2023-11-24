import os

# Get the current working directory
current_directory = os.getcwd()

# List all files in the directory
all_files = os.listdir(current_directory)

# Filter files that start with "LEO"
leo_files  = ["test_%03d.dxf" % x for x in list(range(1,154))]

# Print the list of LEO files
for file in sorted(leo_files):
	file_path = "LEO_"+file
	if not os.path.exists(file_path):
		print(f"The file {file_path} does not exist.")


