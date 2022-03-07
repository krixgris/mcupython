#hackiemackie.py
#
#	main program file
import signal
import sys
import mido
import atexit
from time import perf_counter
import time
from dataclasses import asdict, dataclass
from mackiekeys import MCKeys, MCTracks
import mackiecontrol

from midiconfig import MidiConfig as conf

def timestamp(nobrackets = False):
	t = time.localtime()
	if(nobrackets):
		current_time = time.strftime("%H:%M:%S", t)
	else:
		current_time = time.strftime("[%H:%M:%S]: ", t)
	return current_time

def print_debug(text:str,print_time=True, debug:bool=False):
	debug_mode =True if conf.DEBUGMODE == 1 else False
	if(debug_mode or debug):
		if(print_time):
			text = f"{timestamp()}{text}"
		print(text)

def close_and_quit(outport, outportVirt, multiPorts):
	
	print_debug(f"Cleaning up...closing ports...")
	print_debug(f"Closing outputs: {outport.name}, {outportVirt.name}")
	print_debug(f"Closing inputs: {''.join(port.name for port in multiPorts)}")
	outport.close()
	outportVirt.close()
	for port in multiPorts:
		port.close()
	
	print_debug(f"{outport.name} closed: {outport.closed}")
	print_debug(f"{outportVirt.name} closed: {outportVirt.closed}")
	#print_debug(f"{*multiPorts,.join(str(x) for x in a} closed: {multiPorts}")
	for port in multiPorts:
		print_debug(f"{port.name} closed: {port.closed}")

	#sys.exit(0)


@dataclass
class AutoBankHandler:
	"""Handles banking and track switching attributes"""
	auto_bank:bool
	pong_timeout = 0.150 # shared timeout length between track and banks

	bank_queued = False
	bank_running = False
	_bank_direction:int = 0 # 0 = PREV, any other integer is NEXT
	
	bank_messages = (mackiecontrol.MackieButton(MCKeys.PREVBANK),mackiecontrol.MackieButton(MCKeys.NEXTBANK))

	bank_ping:bool = False
	bank_pong:bool = False
	bank_ping_time = 0

	track_ping:bool = False
	track_pong:bool = False
	track_ping_time = 0

	bank_time_since_bank = 0

	bank_search_time = 0

	@property
	def bank_direction(self):
		return self._bank_direction

	@bank_direction.setter
	def bank_direction(self,dir:int):
		if(dir == 0):
			self._bank_direction = 0
		else:
			self._bank_direction = 1

	def bank_change_direction(self,reset=False):
		self._bank_direction += 1
		if(reset or self.bank_direction>1):
			self._bank_direction = 0
			self.bank_running = False

	def bank_search(self):
		"""Logic for starting search mode"""
		self.bank_search_time = perf_counter()
		self.bank_queued = True
		self.bank_running = True
		self.bank_direction = 0

		print_debug(f"Bank searching started...")
		pass
	def bank_found(self):
		"""Logic for resetting counters and flags"""
		now = perf_counter()
		print_debug(f"Bank found! {now-self.bank_search_time} seconds")
		self.bank_running = False
		self.bank_queued = False

	def bank_send_ping(self):
		self.bank_ping = True
		self.bank_pong = False
		self.bank_ping_time = perf_counter()

	def track_send_ping(self):
		self.track_pong = True
		self.track_ping_time = perf_counter()

	def bank_reset(self):
		self.bank_ping = False
		self.bank_pong = False
		#self.bank_ping_time = 0

	def track_reset(self):
		self.track_ping = False
		self.track_pong = False
		self.track_ping_time = 0

def validateMidiPorts(configPorts, availablePorts):
	availablePorts = list(set(availablePorts))
	incorrect_ports = [port for port in configPorts if port not in availablePorts]
	if(len(incorrect_ports)>0):
		print_debug(
				f"Ports not found:\n{incorrect_ports}\n"
				f"Available ports:\n{availablePorts}\n"
				f"HackieMackie Terminating...Check configuration and restart.")
		sys.exit(0)
	else:
		print_debug(f"Ports found. Setting up MIDI connections for {configPorts}")

@dataclass
class Midi:
	pass

def quit_handler(sig, frame):
	print_debug("\nCtrl-C pressed", debug = True)
	print_debug("HackieMackie Terminating...", debug = True)
	sys.exit(0)

	


