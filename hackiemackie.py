#hackiemackie.py
#
#	main program file
from re import X
import signal
from socket import timeout
import sys
import mido
from mido.ports import MultiPort
import atexit
import asyncio
from datetime import datetime
from time import perf_counter, sleep
from dataclasses import asdict, dataclass, field
from mackiekeys import MCKeys, MCTracks
import mackiecontrol
from midiconfig import MidiConfig as conf

# current issue: track Kick isn't caught due to its position in the sysex being the same as in eq mode..workaround?
# go through one more round of sysex to 'clear' it?
#


DEBUG_MODE:int = 1

MESSAGE_SEND_CRITICAL = 0
MESSAGE_SEND_IMPORTANT = 1
MESSAGE_SEND_DEBUG_LOW = 2
MESSAGE_SEND_DEBUG_MED = 3
MESSAGE_SEND_DEBUG_FULL = 4


@dataclass
class IOPorts:
	output = ""
	output_virt = ""
	multi_input:list = field(init=False)

	def __post_init__(self):
		self.multi_input = []


global multiPorts
multiPorts = ("")

def midi_test(msg:mido.Message)->None:
	"""From test debug environment, start of moving to structural patteren matching new with py3.10"""
	match(msg):
		case mido.messages.messages.Message(note=mValue):
			print(f"type is note message {mValue}")
			# mValue is local to this scope, as it is just bound to mValue 
			# to use outside of match, you have to *assign* it to a variable
		case mido.messages.messages.Message(type="sysex", data=_):
			print(f"sysex")
		case mido.messages.messages.Message(type="control_change"):
			print(f"cc")
		case other:
			print(f"Other type...{other}")
	#print(mValue)
	return 

def timestamp(nobrackets = False):
	t = datetime.now()
	formatStr = "%H:%M:%S"
	if(debug_mode):
		formatStr += ".%f"
	if(not nobrackets):
		formatStr = f"[{formatStr}]: "
	current_time = t.strftime(f"{formatStr}")
	
	return current_time

def print_debug(text:str,msg_debug_level:int=0,print_time=True, override_debug:bool=False):
	if(print_time):
		text = f"{timestamp()}{text}"
	if(msg_debug_level <= DEBUG_MODE or DEBUG_MODE >= MESSAGE_SEND_DEBUG_FULL or DEBUG_MODE<0):
			print(text)

#def close_and_quit(outport, outportVirt, multiPorts):
def close_ports(*ports):
	print_debug(f"Cleaning up...closing ports...",2)
	for port in ports:
			print_debug(f"Closing {port=} ...",2)
			port.close()
			print_debug(f"{port.name} closed: {port.closed}",2)


@dataclass
class AutoBankHandler:
	"""Handles banking and track switching attributes"""
	wait_for_sysex = False
	wait_for_sysex_queued = False
	wait_for_sysex_reset = False

	wait_for_sysex_count = 0

	block_sysex_outport = True

	auto_bank:bool
	pong_timeout = 0.150 # shared timeout length between track and banks

	bank_queued = False
	bank_running = False
	bank_first_run = False
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
		self.bank_first_run = True
		self.bank_search_time = perf_counter()
		self.bank_queued = True
		self.bank_running = True
		self.bank_direction = 0
		#self._bank_direction = -1
		print_debug(f"Bank searching started...",1)
		pass
	def bank_found(self):
		"""Logic for resetting counters and flags"""
		now = perf_counter()
		print_debug(f"Bank found! {now-self.bank_search_time} seconds",2)
		self.bank_running = False
		self.bank_queued = False
		self.bank_first_run = False

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

def validateMidiPorts(configPorts, availablePorts, type:str="Port"):
	availablePorts = list(set(availablePorts))
	incorrect_ports = [port for port in configPorts if port not in availablePorts]
	if(len(incorrect_ports)>0):
		print_debug(
				f"{type} port(s) not found:\n{', '.join(port for port in incorrect_ports)}\n"
				f"Available {type} port(s):\n{', '.join(port for port in availablePorts)}\n"
				f"HackieMackie Terminating...Check configuration and restart.",1)
		sys.exit(0)
	else:
		print_debug(f"Setting up MIDI connections for {type.lower()} port(s):  {', '.join(port for port in configPorts)}",1)


def quit_handler(sig, frame):
	print_debug(f"")
	print_debug("Ctrl-C pressed", 1)
	print_debug("HackieMackie Terminating...", 1)
	sys.exit(0)

