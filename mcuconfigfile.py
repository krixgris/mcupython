#mcuconfigfile.py
#

from curses.ascii import isspace
from datetime import datetime
from enum import Enum, auto, unique
import mido

class CONFIG_PARAMETERS(Enum):
	"""(ID,Defaultvalue)"""
	AUTOBANK = (auto(),1)
	DEBUG_MODE = (auto(),1)
	DAW_MIDI_INPUT = (auto(),"")
	DAW_MIDI_OUTPUT = (auto(),"")
	HW_DEVICE_MIDI_INPUT = (auto(),"")
	HW_DEVICE_MIDI_OUTPUT = (auto(),"")
	ENABLE_DEBUG_DEVICE = (auto(),0)
	DEBUG_DEVICE_MIDI_INPUT = (auto(),"")
	DEBUG_DEVICE_MIDI_OUTPUT = (auto(),"")

	def __repr__(self) -> str:
		return self.name
	def __str__(self) -> str:
		return self.name



def header()->str:
	header = (f"# Config file for mcupython, do not change any of the names in caps\n"
				+f"# MIDI Devices should follow the exact same name as in the list of available inputs\n"
				+f"# See file mididevices.txt for a list of the current devices available on runtime for easy copy&paste\n"
				+f"# AUTOBANK=0,1, DEBUG_MODE=0-4 (0 means nothing but critical messages, and 4 enables full debug mode"
				+f"# ENABLE_DEBUG_DEVICE = 1 will try to load the specified debug midi device. Mostly used for debugging code.\n"
			)
	return header

def footer()->str:
	footer = (f"\n# File created at {datetime.now()}")
	return footer

def create_empty_config(filename,overwrite=False):
	already_exists = False
	try:
		file = open(filename,"r")
		print(f"{filename} already exists. To re-create the config file, either move,delete or rename the file and try again.")
		already_exists = True
	except FileNotFoundError as e:
		print(f"File not found, creating {filename}...")
	if(already_exists and not overwrite):
		return
	file = open(filename, "w")
	file.write(header())
	for c in CONFIG_PARAMETERS:
		file.write(f"{c.name}:{c.value[1]}\n")
	file.write(footer())
	file.close()

def write_midi_port_file(midi_inputs,midi_outputs,filename="available_midi_devices.txt"):

	file = open(filename, "w")
	file.write(f"# This file will be overwritten on runtime, and will be recreated for user troubleshooting purposes only.\n")
	file.write(f"\n####\n# MIDI INPUTS:\n")
	for i in sorted(midi_inputs):
		file.write(f"{i}\n")
	file.write(f"\n####\n# MIDI OUTPUTS:\n")
	for o in sorted(midi_outputs):
		file.write(f"{o}\n")
	file.write(footer())
	file.close()

def validate_midi_config(filename, config_type_port:dict, type:str="Port")->bool:
	ports_validated = True
	midi_inputs = mido.get_input_names()
	midi_inputs = list(set(midi_inputs))
	midi_outputs = mido.get_output_names()
	midi_outputs = list(set(midi_outputs))
	#def validateMidiPorts(configPorts, availablePorts, type:str="Port"):
	#midi_port_names = list(set(midi_port_names)) # aggregate dupes
	midi_port_names = {"Input":midi_inputs, "Output":midi_outputs}
	#print(midi_port_names)
	#print(f"{midi_port_names["Input"]}")
	#print(f"\n")
	#print(f"{midi_port_names}")
	#print(f"{config_type_port['Input']}")
	for k in config_type_port:
		# print(k)
		# print(config_type_port[k])
		mismatchedports = set(config_type_port[k])-set(midi_port_names[k])
		#print(f"{mismatchedports=}, {len(mismatchedports)=}")
		if(len(mismatchedports)>0):
			ports_validated = False
			print(f"Can't find {k} ports {list(mismatchedports)}..")
	# match(config_type_port):
	# 	case{'Input':list(l)} if l in midi_port_names["Input"]:
	# 		print(i)
	# 		print("folk")
	# 	# case{"Output":l} if l in midi_port_names["Output"]:
	# 	# 	print(o)
	# 	case other:
	# 		print(other)
	# 		print("All bad and wrong")
	if(not ports_validated):
		write_midi_port_file(midi_inputs, midi_outputs)
	return ports_validated

	#incorrect_ports = [port for port in configPorts if port not in midi_port_names]
	# if(len(incorrect_ports)>0):
	# 	print(
	# 			f"{type} port(s) not found:\n{', '.join(port for port in incorrect_ports)}\n"
	# 			f"Available {type} port(s):\n{', '.join(port for port in midi_port_names)}\n"
	# 			f"Check available_midi_devices.txt and verify settings are using a device the system can see.")
	# 	write_midi_port_file(filename)
	# 	return False
	# else:
	# 	print(f"Setting up MIDI connections for {type.lower()} port(s):  {', '.join(port for port in configPorts)}")
	# 	return True
	write_midi_port_file(midi_inputs, midi_outputs)

