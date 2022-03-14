#mcupython.py
#
# new main file
from dataclasses import dataclass, field
from sqlite3 import connect
import sys
import signal
import threading
import atexit
import time
from time import perf_counter

from hackiemackieutils import print_debug,UtilityConfig as setup
import mcuconfigfile
from mcuconfigfile import Configuration as conf
import mido

CONFIG_FILE = "config.txt"
PORT_TIMEOUT = 3.0

connection_barrier = threading.Barrier(parties=2, timeout=5.0)

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
	mcuconfigfile.load_midiconfig()

	print_debug(f"Opening ports..",1)
	ports.output = mido.open_output(conf.midi_output_hw)
	print_debug(f"{ports.output=}",1)
	ports.output_virt = mido.open_output(conf.midi_output_daw)
	print_debug(f"{ports.output_virt=}",1)
	ports.multi_input = [mido.open_input(i) for i in conf.midi_input_devices]
	print_debug(f"{ports.multi_input=}",1)
	
	connection_barrier.wait()
	print_debug(f"Connections open...",1)
	ports.open_ports = True


def check_time():
	print_debug("Checking..")
	

def quit_handler(sig, frame):
	print_debug(f"")
	print_debug("Ctrl-C pressed", 1)
	print_debug("HackieMackie Terminating...", 1)
	sys.exit(0)


def close_ports(*ports):
	# print_debug(f"{ports}")
	print_debug(f"Cleaning up...closing ports...",1)
	for port in ports:
			print_debug(f"Closing {port.name=}...",1)
			port.close()
			print_debug(f"{port.name} closed: {port.closed}",1)
	


def main(*args)->None:
	"""Main sets up configuration with conf class"""
	"""Main loop ONLY loops midi and ONLY runs methods"""
	#print("Init? Where?")
	setup.debug_mode = 1
	ports = IOPorts()
	# atexit.register(close_ports,ports.output, ports.output_virt, *ports.multi_input)
	signal.signal(signal.SIGINT, quit_handler)
	# atexit.register(close_ports, ports.output, ports.output_virt,*ports.multi_input)
	start = perf_counter()
	# multithreading load to be able to kill the program if we can't open the portss we need
	t = threading.Thread(target=load_config, args=(CONFIG_FILE,ports), daemon=True)


	if(not validate_config()):
		print_debug(f"Configuration file not valid. Check settings.")
		return False
	
	# try:
	# 	t.start()
	# except(KeyboardInterrupt, SystemExit):
	# 	print_debug("Thread aborted!")
	# 	sys.exit()
	try:
		t.start()
	# #print(ports.open_ports)
	# while(not ports.open_ports):
	# 	time.sleep(0.2)
	# 	#check_time()
	# 	end = time.perf_counter()-start
	# 	if(end >= PORT_TIMEOUT):
	# 		print_debug(f"It took too long to connect! {end}")
	# 		sys.exit(0)
		connection_barrier.wait()
	except threading.BrokenBarrierError as e:
		connection_barrier.abort()
		print_debug("MIDI port timed out...verify that devices are connected and try again...",1)
		sys.exit(0)
	# t.join()

	atexit.register(close_ports, ports.output, ports.output_virt,*ports.multi_input)

	print_debug("Waiting for MIDI... Press Ctrl-C to abort...", 1)

	for port, msg, in mido.ports.multi_receive(ports.multi_input, yield_ports=True, block=True):
		match(port):
			case [conf.midi_input_debug]:
				print_debug(f"Debug port",1)
				print_debug(f"{msg}",1)
			case [conf.midi_input_daw]:
				print_debug(f"DAW port",1)
			case [conf.midi_input_hw]:
				print_debug(f"HW port",1)
		match(msg):
			case mido.messages.messages.Message(note=mValue):
				print_debug(f"{port.name}:note({mValue}:{msg}",1)
			case mido.messages.messages.Message(type="sysex", data=_):
				print_debug(f"{port.name}:sysex:{msg}",1)
			case mido.messages.messages.Message(type="control_change"):
				print_debug(f"{port.name}:cc:{msg}",1)
			case other:
				pass
				#print(f"Other type...{other}")
	
	#mcuconfigfile.create_empty_config(CONFIG_FILE,True)
	pass
if __name__ == "__main__":
	main(*sys.argv[1:])