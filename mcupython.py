#mcupython.py
#
# new main file
from dataclasses import dataclass, field
import sys
import signal
import threading
import atexit
import time
from time import perf_counter

from hackiemackieutils import print_debug,UtilityConfig as setup
import mcuconfigfile
import mido

CONFIG_FILE = "config.txt"
PORT_TIMEOUT = 2.0

@dataclass
class IOPorts:
	open_ports = False
	output = ""
	output_virt = ""
	multi_input:list = field(init=False)

	def __post_init__(self):
		self.multi_input = []

midi_ports_open = False

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

def load_config(filename,ports):
	#async def connect_ports(ports, midi_ports):
	time.sleep(1)
	
	port_names = ['IAC Driver HackieMackie IN',
	'IAC Driver HackieMackie OUT',
	'IAC Driver Streamdeck',
	'Network ipad network']
	print_debug(f"In connect...",1)
	for p in port_names:
		with mido.open_input(p) as port:
			print_debug(f"Opening {port=}")
			ports.multi_input.append(port)
			print_debug(f"{port.name}, {port.closed=}",1)
	
	print_debug(f"Connections open...",1)
	time.sleep(4)
	ports.open_ports = True
	time.sleep(4)


def check_time():
	print_debug("Checking..")
	

def quit_handler(sig, frame):
	print_debug(f"")
	print_debug("Ctrl-C pressed", 1)
	print_debug("HackieMackie Terminating...", 1)
	sys.exit(0)

def close_ports(*ports):
	print_debug(f"Cleaning up...closing ports...",2)
	for port in ports:
			print_debug(f"Closing {port=} ...",2)
			port.close()
			print_debug(f"{port.name} closed: {port.closed}",2)
	


def main(*args)->None:
	"""Main sets up configuration with conf class"""
	"""Main loop ONLY loops midi and ONLY runs methods"""
	#print("Init? Where?")
	setup.debug_mode = 1
	ports = IOPorts()
	# atexit.register(close_ports,ports.output, ports.output_virt, *ports.multi_input)
	signal.signal(signal.SIGINT, quit_handler)
	atexit.register(close_ports, *ports.multi_input)
	start = perf_counter()
	# multithreading load to be able to kill the program if we can't open the portss we need
	t = threading.Thread(target=load_config, args=(CONFIG_FILE,ports), daemon=True)
	
	# if(not validate_config()):
	# 	print_debug(f"Configuration file not valid. Check settings.")
	# 	return False
	# try:
	# 	t.start()
	# except(KeyboardInterrupt, SystemExit):
	# 	print_debug("Thread aborted!")
	# 	sys.exit()
	t.start()
	#print(ports.open_ports)
	while(not ports.open_ports):
		time.sleep(0.2)
		#check_time()
		end = time.perf_counter()-start
		if(end >= PORT_TIMEOUT):
			print_debug(f"It took too long to connect! {end}")
			sys.exit(0)
	print("Out of while")
	t.join()
	
	#mcuconfigfile.create_empty_config(CONFIG_FILE,True)
	pass
if __name__ == "__main__":
	main(*sys.argv[1:])