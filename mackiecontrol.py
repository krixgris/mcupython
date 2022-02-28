#mackieconfig.py
#
#
from dataclasses import dataclass
from enum import Enum, auto, unique
from abc import ABC, abstractclassmethod


import json
import mido
import string


#
#	testa asdict()
#
#	testa field()
#
@unique
class MidiType(Enum):
	note_on = 'note_on'#auto()
	note_off = 'note_off'#auto()
	cc = 'control_change' #auto()
	sysex = 'sysex'#auto()


@unique
class MCType(Enum):
	note = auto()
	cc = auto()
	pitch = auto()
	sysex = auto()

class MackieNote(mido.Message):
	Msg: mido.Message
	def On(self)->mido.Message:
		return mido.Message(type='note_on', note=self.note, channel=self.channel, velocity=127)
	def Off(self)->mido.Message:
		return mido.Message(type='note_off', note=self.note, channel=self.channel, velocity=0)

@dataclass
class MackieCommand(ABC):
	key: int
	mcType: MCType = None
	state: bool = False
	#midiType: MidiType = MidiType.note_on

	#on: mido.Message = mido.Message('note_on')
	#off: mido.Message = mido.Message('note_off')
	@abstractclassmethod
	def activate(self):
		"""What happens when button is pushed/command is sent?"""
		pass
	
	@abstractclassmethod
	def reset(self):
		"""Do we need to reset state of button? What should be done? Example play button first press starts and latches, next push resets to stopped."""
		pass

	# def __post_init__(self):
	# 	self.on = mido.Message(type='note_on', note=self.key, channel=0, velocity=127)
	# 	self.off = mido.Message(type='note_off', note=self.key, channel=0, velocity=0)


# @dataclass
# class MackieButton:
# 	Name: str
# 	MidiCommand: MackieNote
# 	state: bool = False

# 	def __post_init__(self):
# 		pass
# 	def __repr__(self) -> str:
# 		return str(self.MidiCommand)

# 	# def Toggle(self)->mido.Message:
# 	# 	self.state = not self.state
# 	# 	return self.MidiCommand

@dataclass
class MackieButton(MackieCommand):

	mcType:MCType = MCType.note
	def activate(self):
		print("Activate" + str(self.key))
	def reset(self):
		pass

@dataclass
class MackiePrevNext():
	prevKey: int
	nextKey: int

	btnPrev: MackieButton = None# = MackieButton(46)
	btnNext: MackieButton = None# = MackieButton(47)
	
	def __post_init__(self):
		self.btnPrev = MackieButton(self.prevKey)
		self.btnNext = MackieButton(self.nextKey)

	def Prev(self):
		self.btnPrev.activate()
	def Next(self):
		self.btnNext.activate()

@dataclass
class MackieBank:
	##
	#	Important thing here is to check if currently selected bank has a selected track, i.e. "is this the right bank?"
	#	Ideally, we will want to ensure that we follow the selected track, so some kind of logic to also determine the smart way to find it is needed
	#
	#	Possibly implementing an autoBank()-method would be useful.
	#
	##
	BankList = "Some list of n banks. Each Bank has 8 tracks"
	change: MackiePrevNext = MackiePrevNext(46,47)
	

@dataclass
class MackieTrack:
	TrackList = "Some list of 8 tracks"
	##
	#	Selecting a track out of the 8 deselects the others. We only need to send deltas, so just sending the previous selected to reset/off and new track active is enough
	#	If track isn't in current bank, all tracks will be OFF/inactive/reset
	##
	change: MackiePrevNext = MackiePrevNext(48,49)


@dataclass
class MackieControl:
	Bank = MackieBank() ## Allows to view list of banks, as well as navigating prev/next
	Tracks = MackieTrack() ## Allows to view list of tracks, as well as navigating prev/next, Tracks live in banks. 8 tracks per bank
							## Actual MCU Controller only ever knows of 'current track list'..no concept of keeping track of banks exists
	btnF1 = MackieButton(54)
	btnF2 = MackieButton(55)
	btnF3 = MackieButton(56)
	btnF4 = MackieButton(57)

mcu = MackieControl()
mcu.Bank.change.Next()
mcu.Bank.change.Prev()
mcu.Tracks.change.Next()
mcu.Tracks.change.Prev()

mcu.btnF3.activate()




testMsg = mido.Message('sysex', data=[80, 82, 93])



# print(bytes.fromhex(testMsg.hex()))
# for h in testMsg.hex():
# 	print(h)
#test = [bytes.fromhex(h).decode('utf-8')  for h in testMsg.hex().split(" ") if h not in ["F0","F7"] and (h.isalnum())]
test = [bytes.fromhex(h).decode()  for h in testMsg.hex().split(" ") if h not in ["F0","F7"] and (h.isalnum())]
strTest:str = ""

# print(type(test))


def listToStr(l:list)->str:
	# print("infunc")
	# print(l)
	sFromList = ""
	for s in l:
		# print (s)
		sFromList += str(s)
	# print(sFromList)
	return s
strTest = listToStr(test)

# print(test)
# print("this is str")
# print(strTest)
# strTest2: str = ""
# strTest2 = strTest2.join(test)
# print (strTest2)
# print(bytes.fromhex(testMsg.hex()).decode())


# for s in str(msg.hex())[21:].split(' '):
# 					if( s.isalnum() or s.isspace):
# 						if s != 'F0' and s != 'F7':
# 							# sList.append(s.decode('hex'))
# 							#print s.decode('')
# 							sList.append(bytes.fromhex(s).decode('utf-8'))

# 				newString = "decoded hex:"
# 				decodedString = ""

# print(mcu.BankUp.MidiOn)
# print(mcu.BankUp.MidiOff)
# print(mcu.BankDown.off)
# print(mcu.BankDown.on)