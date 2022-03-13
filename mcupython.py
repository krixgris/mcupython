#mcupython.py
#
# new main function ? launches hackiemackie? viable?
# collects configuration settings, sets environment up, cleaner, easier to follow?
# in gitignore for now..
import sys

from hackiemackieutils import print_debug,UtilityConfig as setup
import mcuconfigfile
import mido

CONFIG_FILE = "config.txt"

def validate_config()->tuple():
	is_valid = True
	file_exists = False
	try:
		file = open(CONFIG_FILE,"r")
		file.close()
		file_exists = True
	except FileNotFoundError as e:
		print_debug(f"{e}",0)
		mcuconfigfile.create_empty_config(CONFIG_FILE)
		print_debug(f"config.txt file will be created, open the file and verify settings...",0)
	if(not file_exists):
		return file_exists

	is_valid = mcuconfigfile.validate_config_file(CONFIG_FILE)

	return is_valid

def load_config(filename):
	pass
	
	

def main(*args)->None:
	"""Main sets up configuration with conf class"""
	"""Main loop ONLY loops midi and ONLY runs methods"""
	#print("Init? Where?")
	setup.debug_mode = 1

	if(not validate_config()):
		print_debug(f"Configuration file not valid. Check settings.")
		return False
		
	
	#mcuconfigfile.create_empty_config(CONFIG_FILE,True)
	pass
if __name__ == "__main__":
	main(*sys.argv[1:])