def sysex_text_decode(sysex_hex_str, offset_pos=0, len=-1)->str:
	dehexify = [s for s in sysex_hex_str[20+offset_pos:].split(' ')]
	count = 0
	for i in dehexify:
		count+=1
	if(count+2<len):
		len = -1
	if(count < 3):
		return ""

	_,*dehexify,_ = dehexify

	dehexify = dehexify[:len]
	word = [bytes.fromhex(s).decode('utf-8') for s in dehexify]
	return ''.join(word).strip()



def CreateSetDisplaySysex(TextToConvert,Row=0, Page=0):
	#first 6 defines stuff
	#data=(0,0,102,20,18, <-- means set display
	#6th byte defines position
	#00 is first row, first page
	#56 is second row, first page
	#63 is second, second
	#+7 for each page
	#rowNo*56*pageNo*7 with 0 as first row, 0 as first page

	pos = Row*56+Page*7

	dataArray = [0,0,102,20,18,pos]
	TextToConvert += "       "
	TextToConvert = TextToConvert[0:7]

	for s in TextToConvert:
		dataArray.append(ord(s))

	print_debug(dataArray,4)

	return(dataArray)

def long_sysex_message(*text):
	#first 6 defines stuff
	#data=(0,0,102,20,18, <-- means set display
	#6th byte defines position
	dataArray = [0,0,102,20,18,0]
	
	blank_text = ""
	for i in range(112):
		blank_text += " "
	row1,*row2 = text
	row1 = ''.join(row1)
	text = ""
	if(len(row2) == 0):
		if(len(row1)<8):
			row1 += "         "
			row1 = row1[0:7]
			for i in range(7):
				row1 += row1[0:7]
		text = row1 + blank_text
	else:
		row2 = ''.join(row2[0])
		if(len(row1)<8 and len(row2)<8):
			row1 += "         "
			row2 += "         "
			row1 = row1[0:7]
			row2 = row2[0:7]
			for i in range(7):
				row1 += row1[0:7]
				row2 += row2[0:7]
		text = row1 + blank_text
		text = text[0:56] + row2 + blank_text
	text = text[:112]

	for s in text:
		dataArray.append(ord(s))

	return(dataArray)


def sysex_mido_message(sysex_data):
	return mido.Message('sysex', data=sysex_data)

def send_sysex(outport, sysexdata):
	outport.send(sysex_mido_message(sysexdata))

