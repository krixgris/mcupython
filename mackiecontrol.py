#mackieconfig.py
#
#
from dataclasses import dataclass
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

	mcType:MCType = MCType.note
	def activate(self):
		print("Activate" + str(self.key))
	def reset(self):
		pass

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
	TrackList = "Some list of 8 tracks, or just one track? Extend mackiecommmand for selection?"
	##
	#	Selecting a track out of the 8 deselects the others. We only need to send deltas, so just sending the previous selected to reset/off and new track active is enough
	#	If track isn't in current bank, all tracks will be OFF/inactive/reset
	##
	change: MackiePrevNext = MackiePrevNext(48,49)

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
	Bank = MackieBank() ## Allows to view list of banks, as well as navigating prev/next
	Tracks = MackieTrack() ## Allows to view list of tracks, as well as navigating prev/next, Tracks live in banks. 8 tracks per bank
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

mcu.btnF3.activate()