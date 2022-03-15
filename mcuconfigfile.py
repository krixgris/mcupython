#mcuconfigfile.py
#

from curses.ascii import isspace
from datetime import datetime
from enum import Enum, auto, unique
import mido

class Configuration:
	loaded = True
	file_parameters:dict = dict()
	debug_mode = 1
	midi_input_devices = ""
	midi_output_devices = ""
	midi_output_daw = ""
	midi_output_hw = ""
	midi_input_hw = ""
	midi_input_daw = ""
	midi_input_debug = ""
	midi_outport_hw = ""
	midi_outport_daw = ""

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

	midi_port_names = {"Input":midi_inputs, "Output":midi_outputs}

	for k in config_type_port:
		mismatchedports = set(config_type_port[k])-set(midi_port_names[k])
		#print(f"{mismatchedports=}, {len(mismatchedports)=}")
		if(len(mismatchedports)>0):
			ports_validated = False
			print(f"Can't find {k} ports {list(mismatchedports)}..")
	if(not ports_validated):
		write_midi_port_file(midi_inputs, midi_outputs)
	return ports_validated

def validate_config_file(filename)->bool:
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

	for c in CONFIG_PARAMETERS:
		# print(config[c.name])
		if c.name not in [k for k in config]:
			print(f"Parameter {c} not found in {filename}")
			is_valid_conf = False
			return False

	for conf in CONFIG_PARAMETERS:
		i,*d = conf.value
		match(d):

			case [0|1] as d if str(d[0]) not in config[conf.name]:
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

	config_type_port = {"Input":midi_input_devices,"Output":midi_output_devices}
	is_valid_conf = validate_midi_config(filename, config_type_port)
	if(is_valid_conf):
		Configuration.file_parameters = config.copy()
		pass
		#print(f"Configuration file valid.")
	else:
		print(f"Error: Configuration file invalid.")
	return is_valid_conf

def load_midiconfig():
	print(f"{Configuration}")
	Configuration.midi_input_devices = [Configuration.file_parameters[str(CONFIG_PARAMETERS.DAW_MIDI_INPUT)],
						Configuration.file_parameters[str(CONFIG_PARAMETERS.HW_DEVICE_MIDI_INPUT)]]
						
	Configuration.midi_output_devices = [Configuration.file_parameters[str(CONFIG_PARAMETERS.DAW_MIDI_OUTPUT)],
						Configuration.file_parameters[str(CONFIG_PARAMETERS.HW_DEVICE_MIDI_OUTPUT)]]

	Configuration.midi_input_hw = Configuration.file_parameters[str(CONFIG_PARAMETERS.HW_DEVICE_MIDI_INPUT)]
	Configuration.midi_input_daw = Configuration.file_parameters[str(CONFIG_PARAMETERS.DAW_MIDI_INPUT)]
	Configuration.midi_input_debug = Configuration.file_parameters[str(CONFIG_PARAMETERS.DEBUG_DEVICE_MIDI_INPUT)]


	Configuration.midi_output_daw = Configuration.file_parameters[str(CONFIG_PARAMETERS.DAW_MIDI_OUTPUT)]
	Configuration.midi_output_hw = Configuration.file_parameters[str(CONFIG_PARAMETERS.HW_DEVICE_MIDI_OUTPUT)]

	if(Configuration.file_parameters[str(CONFIG_PARAMETERS.ENABLE_DEBUG_DEVICE)] == 1):
		Configuration.midi_input_devices.append(Configuration.file_parameters[str(CONFIG_PARAMETERS.DEBUG_DEVICE_MIDI_INPUT)])
		Configuration.midi_output_devices.append(Configuration.file_parameters[str(CONFIG_PARAMETERS.DEBUG_DEVICE_MIDI_OUTPUT)])
	pass