async def main(*args)->None:

	global debug_mode
	midi_ports = IOPorts()
	#global multiPorts
	multiPorts = ("")
	debug_device_enabled = True

	signal.signal(signal.SIGINT, quit_handler)
	auto_bank = True if conf.AUTOBANK == 1 else False
	debug_mode = True if conf.DEBUGMODE == 1 else False

	midiInputs = [conf.HWINPUT, conf.DAWINPUT]
	midiOutputs = [conf.HWOUTPUT, conf.DAWOUTPUT]

	for arg in args:
		k = arg.split("=")[0].lower()
		v = arg.split("=")[1].lower()
		if(k == "debug"):
			if(v in ['false','0','off']):
				debug_mode = False
			elif(v in ['true','1','on','debug']):
				debug_mode = True
			else:
				print_debug(f"Incorrect value sent for {k}. Parameter ignored.",1)
		elif(k == "autobank"):
			if(v in ['false','0','off']):
				auto_bank = False
			elif(v in ['true','1','on','auto_bank','auto']):
				auto_bank = True

			else:
				print_debug(f"Incorrect value sent for {k}. Parameter ignored.",1)
		elif(k == "debug_device_enabled"):
				if(v in ['false','0','off']):
					debug_device_enabled = False
				elif(v in ['true','1','on','debug']):
					debug_device_enabled = True
				else:
					print_debug(f"Incorrect value sent for {k}. Parameter ignored.",1)
		else:
			print_debug(f"Unhandled argument passed: {k}. Parameter ignored.",1)

	if(debug_mode and debug_device_enabled):
		midiInputs.append(conf.DEBUGINPUT)

	if(auto_bank):
		print_debug(f"Auto-Bank Enabled", 1)
	else:
		print_debug(f"Auto-Bank Disabled", 1)

	mcu = mackiecontrol.MackieControl()
	banker = AutoBankHandler(auto_bank)



	# tuples might be a better idea, to keep this as one single call
	validateMidiPorts(midiInputs, mido.get_input_names(), type="Input")
	validateMidiPorts(midiOutputs, mido.get_output_names(), type="Output")

	if(debug_mode):
		print_debug(f"Debug mode enabled, using device {conf.DEBUGINPUT} as debug input.",1)
		print_debug(f"Mackie Command wont get sent until Modwheel cc 127 is sent from debug to confirm.",1)

	print_debug(f"Opening ports..",4)
	outport = mido.open_output(conf.HWOUTPUT)
	print_debug(f"{outport=}",4)
	outportVirt = mido.open_output(conf.DAWOUTPUT)
	print_debug(f"{outportVirt=}",4)
	midi_ports.multi_input = [mido.open_input(i) for i in midiInputs]
	multiPorts = midi_ports.multi_input
	# try:
	# 	print_debug(f"Connect is running above..",1)
	# 	#task_connect = asyncio.wait_for(connect_ports(midiInputs,midi_ports),timeout=3.0)
	# 	#await asyncio.gather(task_connect)
	# 	sleep(1)

	# 	print(f"{midi_ports.multi_input=}")
	# 	#await asyncio.wait(connect_ports(midiInputs), timeout=4.0)
	# 	#await asyncio.wait({multiPorts}, timeout=4.0)
	# 	#midi_ports.multi_input = [mido.open_input(i) for i in midiInputs]

	# 	for p in midiInputs:
	# 		print(p)
	# 		# with mido.open_input(p) as port:
	# 		# 	print_debug(f"Opening {port=}")
	# 		# 	midi_ports.multi_input.append(port)
	# 		# 	print_debug(f"{port.name}, {port.closed=}",1)
	# 	#multiPorts = [mido.open_input(i) for i in midiInputs]
		
	# except:
	# 	print("Took way too long..")
	# 	#multiPorts = ""

	# print("FINALLY! And now?")
	# #await asyncio.sleep(2)
	# print("FINALLY! And now? After sleep...")
	
	# multiPorts = midiInputs#midi_ports.multi_input
	# print(multiPorts)
	#inputPorts = MultiPort(multiPorts)
	# print_debug(f"{multiPorts=}",1)
	if(multiPorts == ""):
		print_debug("ERRRRRRRORRRRRR",0)
	print_debug(f"Connected...{multiPorts=}",1)
	# dict for lookup/validation for mackie commands
	MCDict = {x:x for x in MCKeys}
	
	#atexit.register(close_ports,outport, outportVirt, *multiPorts)

	print_debug("HackieMackie Starting...Ctrl-C to terminate.", 0)
	#
	# updates display on controller, this may or may not work for various controllers. will need testing i guess
	# useful to see if app started
	outport.send(sysex_mido_message(long_sysex_message("Started",f"{timestamp(1)[0:5]}")))
	# MAIN LOOP
	#
	# print(inputPorts)
	# print(dir(inputPorts))

	# print(type(inputPorts))
	# for port, msg in inputPorts:
	# 	print(port)
	# 	print(msg)
	# with mido.open_input(inputPorts) as multi_port:
	# 	pass


	for port, msg, in mido.ports.multi_receive(multiPorts, yield_ports=True, block=True):

		match(port):
			case [conf.DEBUGINPUT]:
				print_debug(f"Debug port",2)
			case [conf.DAWINPUT]:
				print_debug(f"DAW port",2)
			case [conf.HWINPUT]:
				print_debug(f"HW port",2)

		# DEBUG INPUT
		if(port.name == conf.DEBUGINPUT):
			if(msg.type == 'note_on' and msg.note in [118,119,120]):
				msg.velocity = 127
				msg.channel = 0
				print_debug(f"Debugcommand {msg.note}")
				if(msg.note == 118):
					# newMsg = SysexMidoMessage(CreateSetDisplaySysex("Auto",0,0))
					# newMsg = SysexMidoMessage(CreateSetDisplaySysex("Bank",1,0))
					#outport.send(mackiecontrol.MackieButton(MCKeys.TRACK_1).onMsg)
					outport.send(sysex_mido_message(long_sysex_message(f"{msg.note}",f"{msg.type}")))
					#msg = SysexMidoMessage(CreateSetDisplaySysex("Send this back",1,0))
					#msg.note = MCKeys.PREVBANK #for now while testing ping pong
					# multiPorts.append((port,msg))
					#multiPorts.insert(0,(port,newMsg))
				elif(msg.note == 119):
					#banker.bank_direction = 0
					msg = mackiecontrol.MackieButton(MCKeys.FADERBANKMODE_PANS).onMsg
					print_debug(f"Stopping - {banker.wait_for_sysex_count=}",4)
					
					pass
				elif(msg.note == 120):
					#banker.bank_direction = 1
					msg = mackiecontrol.MackieButton(MCKeys.FADERBANKMODE_EQ).onMsg
					print_debug(f"Debug device {MCKeys.FADERBANKMODE_EQ.name}",4)
					banker.wait_for_sysex_count = 0
					banker.wait_for_sysex = True
					banker.wait_for_sysex_queued = True
					pass
				elif(msg.note in [MCKeys.PREVBANK,MCKeys.NEXTBANK]):
					banker.bank_send_ping()


				print_debug(f"Debug msg sending: {msg}",4)
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
					print_debug("Primed msg: " + str(MCKeys(primedMsg.note)) + " (" + str(primedMsg.note) + ")" + " (Vel:" + str(primedMsg.velocity) + ")",4)
			if(msg.type == 'control_change'):
				if(msg.value==127 and msg.control==1 and queuedDebug):
					print_debug("Sending:" + str(MCKeys(primedMsg.note)) + " (" + str(primedMsg.note) + ")" + " (Vel:" + str(primedMsg.velocity) + ")",4)
					outportVirt.send(primedMsg)
					queuedDebug = False
					primedMsg = None
		# END DEBUG INPUT

		
		#################################################
		#
		#  VIRTUAL INPUT
		#
		#################################################
		if(port.name == conf.DAWINPUT):
			if(msg.type == 'sysex'):
				if(banker.wait_for_sysex_count == 3 and banker.wait_for_sysex):
						print_debug(f"Track retrieved, and mode back to normal.",3)
						banker.can_send_sysex = True
				elif(banker.wait_for_sysex_count<7):
					banker.wait_for_sysex_count += 1
					
				if(debug_mode):
					sysex_str = sysex_text_decode(msg.hex())
					if(len(sysex_str) == 0 and banker.wait_for_sysex_count == 2):
						print_debug(f"NAME LOGIC: Case where we need 7 sysex to reset, not 3.",3)
					elif(banker.wait_for_sysex_count == 2):
						print_debug(f"NAME LOGIC: Normal 3 count case",3)
					print_debug(f"Full sysex: {sysex_str}, {len(sysex_str)=}",3)
				if(banker.wait_for_sysex):
					# rough code to return to pan mode
					#
					# count how many sysex we receive until we are fully reset after this
					# so far we end up inside this loop with count 1, so it gets here instantly, as it's also first row of sysex
					# after this we know for sure there is 1 row of bottom row for EQ mode, and then we should expect 2 more rows of pan
					#
					# once counter hits 4 sysex we should be back to normal. this gets messed up if daw sends stuff inbetween..
					# might be able to fail safe it
					# 
					#banker.wait_for_sysex_count += 1
					print_debug(f"Track Name: {sysex_text_decode(msg.hex(),48,29)}",1)
					print_debug(f"NAME LOGIC: Track name retrieval took {banker.wait_for_sysex_count=}.",3)
					nameMsg = mackiecontrol.MackieButton(MCKeys.FADERBANKMODE_PANS).onMsg
					outportVirt.send(nameMsg)
					banker.wait_for_sysex = False
					banker.wait_for_sysex_reset = True

				if(banker.bank_ping and len(msg.data)>40):
					print_debug(f"Port:{port.name} says: Bank Pong!",2)
					banker.bank_pong = True
					print_debug(f"Pong {banker.bank_pong} and Ping {banker.bank_ping} and QueuedBank {banker.bank_queued=}",2)

			if(msg.type == 'note_on' and msg.note in mcu.TrackLookup and msg.velocity == 127):
				print_debug(f"Active track msg: {msg}",3)

				# ping is pong for tracks...confusing, but live with it
				banker.track_send_ping()

				print_debug(f"Pongstatus {port.name}: {banker.track_pong} for msg: {msg}",3)


				
			if((msg.type == 'note_on' or msg.type == 'note_off') and msg.velocity==0 and msg.note == MCKeys.TRACK_CHANGE):
				print_debug(f"Received track ping from {port=}, {msg=}",3)
				banker.track_ping = True

		
			if(msg.type == 'note_on' and msg.note in [MCKeys.PREVBANK, MCKeys.NEXTBANK]):
				print_debug(f"VirtCommand {str(MCKeys(msg.note))}",3)

				print_debug(f"Virt msg sending: {msg}",3)
			if(msg.type == 'sysex' and banker.block_sysex_outport):
				"""If we are blocking sysex while fetching data, don't spam device"""
				pass
			else:
				outport.send(msg)
		# END VIRTUAL INPUT

		# HARDWARE INPUT
		if(port.name ==conf.HWINPUT):
			if(msg.type == 'note_on' and msg.velocity == 127 and msg.note in [MCKeys.PREVBANK, MCKeys.NEXTBANK]):
				print_debug(f"HWCommand {str(MCKeys(msg.note))}",4)
				banker.bank_send_ping()

			outportVirt.send(msg)
		# END HARDWARE INPUT

		# PING PONG Logic
		if(banker.bank_ping):
			now = perf_counter()
			if(banker.bank_pong):
				print_debug(f"BANK CHANGE Ping pong:{now-banker.bank_ping_time} seconds",3)
				banker.bank_reset()
				banker.track_ping = True
				banker.block_sysex_outport = False

			elif(abs(now-banker.bank_ping_time) > banker.pong_timeout):
				print_debug(f"BANK CHANGE: No Pong, end of bank list?:{now-banker.bank_ping_time} seconds",3)
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
				print_debug(f"Direction: {banker.bank_direction} and running {banker.bank_running} and queued: {banker.bank_queued}",3)

		if(banker.track_ping):
			now = perf_counter()
			if(banker.track_pong):
				
				# rough code to trigger name lookup
				name_msg = mackiecontrol.MackieButton(MCKeys.FADERBANKMODE_EQ).onMsg
				banker.can_send_sysex = False
				banker.wait_for_sysex = True
				banker.wait_for_sysex_queued = True
				banker.wait_for_sysex_count = 0
				outportVirt.send(name_msg)

				print_debug(f"TRACK CHANGE Ping pong:{now-banker.track_ping_time} seconds",3)
				banker.track_reset()

				if(banker.bank_running):
					banker.bank_found()
				# should be banker.bank_stop
				banker.bank_change_direction(reset = True)

			elif(abs(now-banker.track_ping_time) > banker.pong_timeout):
				if(banker.wait_for_sysex):
					print_debug(f"Can we try to get name here?",3)

				else:
					pass
					# name_msg = mackiecontrol.MackieButton(MCKeys.FADERBANKMODE_EQ).onMsg
					# banker.wait_for_sysex = True
					# banker.wait_for_sysex_queued = True
					# outportVirt.send(name_msg)
				# name_msg = mackiecontrol.MackieButton(MCKeys.FADERBANKMODE_EQ).onMsg
				# banker.wait_for_sysex = True
				# banker.wait_for_sysex_queued = True
				# outportVirt.send(name_msg)

				# rough code to trigger name lookup
				name_msg = mackiecontrol.MackieButton(MCKeys.FADERBANKMODE_EQ).onMsg
				banker.wait_for_sysex = True
				banker.wait_for_sysex_queued = True
				banker.wait_for_sysex_count = 0
				# outportVirt.send(name_msg)


				print_debug(f"TRACK CHANGE: No Pong, track not in bank. Auto-bank needed:{now-banker.track_ping_time} seconds",3)
				banker.track_reset()
				#
				if(banker.bank_running):
					pass
				else:
					print_debug(f"Bank search in TRACK CHANGE NO PONG",1)
					banker.bank_search()

				
				banker.bank_queued = True
		
		# PING PONG Logic
		
		if(banker.bank_queued and banker.auto_bank and not banker.wait_for_sysex_queued):
			banker.bank_queued = False
			banker.bank_send_ping()
			now=perf_counter()

			print_debug(f"In banker with status running: {banker.bank_running}",3)
			print_debug(banker.bank_messages[banker.bank_direction],4)
			#algo idea.. bank once next, and then pick up normal logic
			# if(banker.bank_first_run):
			# 		outportVirt.send(banker.bank_messages[1].onMsg)
			# 		banker.bank_first_run = False

			# else:
			# 		outportVirt.send(banker.bank_messages[banker.bank_direction].onMsg)
			outportVirt.send(banker.bank_messages[banker.bank_direction].onMsg)
			
			banker.bank_time_since_bank = perf_counter()

		if(banker.wait_for_sysex_queued):
			banker.wait_for_sysex_queued = False


		#
		#	End of Midi loop
		#


if __name__ == "__main__":

	# if len(sys.argv) < 3:
	# 	raise SyntaxError("Insufficient arguments.")
	# if len(sys.argv) != 3:
	# 	# If there are keyword arguments
	# 	main(sys.argv[1], sys.argv[2], *sys.argv[3:])
	# else:
	# 	# If there are no keyword arguments
	# 	main(sys.argv[1], sys.argv[2])
	asyncio.run(main(*sys.argv[1:]))