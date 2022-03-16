#mcupython.py
#
# new main file
from contextlib import ExitStack
from dataclasses import dataclass, field
from multiprocessing import Value
from sqlite3 import connect
import sys
import signal
import threading
import concurrent.futures

import atexit
import time
from time import perf_counter
from tkinter import E

from hackiemackieutils import print_debug,UtilityConfig as setup
import mcuconfigfile
from mcuconfigfile import Configuration as conf
import mido

CONFIG_FILE = "config.txt"
PORT_TIMEOUT = 3.0

connection_barrier = threading.Barrier(parties=2, timeout=5.0)

def to_14bit(v:int)->tuple:
	if(v>16383):
		v = 16383
	elif(v<=3):
		v = 0
	cc1 = int(bin(v>>7),2)
	cc2 = int(bin(v&127),2)

	return (cc1,cc2)

def from_14bit(cc1,cc2)->int:
	return (cc1<<7|cc2)

@dataclass
class IOPorts:
	open_ports = False
	output = ""
	output_virt = ""
	multi_input:list = field(init=False)

	def __post_init__(self):
		self.multi_input = []

conf_ports = IOPorts()

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

def load_config(filename,ports)->bool:
	print_debug(f"Opening ports..",1)
	ports.output = mido.open_output(conf.midi_output_hw)
	print_debug(f"{ports.output=}",1)
	ports.output_virt = mido.open_output(conf.midi_output_daw)
	print_debug(f"{ports.output_virt=}",1)
	for i in conf.midi_input_devices:
		#time.sleep(0.1)
		ports.multi_input.append(mido.open_input(i))
		time.sleep(0.1)
	# # ports.multi_input = [mido.open_input(i) for i in conf.midi_input_devices]
	print_debug(f"{ports.multi_input=}",1)
	
	# connection_barrier.wait()
	time.sleep(1)
	print_debug(f"{ports=}")
	print_debug(f"Connections open...",1)
	ports.open_ports = True

	#return True
	#return conf_ports
	return True


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
	del ports
	
def stop_process_pool(executor):
	for pid, process in executor._processes.items():
		process.terminate()
	executor.shutdown()
	sys.exit(0)

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
	else:
		print(f"{conf}")
	try:
		mcuconfigfile.load_midiconfig()
	except KeyError as e:
		print_debug(f"Config file broken..{e} not found.",1)
	print(ports)
	
	# # try:
	# # 	t.start()
	# # except(KeyboardInterrupt, SystemExit):
	# # 	print_debug("Thread aborted!")
	# # 	sys.exit()
	# try:
	# 	t.start()
	# # #print(ports.open_ports)
	# # while(not ports.open_ports):
	# # 	time.sleep(0.2)
	# # 	#check_time()
	# # 	end = time.perf_counter()-start
	# # 	if(end >= PORT_TIMEOUT):
	# # 		print_debug(f"It took too long to connect! {end}")
	# # 		sys.exit(0)
	# 	connection_barrier.wait()
	# except threading.BrokenBarrierError as e:
	# 	connection_barrier.abort()
	# 	print_debug("MIDI port timed out...verify that devices are connected and try again...",1)
	# 	sys.exit(0)
	# # t.join()
	#temp_conf = conf()

	#print(f"New temp conf:{temp_conf}")

	with concurrent.futures.ThreadPoolExecutor() as executor:
		#p = executor.submit(load_config, (CONFIG_FILE,ports))
		try:
			f = executor.submit(check_time)
			#for future in concurrent.futures.as_completed(f,timeout=2):
			#file_loaded = f.result(timeout=2)
			load_config(CONFIG_FILE, ports)
			f.result(timeout=2)
			# if(not file_loaded):
			# 	sys.exit(0)
		except concurrent.futures._base.TimeoutError:
			print("This took to long...")
			stop_process_pool(executor)
	#ports = conf_ports
	print(f"{ports=}")
	print(f"{conf_ports=}")
	# load_config(CONFIG_FILE,ports, conf)


	atexit.register(close_ports, ports.output, ports.output_virt,*ports.multi_input)

	print_debug("Waiting for MIDI... Press Ctrl-C to abort...", 1)

	# ports.multi_input.append(mido.open_input(i))
	
	# with mido.open_input(conf.midi_input_daw) as daw, \
	# 	 mido.open_input(conf.midi_input_hw) as hw:
				#mido.open_input(conf.midi_input_debug) as debug:

		# for msg in daw:
		# 	for msg in hw:
		# 		print(msg)
		# 	print(msg)
		# for msg in daw:
		# 	print(msg)

		# for msg in debug:
		# 	print(msg)

	# midi_input_list = []
	# #conf.midi_input_devices = ['Arturia KeyStep 32']
	# #print(f"asdfasdfasdf {conf.midi_input_hw}")
	# with ExitStack() as midi_stack:
	# 	for midi_input in conf.midi_input_devices:
	# 		print(f"{conf.midi_input_devices=}")
	# 	midi_input_list.append(midi_stack.enter_context(mido.open_input(midi_input)))
	# 	print(midi_input_list)
	# 	for port,msg in mido.ports.multi_receive(midi_input_list, yield_ports=True, block=True):
	# 		print(f"{port=}")
	# 		for msg in port:
	# 			print(f"{port=},{msg=}")
	# 		print("never gets here")

	cc1msg_return = mido.Message('control_change', control=12, channel=0, value=123)
	cc2msg_return = mido.Message('control_change', control=44, channel=0, value=123)
	pitchmsg_volume = mido.Message('pitchwheel', channel=0, pitch=8023)
	cc1arrived = False
	cc1val = 0
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
				if(msg.control==12 and port.name == conf.midi_input_daw):
					#cc1arrived = True
					cc1val = msg.value
					#print("True!")
				if(msg.control==44 and port.name == conf.midi_input_daw):
					cc2msg_return.value = msg.value
					pitchmsg_volume.pitch = from_14bit(cc1val, cc2msg_return.value)-8192
					ports.output.send(pitchmsg_volume)

			case mido.messages.messages.Message(type="pitchwheel"):
				#print_debug(f"{port.name}:cc:{msg}",1)
				# print_debug(f"{port.name}:pw:{msg}",1)
				cc1msg = mido.Message('control_change', control=12, channel=0, value=123)
				cc2msg = mido.Message('control_change', control=44, channel=0, value=123)
				print(msg.pitch+8192+3)
				cc1msg.value, cc2msg.value = to_14bit(msg.pitch+8192+3)
				
				ports.output_virt.send(cc2msg)
				ports.output_virt.send(cc1msg)
				

				
			case other:
				pass
				print(f"Other type...{other}")
	
	#mcuconfigfile.create_empty_config(CONFIG_FILE,True)
	pass
if __name__ == "__main__":
	main(*sys.argv[1:])