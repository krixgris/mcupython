#mackiecontrol.py
#
#
from dataclasses import asdict, dataclass
from enum import Enum, auto, unique
from abc import ABC, abstractclassmethod

import mido


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
	
	@abstractclassmethod
	def activate(self):
		"""What happens when button is pushed/command is sent?"""
		pass
	
	@abstractclassmethod
	def reset(self):
		"""Do we need to reset state of button? What should be done? Example play button first press starts and latches, next push resets to stopped."""
		pass



@dataclass
class MackieButton(MackieCommand):
	active:bool = False
	mcType:MCType = MCType.note

	def activate(self):
		return str(self)

	def reset(self):
		self.active = True
		retMsg = str(self)
		self.active = False
		return str(retMsg)

	def __repr__(self):
		return str(self)

	def __str__(self):
		return (("note_off" if self.active else "note_on") + " note=" + str(self.key) + " channel=0 velocity=127")

@dataclass
class MackiePrevNext():
	prevKey: int
	nextKey: int
	#
	#	Extending this class with general names for list of items, as well as names if applicable (tracks)
	#	Since mackie has 8 tracks (or channels) per bank, we need a way to get and set tracks reliably based on position
	#	Unsure if this all goes here, or not..8 tracks is track specific not bank, so maybe inherited class?
	#

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
	# is this just redundant?
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
class MackieTrack(MackieButton):
	# is this just redundant?
	key:int
	#mcType:MCType = MCType.note
	Name:str = ""
	##
	#	Selecting a track out of the 8 deselects the others. We only need to send deltas, so just sending the previous selected to reset/off and new track active is enough
	#	If track isn't in current bank, all tracks will be OFF/inactive/reset
	##
	#change: MackiePrevNext = MackiePrevNext(48,49)

@dataclass
class MackieFaderBank:
	#
	#	Bank and Track objects instead? Which also keep lists of tracks and banks, currently selected and whatnot
	#	Might be best to extend MackiePrevNext for to avoid code duplication, general names for lists etc..
	#	
	#
	Banks: MackiePrevNext = MackiePrevNext(46,47)
	Tracks: MackiePrevNext = MackiePrevNext(48,49)

@dataclass
class MackieControl:
	FaderBank = MackieFaderBank()
	#
	Bank:None = None 	# Separate object? Holds what? List of track names? Keeps track of magic autobank?
						# 
	#
	#
	#
	#Bank = MackieBank() ## Allows to view list of banks, as well as navigating prev/next
	#Tracks = MackieTrack() ## Allows to view list of tracks, as well as navigating prev/next, Tracks live in banks. 8 tracks per bank
							## Actual MCU Controller only ever knows of 'current track list'..no concept of keeping track of banks exists
	btnF1 = MackieButton(54)
	btnF2 = MackieButton(55)
	btnF3 = MackieButton(56)
	btnF4 = MackieButton(57)

mcu = MackieControl()
mcu.FaderBank.Banks.Next()
mcu.FaderBank.Tracks.Next()

#mcu.FaderBank.TrackNext() ? NextTrack() ? Or objects inside faderbank for banks/tracks..

# mcu.Bank.change.Next()
# mcu.Bank.change.Prev()
# mcu.Tracks.change.Next()
# mcu.Tracks.change.Prev()

#print(asdict(mcu.Bank))

tracks = [MackieTrack(x+24) for x in range(8)]
for t in tracks:
	print(asdict(t))



mcu.btnF3.activate()

print("Start")
print(tracks[0].activate())

print(MackieButton(25))
msg1 = mido.Message.from_str(str(tracks[0]))
msg2 = mido.Message(type="note_off",channel=0,velocity=127,note=26, time=0)

TrackMessages = [mido.Message.from_str(str(t)) for t in tracks]

print(msg1)
print(msg2)
# this finds msg in trackmessages-list.. keep in mind note on only, which we might want?
# or figure out if we need a similar, but note off? note off handled... time is a potential issue, but can be forced to time 0
#
# this also requires us to ensure that we only compare keys in the index, so no index out of bounds.. i.e. only check for notes within 24-31
#
# smart compare possibly... or if *not* exist, query the change required?

if(msg2 in TrackMessages):
	print("Equal on note " + str(msg2.note))
else:
	print("Not Equal: " + str(msg2))
	print(TrackMessages[msg2.note-24])
	#
	TrackMessages[msg2.note-24] = msg2.copy()
	#
	#	Here we need to sync this back to the actual TrackMessages
	#
	#	Maybe smartest way is to analyze the changed message, and update what is changed
	#	Do we need to maintain both trackmessages as well as tracks here? Seems redundant
	#
	print(TrackMessages[msg2.note-24])
	print(tracks)

#print(TrackMessages)
print("Test outputs")
print(tracks[0])
print(tracks[0].activate())
print(tracks[0].reset())
print(str(tracks[0]))
print("End")