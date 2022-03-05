#hackiemackie.py
#
#	main program file
import signal
import sys
import mido
from dataclasses import asdict, dataclass
from mackiekeys import MCKeys, MCTracks

from midiconfig import MidiConfig as conf

def validateMidiPorts(configPorts, availablePorts):
	validated_ports = [midiDevice for midiDevice in configPorts if input in availablePorts]
	
	incorrect_ports = [port for port in configPorts if port not in availablePorts]
	if(len(incorrect_ports)>0):
		print(
				f"Ports not found:\n{incorrect_ports}\n"
				f"Available ports:\n{availablePorts}\n"
				f"HackieMackie Terminating...Check configuration and restart.")
		sys.exit(0)
	else:
		print(f"Ports found. Setting up MIDI connections.")

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

	midiInputs = [conf.HWINPUT, conf.DAWINPUT]
	if(debugMode):
		midiInputs.append(conf.DEBUGINPUT)
	midiOutputs = [conf.HWOUTPUT, conf.DAWOUTPUT]

	# tuples might be a better idea, to keep this as one single call
	validateMidiPorts(midiInputs, mido.get_input_names())
	validateMidiPorts(midiOutputs, mido.get_output_names())

	if(debugMode):
		print("Debug mode enabled, using device " + conf.DEBUGINPUT + " as debug input."
				+ "\nMackie Command will be printed, and wont get sent until Modwheel cc 127 is sent from debug to confirm.\n")

	outport = mido.open_output(conf.HWOUTPUT)
	outportVirt = mido.open_output(conf.DAWOUTPUT)

	multiPorts = [mido.open_input(i) for i in midiInputs]

	# dict for lookup/validation for mackie commands
	MCDict = {x:x for x in MCKeys}

	print("HackieMackie Starting...Ctrl-C to terminate.")
	# MAIN LOOP
	#
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
				outportVirt.send(msg)
			if(msg.type == 'note_on' or msg.type=='note_off'):
				if(int(msg.note) in MCDict):
					if(msg.type == 'note_on' and msg.velocity>40):
						print('toggles on')
						msg.velocity = 127
						msg.channel = 0
						primedMsg = msg.copy()
						queuedDebug = True
						#print("Primed msg: " + str(MCKeys(primedMsg.note)) + " (" + str(primedMsg.note) + ")" + " (Vel:" + str(primedMsg.velocity) + ")")
					if(msg.type == 'note_on' and msg.velocity<=40):
						print('toggles off')
						offMsg = mido.Message('note_on', channel = 0, note = msg.note, velocity=0)
						primedMsg = offMsg.copy()
						queuedDebug = True
						#outportVirt.send(offMsg)
					print("Primed msg: " + str(MCKeys(msg.note)) + " (" + str(msg.note) + ")" + " (Vel:" + str(msg.velocity) + ")")
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