def validate_config_file(filename="config.txt")->bool:
	#filename = "config.txt"
	config = dict()
	is_valid_conf = True
	with open(filename) as f:
		for l in f:
			first,*r = l
			if(first == "#" or isspace(first)):
				pass
			else:
				l = l.split(":")
			match(l):
				case [k,v] if k in [c.name for c in CONFIG_PARAMETERS]:
					config[k]=v.strip()
				case other:
					pass
	#print(config)

	#is_valid_conf = True
	for c in CONFIG_PARAMETERS:
		# print(config[c.name])
		if c.name not in [k for k in config]:
			print(f"Parameter {c} not found in {filename}")
			is_valid_conf = False
			return False

	for conf in CONFIG_PARAMETERS:
		i,*d = conf.value
		match(d):
			# case undef if str(undef) not in config[conf.name]:
			# 	is_valid_conf = False
			# 	print(f"{undef=}")
			case [0|1] as d if str(d[0]) not in config[conf.name]:
				#print(f"Invalid value for {conf.name=}: {d=} and {config[conf.name]=}, {type(d)=}")
				is_valid_conf = False
			case [0|1] as d:
				pass
				#print(f"{conf.name}: {config[conf.name]}")
			case _:
				pass
				#print(f"{conf.name}: {config[conf.name]}")


	

	if(not is_valid_conf):
		print(f"Incorrect parameters in {filename}. Verify that none of the parameters were changed, or delete/rename/move the file, and restart the program to generate a new config-file.")
		return False

	midi_input_devices = [config[str(CONFIG_PARAMETERS.DAW_MIDI_INPUT)],
						config[str(CONFIG_PARAMETERS.HW_DEVICE_MIDI_INPUT)]]
						
	midi_output_devices = [config[str(CONFIG_PARAMETERS.DAW_MIDI_OUTPUT)],
						config[str(CONFIG_PARAMETERS.HW_DEVICE_MIDI_OUTPUT)]]

	if(config[str(CONFIG_PARAMETERS.ENABLE_DEBUG_DEVICE)] == 1):
		midi_input_devices.append(config[str(CONFIG_PARAMETERS.DEBUG_DEVICE_MIDI_INPUT)])
		midi_output_devices.append(	config[str(CONFIG_PARAMETERS.DEBUG_DEVICE_MIDI_OUTPUT)])

	#is_valid_conf = validate_midi_config(midi_port_names=midi_input_device, midi_output_device=)

	#print(midi_input_devices)
	config_type_port = {"Input":midi_input_devices,"Output":midi_output_devices}
	#is_valid_conf = validate_midi_config(filename, config_type_port)
	if(is_valid_conf):
		pass
		#print(f"Configuration file valid.")
	else:
		print(f"Error: Configuration file invalid.")
	return is_valid_conf