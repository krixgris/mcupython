#hackiemackie.py
#
#	main program file
import signal
import sys
import mido
from timeit import timeit
from time import perf_counter, localtime
import time
from dataclasses import asdict, dataclass
from mackiekeys import MCKeys, MCTracks
import mackiecontrol

from midiconfig import MidiConfig as conf

@dataclass
class AutoBankHandler:
	"""Handles banking and track switching attributes"""
	pong_timeout = 0.500 # shared timeout length between track and banks

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

	@property
	def bank_direction(self):
		return self._bank_direction

	@bank_direction.setter
	def bank_direction(self,dir:int):
		if(dir == 0):
			self._bank_direction = 0
		else:
			self._bank_direction = 1

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

	def track_reset(self):
		self.track_ping = False
		self.track_pong = False

def validateMidiPorts(configPorts, availablePorts):
	#validated_ports = [midiDevice for midiDevice in configPorts if input in availablePorts]
	
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

def timestamp():
	t = time.localtime()
	current_time = time.strftime("%H:%M:%S", t)
	return current_time


def main()->None:
	mcu = mackiecontrol.MackieControl()
	banker = AutoBankHandler()


	signal.signal(signal.SIGINT, quit_handler)
	ping:bool = False
	pong:bool = True

	pingTrack:bool = False
	pongTrack:bool = False

	pingTime = 0
	pingTimeTrack = 0
	pongTimeout = 0.50 # if no response is received, pong is overriden, and logic can be performed if needed

	queuedBank = False
	bankingRunning = False
	bankPrevDone = False
	bankNextDone = False
	bankDirectionNext = True # True = next, False = prev


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
		
		if(ping):
			now = perf_counter()
			if(pong):
				print(f"{timestamp()}: BANK CHANGE Ping pong:{now-pingTime} seconds")
				#pingMsg = mcu.PingTrack.onMsg.copy()
				#pingMsg.velocity = 0
				# how do we ping tracks in bank? can we simply say ping track and see?
				#print(mcu.PingTrack.onMsg)
				# banker.bank_ping = False
				# banker.bank_pong = False
				banker.bank_reset()

				banker.track_ping = True

				pingTrack = True
				ping = False
				pong = False
			elif(abs(now-pingTime) > pongTimeout):
				print(f"{timestamp()}: BANK CHANGE: No Pong, end of bank list?:{now-pingTime} seconds")
				ping = False
				pong = False

				# banker.bank_ping = False
				# banker.bank_pong = False
				banker.bank_reset()

				# if(bankDirectionNext):
				# 	bankNextDone = True
				# else:
				# 	bankPrevDone = True
				# bankDirectionNext = not bankDirectionNext
				# if(bankingRunning and bankNextDone and bankPrevDone):
				# 	bankingRunning = False
				# 	bankNextDone = False
				# 	bankPrevDone = False
				# 	print(f"Track not in a bank. Group or MIDI track selected?")

				
			#print(now)
			#pong = False
		if(pingTrack):
			now = perf_counter()
			#print(f"{pingTrack}")
			if(pongTrack):
				print(f"{timestamp()}: TRACK CHANGE Ping pong:{now-pingTimeTrack} seconds")
				pingTrack = False
				pongTrack = False

				# banker.track_ping = False
				# banker.track_pong = False
				banker.track_reset()
				# if(bankingRunning):
				# 	bankingRunning = False
				# 	bankNextDone = False
				# 	bankPrevDone = False

			elif(abs(now-pingTimeTrack) > pongTimeout):
				print(f"{timestamp()}: TRACK CHANGE: No Pong, track not in bank. Auto-bank needed:{now-pingTimeTrack} seconds")
				pingTrack = False
				pongTrack = False

				# banker.track_ping = False
				# banker.track_pong = False
				banker.track_reset()
				banker.bank_queued = True

				queuedBank = True
				# bankingRunning = True

		# DEBUG INPUT
		if(port.name == conf.DEBUGINPUT):
			if(msg.type == 'note_on' and msg.note in [118,119,120]):
				msg.velocity = 127
				msg.channel = 0
				#if(pong):
				print(f"Debugcommand {msg.note}")
				if(msg.note == 118):
					msg.note = MCKeys.PREVBANK #for now while testing ping pong
				if(msg.note == 119):
					banker.bank_direction = 0
					bankDirectionNext = False
					#msg.note = MCKeys.PREVBANK
				if(msg.note == 120):
					banker.bank_direction = 0
					bankDirectionNext = True
					#msg.note = MCKeys.NEXTBANK
				if(msg.note in [MCKeys.PREVBANK,MCKeys.NEXTBANK]):	
					ping = True
					pong = False
					pingTime = perf_counter()


				# banker.bank_ping = True
				# banker.bank_pong = False
				# banker.bank_ping_time = perf_counter()
				banker.bank_send_ping()


				print(f"Debug msg sending: {msg}")
				outportVirt.send(msg)
			elif(msg.type == 'note_on' or msg.type=='note_off'):
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
			if(msg.type == 'sysex'):
				if(ping and len(msg.data)>40):
					print(f"{timestamp()}:{port.name} Bank Pong!")
					pong = True
					banker.bank_pong = True

					#	big issue here, with this message not going around to get the ping pong check until next loop.
					#	uncertain how i can manipulate it.. possible to force reading messages from port?
					print(f"Pong {pong} and Ping {ping} and QueuedBank {queuedBank}")
					#
					#	push dummy message cc127 (undefined for MCU) to port to ensure pong gets caught	
					# outportVirt.send(mackiecontrol.MackieButton(122).onMsg)

			if(msg.type == 'note_on' and msg.note in mcu.TrackLookup and msg.velocity == 127):
				#outport.send(msg)
				print(f"{timestamp()}Active track msg: {msg}")
				pongTrack = True
				pingTimeTrack = perf_counter()

				# banker.track_pong = True
				# banker.track_ping_time = perf_counter()
				banker.track_send_ping()

				print(f"\nPongstatus {port.name}: {pongTrack} for msg: {msg}\n")
				#print(f"Pongstatus: {pongTrack} for msg: {msg}")
				# if(msg.velocity == 127):
				# 	print(f"Pingstatus: {pingTrack} for msg: {msg}")
				# 	if(pingTrack):
				# 		print("Track Pong!")
				# 		pongTrack = True


				
			if((msg.type == 'note_on' or msg.type == 'note_off') and msg.velocity==0 and msg.note == MCKeys.TRACK_CHANGE):
				print(msg)
				pingTrack = True
				banker.track_ping = True
				#pongTrack = False
				#pingTimeTrack = perf_counter()
				#print(f"Track changed: PING ({pingTimeTrack})")
				#print(f"Pingstatus: {pingTrack} for msg: {msg}")
				#outport.send(msg)

		
			if(msg.type == 'note_on' and msg.note in [MCKeys.PREVBANK, MCKeys.NEXTBANK]):
				print(f"VirtCommand {str(MCKeys(msg.note))}")
				#ping = True
				#pong = False
				#pingTime = perf_counter()
				print(f"Virt msg sending: {msg}")
				#outportVirt.send(msg)

			# # if(pong):
			# # 		if(msg.type == 'note_on' and msg.note in [MCKeys.PREVBANK, MCKeys.NEXTBANK]):
			# # 			ping = True
			# # 			pong = False
			# # 			print("Listening to bank changes from virt")
			# # 			pingTime = perf_counter()
			# # 			outport.send(msg)

			outport.send(msg)


		# HARDWARE INPUT
		if(port.name ==conf.HWINPUT):

