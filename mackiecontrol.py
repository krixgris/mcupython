#mackiecontrol.py
#
#
from dataclasses import asdict, dataclass
from enum import Enum, auto, unique
from abc import ABC, abstractclassmethod

import mido

from mackiekeys import MCKeys, MCTracks

#
#	Conventions:
#	mido refers to channels with a 0 index, so channel 0 = 1, 1 = 2, 15 = 16 and so on
#	i tried to stay consistent with this throughout in comments etc, but it is confusing if you're used to "real midi"

@dataclass
class MCMidiMessage:
	def NoteOn(self):
		pass
	# simpler init for mackie message that are dead simple
	# note_on = velocity 127
	# note_off = velocity 0
	# channel = 0
	pass

@unique
class MidiType(Enum):
	# perhaps tuples with type and value-column? sysex would have sysex,data, whereas note_on,note and so on
	# cc should have note as well i think, but not certain
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
	# not really used, should be removed
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

	# def MidiType(self)->tuple():
	# 	return (("note_off",0) if self.active else ("note_on",127))
	def MidiType(self, Override:bool=False,OnMessage:bool=False)->tuple():
		if(not Override):
			OnMessage = not self.active
		return (("note_off",0) if not OnMessage else ("note_on",127))

	@property
	def MidiStr(self)->str:
		#consider changing to normal method, and accept parameter to force on/off message
		return self.MidiType()[0] + " note=" + str(self.key) + " channel=0 velocity=" + str(self.MidiType()[1]) + ""

	def activate(self):
		# pointless? just use MidiStr? or change behaviour for it to make sense
		return self.MidiStr

	def reset(self):
		# ensure active is true, to generate a note OFF message to reset
		# technically speaking this should always be an off message..perhaps re-think this a little
		self.active = True
		retMsg = self.MidiStr
		self.active = False
		return str(retMsg)

	def __repr__(self):
		return self.MidiStr

	def __str__(self):
		return self.MidiStr

@dataclass
class MackieKnob(MackieCommand):
	"""CC16-23 on channel 0"""
	pass

@dataclass
class MackieFader(MackieCommand):
	"""Pitchbend on channels 0-8 (tracks1-8 and master on channel 8"""
	pass

class MackieJogWheel(MackieCommand):
	"""CC60 on channel 1, value 1 UP, value 65 down"""
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
	# is this just redundant?
	
	##
	#	Important thing here is to check if currently selected bank has a selected track, i.e. "is this the right bank?"
	#	Ideally, we will want to ensure that we follow the selected track, so some kind of logic to also determine the smart way to find it is needed
	#
	#	Possibly implementing an autoBank()-method would be useful.
	#
	##
	BankList = "Some list of n banks. Each Bank has 8 tracks"
	change: MackiePrevNext = MackiePrevNext(MCKeys.PREVBANK,MCKeys.NEXTBANK)
	

@dataclass
class MackieTrack(MackieButton):
	# is this just redundant?
	#
	# does this do anything other than a normal mackiebutton? mackiebutton might look better as mackienote... uncertain
	#
	key:int
	#state:bool = False
	#mcType:MCType = MCType.note
	midiMsg = None #must init to a type? this is over
	Name:str = ""
	##
	#	Selecting a track out of the 8 deselects the others. We only need to send deltas, so just sending the previous selected to reset/off and new track active is enough
	#	If track isn't in current bank, all tracks will be OFF/inactive/reset
	##
	#change: MackiePrevNext = MackiePrevNext(48,49)


	#
	# this whole section is sketchy as note_off etc is kept track of in 2 places which seems tricky.. 
	# is there a gain to having these objects? is it enough to just return a string?
	# 
	#
	@property
	def MidiMsg(self):
		return self.midiMsg
	@MidiMsg.setter
	def MidiMsg(self, msg:mido.Message):
		self.state = True if msg.type == 'note_off' else False
		self.midiMsg = msg.copy()
	
	def __post_init__(self):
		self.midiMsg = mido.Message.from_str(self.MidiStr)