def main()->None:
	mcu = mackiecontrol.MackieControl()
	auto_bank = True if conf.AUTOBANK == 1 else False
	banker = AutoBankHandler(auto_bank)

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
		print_debug(f"Debug mode enabled, using device {conf.DEBUGINPUT} as debug input.")
		print_debug(f"Mackie Command wont get sent until Modwheel cc 127 is sent from debug to confirm.")

	outport = mido.open_output(conf.HWOUTPUT)
	outportVirt = mido.open_output(conf.DAWOUTPUT)

	multiPorts = [mido.open_input(i) for i in midiInputs]

	# dict for lookup/validation for mackie commands
	MCDict = {x:x for x in MCKeys}
	
	atexit.register(close_and_quit,outport, outportVirt, multiPorts)

	print_debug("HackieMackie Starting...Ctrl-C to terminate.", debug = True)
	# MAIN LOOP
	#
	for port, msg in mido.ports.multi_receive(multiPorts, yield_ports=True, block=True):
		# DEBUG INPUT
		if(port.name == conf.DEBUGINPUT):
			if(msg.type == 'note_on' and msg.note in [118,119,120]):
				msg.velocity = 127
				msg.channel = 0
				print_debug(f"Debugcommand {msg.note}")
				if(msg.note == 118):
					msg.note = MCKeys.PREVBANK #for now while testing ping pong
				if(msg.note == 119):
					banker.bank_direction = 0
				if(msg.note == 120):
					banker.bank_direction = 1
				if(msg.note in [MCKeys.PREVBANK,MCKeys.NEXTBANK]):	
					banker.bank_send_ping()


				print_debug(f"Debug msg sending: {msg}")
				outportVirt.send(msg)
			elif(msg.type == 'note_on' or msg.type=='note_off'):
				if(int(msg.note) in MCDict and msg.type =='note_on'):
					if(msg.type == 'note_on' and msg.velocity>40):
						print_debug('toggles on')
						msg.velocity = 127
						msg.channel = 0
						primedMsg = msg.copy()
						queuedDebug = True
					if(msg.type == 'note_on' and msg.velocity<=40):
						print_debug('toggles off')
						offMsg = mido.Message('note_on', channel = 0, note = msg.note, velocity=0)
						primedMsg = offMsg.copy()
						queuedDebug = True
					print_debug("Primed msg: " + str(MCKeys(primedMsg.note)) + " (" + str(primedMsg.note) + ")" + " (Vel:" + str(primedMsg.velocity) + ")")
			if(msg.type == 'control_change'):
				if(msg.value==127 and msg.control==1 and queuedDebug):
					print_debug("Sending:" + str(MCKeys(primedMsg.note)) + " (" + str(primedMsg.note) + ")" + " (Vel:" + str(primedMsg.velocity) + ")")
					outportVirt.send(primedMsg)
					queuedDebug = False
					primedMsg = None
		# END DEBUG INPUT

		
		# VIRTUAL INPUT
		if(port.name == conf.DAWINPUT):
			if(msg.type == 'sysex'):
				if(banker.bank_ping and len(msg.data)>40):
					print_debug(f"{port.name} Bank Pong!")
					banker.bank_pong = True
					print_debug(f"Pong {banker.bank_pong} and Ping {banker.bank_ping} and QueuedBank {banker.bank_queued}")

			if(msg.type == 'note_on' and msg.note in mcu.TrackLookup and msg.velocity == 127):
				print_debug(f"Active track msg: {msg}")

				# ping is pong for tracks...confusing, but live with it
				banker.track_send_ping()

				print_debug(f"Pongstatus {port.name}: {banker.track_pong} for msg: {msg}")


				
			if((msg.type == 'note_on' or msg.type == 'note_off') and msg.velocity==0 and msg.note == MCKeys.TRACK_CHANGE):
				print_debug(msg)
				banker.track_ping = True

		
			if(msg.type == 'note_on' and msg.note in [MCKeys.PREVBANK, MCKeys.NEXTBANK]):
				print_debug(f"VirtCommand {str(MCKeys(msg.note))}")

				print_debug(f"Virt msg sending: {msg}")

			outport.send(msg)
		# END VIRTUAL INPUT

		# HARDWARE INPUT
		if(port.name ==conf.HWINPUT):
			if(msg.type == 'note_on' and msg.velocity == 127 and msg.note in [MCKeys.PREVBANK, MCKeys.NEXTBANK]):
				print_debug(f"HWCommand {str(MCKeys(msg.note))}")
				banker.bank_send_ping()

			outportVirt.send(msg)
		# END HARDWARE INPUT

		# PING PONG Logic
		if(banker.bank_ping):
			now = perf_counter()
			if(banker.bank_pong):
				print_debug(f"BANK CHANGE Ping pong:{now-banker.bank_ping_time} seconds")
				banker.bank_reset()
				banker.track_ping = True
			elif(abs(now-banker.bank_ping_time) > banker.pong_timeout):
				print_debug(f"BANK CHANGE: No Pong, end of bank list?:{now-banker.bank_ping_time} seconds")
				banker.bank_reset()
				if(banker.bank_running):
					if(banker.bank_direction == 1):
						banker.bank_reset()
						banker.bank_queued = False
						banker.bank_running = False
					else:
						banker.bank_queued = True
						banker.bank_change_direction()
						banker.track_ping = True
				print_debug(f"Direction: {banker.bank_direction} and running {banker.bank_running} and queued: {banker.bank_queued}")

		if(banker.track_ping):
			now = perf_counter()
			if(banker.track_pong):
				print_debug(f"TRACK CHANGE Ping pong:{now-banker.track_ping_time} seconds")
				banker.track_reset()

				if(banker.bank_running):
					banker.bank_found()
				# should be banker.bank_stop
				banker.bank_change_direction(reset = True)

			elif(abs(now-banker.track_ping_time) > banker.pong_timeout):
				print_debug(f"TRACK CHANGE: No Pong, track not in bank. Auto-bank needed:{now-banker.track_ping_time} seconds")
				banker.track_reset()
				#
				if(banker.bank_running):
					pass
				else:
					banker.bank_search()
					# should be method
					# banker.bank_queued = True
					# banker.bank_running = True
					# banker.bank_direction = 0
				
				banker.bank_queued = True
				
				
				# bankingRunning = True
		
		# PING PONG Logic
		
		if(banker.bank_queued and banker.auto_bank):#should check only for auto_bank mode but for debug, nope
			banker.bank_queued = False
			banker.bank_send_ping()
			now=perf_counter()

			#	logic to figure out direction here
			print_debug(f"In banker with status running: {banker.bank_running}")
			print_debug(banker.bank_messages[banker.bank_direction])
			outportVirt.send(banker.bank_messages[banker.bank_direction].onMsg)
			banker.bank_time_since_bank = perf_counter()

		#
		#	End of Midi loop
		#


if __name__ == "__main__":
    main()