#			if(pong):
			if(msg.type == 'note_on' and msg.velocity == 127 and msg.note in [MCKeys.PREVBANK, MCKeys.NEXTBANK]):
				print(f"{timestamp()}:HWCommand {str(MCKeys(msg.note))}")
				ping = True
				pong = False
				pingTime = perf_counter()

				# banker.bank_ping = True
				# banker.bank_pong = False
				# banker.bank_ping_time = perf_counter()
				banker.bank_send_ping()
				# print(f"HW msg sending: {msg}")
				#outportVirt.send(msg)

			outportVirt.send(msg)
		
			# if(msg.type == 'note_on' and msg.note in mcu.TrackLookup and msg.velocity == 127):
			# 	#outport.send(msg)
			# 	print(msg)
			# 	pongTrack = True
			# 	pingTime = perf_counter()
			# 	print(f"\nPongstatus {port.name}: {pongTrack} for msg: {msg}\n")
			# 	# if(msg.velocity == 127):
			# 	# 	print(f"Pingstatus: {pingTrack} for msg: {msg}")
			# 	# 	if(pingTrack):
			# 	# 		print("Track Pong!")
			# 	# 		pongTrack = True


		#
		#	Consideration of having to check for ping pong at the end *as well* as the top
		#
		# if(ping and queuedBank):
		# 	now = perf_counter()
		# 	if(pong):
		# 		print(f"bottom of code")
		# 		print(f"{timestamp()}: BANK CHANGE Ping pong:{now-pingTime} seconds")
		# 		#pingMsg = mcu.PingTrack.onMsg.copy()
		# 		#pingMsg.velocity = 0
		# 		# how do we ping tracks in bank? can we simply say ping track and see?
		# 		#print(mcu.PingTrack.onMsg)
		# 		pingTrack = True
		# 		#pongTrack = False
		# 		#pingTimeTrack = 0
		# 		ping = False
		# 		pong = False
		# 	elif(abs(now-pingTime) > pongTimeout):
		# 		print(f"bottom of code")
		# 		print(f"{timestamp()}: BANK CHANGE: No Pong, end of bank list?:{now-pingTime} seconds")
		# 		ping = False
		# 		pong = False
				
		# 		# if(bankDirectionNext):
		# 		# 	bankNextDone = True
		# 		# else:
		# 		# 	bankPrevDone = True
		# 		# bankDirectionNext = not bankDirectionNext
		# 		# if(bankingRunning and bankNextDone and bankPrevDone):
		# 		# 	bankingRunning = False
		# 		# 	bankNextDone = False
		# 		# 	bankPrevDone = False
		# 		# 	print(f"Track not in a bank. Group or MIDI track selected?")

		# if(pingTrack and queuedBank):
		# 	now = perf_counter()
		# 	#print(f"{pingTrack}")
		# 	if(pongTrack):
		# 		print(f"bottom of code")
		# 		print(f"{timestamp()}: TRACK CHANGE Ping pong:{now-pingTimeTrack} seconds")
		# 		pingTrack = False
		# 		pongTrack = False
		# 		# if(bankingRunning):
		# 		# 	bankingRunning = False
		# 		# 	bankNextDone = False
		# 		# 	bankPrevDone = False

		# 	elif(abs(now-pingTimeTrack) > pongTimeout):
		# 		print(f"bottom of code")
		# 		print(f"{timestamp()}: TRACK CHANGE: No Pong, track not in bank. Auto-bank needed:{now-pingTimeTrack} seconds")
		# 		pingTrack = False
		# 		pongTrack = False
		# 		queuedBank = True
		# 		# bankingRunning = True



		if(queuedBank):
			queuedBank = False
			ping = True
			pong = False

			banker.bank_queued = False
			# banker.bank_ping = True
			# banker.bank_pong = False
			# banker.bank_ping_time = perf_counter()
			banker.bank_send_ping()

			#	logic to figure out direction here
			#	send msg, not print
			print(banker.bank_messages[banker.bank_direction])

			#bankDirectionNext = True
			pingTime = perf_counter()
			if(bankDirectionNext):
				print(f"Next bank")
				#bankDirectionNext = not bankDirectionNext
				outportVirt.send(mcu.NextBank.onMsg)
			else:
				print(f"Prev bank")
				#bankDirectionNext = not bankDirectionNext
				outportVirt.send(mcu.PrevBank.onMsg)
		#
		#	End of Midi loop
		#


if __name__ == "__main__":
    main()