@dataclass
class MackieFaderBank:
	#
	#	Bank and Track objects instead? Which also keep lists of tracks and banks, currently selected and whatnot
	#	Might be best to extend MackiePrevNext for to avoid code duplication, general names for lists etc..
	#	
	#
	Banks: MackiePrevNext = MackiePrevNext(MCKeys.PREVBANK,MCKeys.NEXTBANK)
	Tracks: MackiePrevNext = MackiePrevNext(MCKeys.PREVTRACK,MCKeys.NEXTTRACK)
@dataclass
class MackieTrackBank:
	Tracks = [MackieTrack(x+MCKeys.TRACK_1) for x in range(8)]
	pass

	def GetActiveTrack(self):
		pass
	def SetActiveTrack(self):
		pass


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
	btnF1 = MackieButton(MCKeys.F1)
	btnF2 = MackieButton(MCKeys.F2)
	btnF3 = MackieButton(MCKeys.F3)
	btnF4 = MackieButton(MCKeys.F4)

mcu = MackieControl()
mcu.FaderBank.Banks.Next()
mcu.FaderBank.Tracks.Next()

#mcu.FaderBank.TrackNext() ? NextTrack() ? Or objects inside faderbank for banks/tracks..

# mcu.Bank.change.Next()
# mcu.Bank.change.Prev()
# mcu.Tracks.change.Next()
# mcu.Tracks.change.Prev()

#print(asdict(mcu.Bank))

tracks = [MackieTrack(x+MCKeys.TRACK_1) for x in range(8)]

# trackDict = {x:MackieTrack(x) for x in range(MCKeys.TRACK_1,MCKeys.TRACK_8+1)}

trackDict = {t:MackieTrack(int(t)) for t in MCTracks}

for t in tracks:
	print(asdict(t))
print(trackDict)


mcu.btnF3.activate()

print("Start")
print(tracks[0].activate())

#print(MackieButton(25))
msg1 = mido.Message.from_str(str(tracks[0]))
msg2 = mido.Message(type="note_on",channel=0,velocity=127,note=MCKeys.TRACK_1, time=0)

msg3 = mido.Message(type="note_on",channel=0,velocity=127,note=MCKeys.TRACK_8, time=0)

TrackMessages = [mido.Message.from_str(str(t)) for t in tracks]

print(msg1)
print(msg2)
# this finds msg in trackmessages-list.. keep in mind note on only, which we might want?
# or figure out if we need a similar, but note off? note off handled... time is a potential issue, but can be forced to time 0
#
# this also requires us to ensure that we only compare keys in the index, so no index out of bounds.. i.e. only check for notes within 24-31
#
# smart compare possibly... or if *not* exist, query the change required?

# if(msg2 in [t.midiMsg for t in tracks]):
# 	print("Equal on note " + str(msg2.note))
# 	print(msg2)
# 	print(msg2.note)
# 	print(int(msg2.note))
# else:
# 	print("Not Equal: " + str(msg2))
# 	print(tracks[msg2.note-24].midiMsg)
# 	#
# 	print("Updating from: " + str(msg2))
# 	tracks[msg2.note-MCKeys.TRACK_1].MidiMsg = msg2.copy()

# 	print("Updated: " + str(tracks[msg2.note-MCKeys.TRACK_1].MidiMsg))

	#
	#	Here we need to sync this back to the actual TrackMessages
	#
	#	Maybe smartest way is to analyze the changed message, and update what is changed
	#	Do we need to maintain both trackmessages as well as tracks here? Seems redundant
	#
	#	Do we care?
	#
	# print(tracks[msg2.note-MCKeys.TRACK_1])
	
	#print(tracks)
# print(tracks[msg2.note-MCKeys.TRACK_1].MidiStr)
	
#print(TrackMessages)
#print("Test outputs")
# print(tracks[0])
# print(tracks[0].activate())
# print(tracks[0].reset())
# print(str(tracks[0]))

for i in MCTracks:
	print(type(i))

if(msg3.note in trackDict):
	print("It's a trackmessage")
else:
	print("Nope, not in tracklist")

print("End")

# for s in MCKeys:
# 	print(s)
