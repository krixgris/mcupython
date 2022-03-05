#hackiemackie.py
#
#	main program file
import signal
import sys
import mido
from dataclasses import asdict, dataclass
from mackiekeys import MCKeys, MCTracks

from midiconfig import MidiConfig as conf

@dataclass
class Midi:
	pass

def quit_handler(sig, frame):
	print("\nCtrl-C pressed")
	print("HackieMackie Terminating...")
	sys.exit(0)

def main()->None:
	signal.signal(signal.SIGINT, quit_handler)

	debugMode:bool = True if conf.DEBUGMODE == 1 else False
	midiOutput = conf.HWOUTPUT
	midiOutputVirtual = conf.DAWOUTPUT
	midiInputs = [conf.HWINPUT, conf.DAWINPUT]
	if(debugMode):
		midiInputs.append(conf.DEBUGINPUT)
	midiOutputs = [conf.HWOUTPUT, conf.DAWOUTPUT]

	# ensure devices are found, and only use those, print msg for information
	# code duplication, should move to validation function
	#
	midiMultiInput = [input for input in midiInputs if input in mido.get_input_names()]
	detectedOutputs = [output for output in midiOutputs if output in mido.get_output_names()]
	if(len(midiMultiInput) != len(midiInputs)):
		missingInputs = set(midiInputs)-set(midiMultiInput)
		print("Inputs not found:")
		for input in missingInputs:
			print(input)
		print("List of available inputs:")
		print(mido.get_input_names())
		print("\nFollowing devices are configured as inputs:")
		print(midiMultiInput)
		print("\n")

	if(len(detectedOutputs) != len(midiOutputs)):
		missingOutputs = set(midiOutputs)-set(detectedOutputs)
		print("Outputs not found:")
		for output in missingOutputs:
			print(output)
		print("List of available outputs:")
		print(mido.get_output_names())
		print("\nFollowing devices are configured as outputs:")
		print(detectedOutputs)
		print("HackieMackie terminating...outputs need to be configured correctly to run.")
		sys.exit(0)

	if(debugMode):
		print("Debug mode enabled, using device " + conf.DEBUGINPUT + " as debug input."
				+ "\nMackie Command will be printed, and wont get sent until Modwheel cc 127 is sent from debug to confirm.\n")

	# needs validation to prevent errors
	outport = mido.open_output(midiOutput)
	outportVirt = mido.open_output(midiOutputVirtual)



	multiPorts = [mido.open_input(i) for i in midiMultiInput]

	MCDict = {x:x for x in MCKeys}



	print("HackieMackie Starting...Ctrl-C to terminate.")
	# MAIN LOOP
	for port, msg in mido.ports.multi_receive(multiPorts, yield_ports=True, block=True):
		# DEBUG INPUT
		if(port.name == conf.DEBUGINPUT):
			if(msg.type == 'note_on' and msg.note in [125,126,127]):
				print(f"Debugcommand {msg.note}")
				if(msg.note == 125):
					msg.note = 125
				if(msg.note == 126):
					msg.note = 46
				if(msg.note == 127):
					msg.note = 47
			if(msg.type == 'note_on' or msg.type=='note_off'):
				if(int(msg.note) in MCDict):
					if(msg.type == 'note_on' and msg.velocity>40):
						print('toggles on')
						msg.velocity = 127
						msg.channel = 0
						primedMsg = msg.copy()
						queuedDebug = True
						print("Primed msg: " + str(MCKeys(msg.note)) + " (" + str(msg.note) + ")" + " (Vel:" + str(msg.velocity) + ")")
					if(msg.type == 'note_on' and msg.velocity<=40):
						print('toggles off')
						offMsg = mido.Message('note_on', channel = 0, note = msg.note, velocity=0)
						msg.channel = 0
						msg.velocity = 0
						primedMsg = msg.copy()
						queuedDebug = True
						print("Primed msg: " + str(MCKeys(msg.note)) + " (" + str(msg.note) + ")" + " (Vel:" + str(msg.velocity) + ")")
						#outportVirt.send(offMsg)
			if(msg.type == 'control_change'):
				# control = ccnr
				# value = value
				if(msg.value==127 and msg.control==1 and queuedDebug):
					print("Sending:" + str(MCKeys(primedMsg.note)) + " (" + str(primedMsg.note) + ")" + " (Vel:" + str(primedMsg.velocity) + ")")
					outportVirt.send(primedMsg)
					queuedDebug = False
					primedMsg = None

		
		# VIRTUAL INPUT
		if(port.name == conf.DAWINPUT):
			outport.send(msg)


		# HARDWARE INPUT
		if(port.name ==conf.HWINPUT):
			outportVirt.send(msg)



if __name__ == "__main__":
    main()