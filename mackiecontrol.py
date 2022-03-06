#mackiecontrol.py
#
#
from dataclasses import asdict, dataclass, field
from enum import Enum, auto, unique
from abc import ABC, abstractclassmethod

import mido

from mackiekeys import MCKeys, MCTracks, MCTracksFaderCH, MCTracksVPotCC

#
#	Conventions:
#	mido refers to channels with a 0 index, so channel 0 = 1, 1 = 2, 15 = 16 and so on
#	i tried to stay consistent with this throughout in comments etc, but it is confusing if you're used to "real midi"

#
#	General Mackie curiosity when changing tracks:
#	MCU always sends Note 54 for Edit (D#2 or D#3 depending on daw middle C)
#	as well as Note 74,75 (D4 and D#4 to get automation RW settings, as they're not stored per track)

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

	onMsg:mido.Message = field(init=False)
	offMsg:mido.Message = field(init=False)

	# def select(self)->mido.Message:
	# 	pass
	# def deselect(self)->mido.Message:
	# 	pass

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

	def __post_init__(self):
		self.onMsg = mido.Message(type='note_on',note=self.key, channel=0, velocity=127)
		self.offMsg = mido.Message(type='note_off',note=self.key, channel=0, velocity=0)

	def __repr__(self):
		return self.MidiStr

	def __str__(self):
		return self.MidiStr

@dataclass
class MackieKnob(MackieCommand):
	"""CC16-23 on channel 0"""
	mcType:MCType = MCType.cc
	ccMsg:mido.Message = field(init=False)
	pass
	def activate(self):
		pass
	def reset(self):
		pass

	def __post_init__(self):
		self.ccMsg = mido.Message(type='control_change',control=self.key, channel=0, value=0)

@dataclass
class MackieFader(MackieCommand):
	"""Pitchbend on channels 0-8 (tracks1-8 and master on channel 8"""
	mcType:MCType = MCType.pitch
	pitchMsg:mido.Message = field(init=False)
	pass
	def activate(self):
		pass
	def reset(self):
		pass
	def __post_init__(self):
		self.pitchMsg = mido.Message(type='pitchwheel', channel=self.key, pitch=0)


class MackieJogWheel(MackieCommand):
	"""CC60 on channel 1, value 1 UP, value 65 down"""
	mcType:MCType = MCType.cc
	backMsg:mido.Message = field(init=False)
	fwdMsg:mido.Message = field(init=False)

	def activate(self):
		pass
	def reset(self):
		pass
	def __post_init__(self):
		self.backMsg = mido.Message(type='control_change',control=self.key, channel=0, value=65)
		self.fwdMsg = mido.Message(type='control_change',control=self.key, channel=0, value=1)

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
class MackieTrack:
	# not redundant anymore, but inheritance is not a good idea
	# a MackieTrack should have a select track, volume fader, vpot, rec, mute, solo
	# a track number is likely a good idea as well. 1-8
	# 
	#
	# does this do anything other than a normal mackiebutton? mackiebutton might look better as mackienote... uncertain
	#
	trackindex:int
	key:int = field(init=False) # used to compare track selection from daw
	lastTrack:int = 7
	n:int = field(init=False)

	select:MackieButton = None
	rec:MackieButton = None
	solo:MackieButton = None
	mute:MackieButton = None
	vpot:MackieButton = None
	vpotCC:MackieKnob = None
	fader:MackieFader = None
	fadertouch:MackieButton = None
	
	Name:str = ""

	
	##
	#	Selecting a track out of the 8 deselects the others. We only need to send deltas, so just sending the previous selected to reset/off and new track active is enough
	#	If track isn't in current bank, all tracks will be OFF/inactive/reset
	##
	#change: MackiePrevNext = MackiePrevNext(48,49)

	@property
	def MidiMsg(self):
		return self.midiMsg
	@MidiMsg.setter
	def MidiMsg(self, msg:mido.Message):
		self.state = True if msg.type == 'note_off' else False
		self.midiMsg = msg.copy()
	
	def __post_init__(self):
		# TRACK_1 used as offset for index to get correct midi note
		#
		i = self.trackindex
		self.key = i+MCTracks.TRACK_1
		self.select = MackieButton(i+MCTracks.TRACK_1)
		self.rec = MackieButton(i+MCKeys.TRACK_1_REC)
		self.solo = MackieButton(i+MCKeys.TRACK_1_SOLO)
		self.mute = MackieButton(i+MCKeys.TRACK_1_MUTE)
		self.vpot = MackieButton(i+MCKeys.VPOT_TRACK_1)
		self.fadertouch = MackieButton(i+MCKeys.FADER_1_TOUCH)
		self.vpotCC = MackieKnob(i+MCTracksVPotCC.VPOT_CC_TRACK_1)
		self.fader = MackieFader(i+MCTracksFaderCH.FADER_TRACK_1)
		#self.TrackIndex = self.key-MCTracks.TRACK_1
		#self.midiMsg = mido.Message.from_str(self.MidiStr)

	def __repr__(self):
		return f"{self.select.mcType} {str(MCTracks(self.key))} ({MCTracks(self.key)})"
	def __int__(self):
		return self.key

	# def __next__(self):
	# 	if self.n < self.lastTrack:
	# 		result = self.n+1
	# 		self.n += 1
	# 		return result
	# 	else:
	# 		raise StopIteration


@dataclass
class MackieFaderBank:
	Banks: MackiePrevNext = MackiePrevNext(MCKeys.PREVBANK,MCKeys.NEXTBANK)
	Tracks: MackiePrevNext = MackiePrevNext(MCKeys.PREVTRACK,MCKeys.NEXTTRACK)

# @dataclass
# class MackieTrackBank:
# 	Tracks = [MackieTrack(i) for i in range(len(MCTracks))]

		

@dataclass
class MackieControl:
	track_index:int = 0 # 0-7
	ActiveBank:bool = False
	#
	# Has: 8 tracks
	# Bank selector
	# Mode selector
	# Master fader
	# Read, Automation, that changes selected track i daw (not necessary to have a selected bank/track)
	# 
	# 
	FaderBank = MackieFaderBank()
	Bank:None = None 	# Separate object? Holds what? List of track names? Keeps track of magic autobank?
	Tracks = [MackieTrack(i) for i in range(len(MCTracks))]
	TrackLookup:dict = field(init=False)
	

	PingTrack = MackieButton(MCKeys.TRACK_CHANGE)

	PrevBank = MackieButton(MCKeys.PREVBANK)
	NextBank = MackieButton(MCKeys.NEXTBANK)

	btnF1 = MackieButton(MCKeys.F1)
	btnF2 = MackieButton(MCKeys.F2)
	btnF3 = MackieButton(MCKeys.F3)
	btnF4 = MackieButton(MCKeys.F4)

	def GetActiveTrack(self):
		pass
	def SetActiveTrack(self):
		pass

	def __post_init__(self):
		#self.TrackLookup = {self.Tracks[i].key:i for i in range(len(MCTracks))}
		self.TrackLookup = {t.key:t.trackindex for t in self.Tracks}


# mcu = MackieControl()
# mcu.FaderBank.Banks.Next()
# mcu.FaderBank.Tracks.Next()



# t = MackieTrack(0)
# print(t)

# print("Start")

msg1 = None#mido.Message.from_str(str(tracks[0]))
msg2 = mido.Message(type="note_on",channel=0,velocity=127,note=MCKeys.TRACK_2, time=0)
msg3 = mido.Message(type="note_on",channel=0,velocity=127,note=int(MCKeys.TRACK_8), time=0)
#if(msg3.note in {int(t.key):t for t in mcu.Tracks}):
# if(msg3.note in mcu.TrackLookup):
# 	#print("Is equal")
# 	print(f"{msg3} is equal to {mcu.Tracks[msg3.note-MCTracks.TRACK_1].key}")


	# print(t[msg3.note-MCTracks.TRACK_1].key)

# for key in mcu.Tracks:
# 	#print("Is equal")
# 	print(str(int(key)))


# tb = MackieTrackBank()
# for t in tb:
# 	print(t)
# print(tb)

#print(dict(mcu.Tracks))
#print(type(mcu.Tracks))

#print(msg1)
#print(msg2)

# if(msg2 in [t.midiMsg for t in tracks]):
# 	print("Equal on note " + str(msg2.note))
# 	print(msg2)
# 	print(msg2.note)
# 	print(int(msg2.note))


# for i in MCTracks:
# 	print(type(i))


# TrackList = [MackieTrack(i) for i in range(len(MCTracks))]
# print(TrackList[7])

# if(msg3.note in trackDict):
# 	print("It's a trackmessage")
# else:
# 	print("Nope, not in tracklist")

#print(len(MCTracks))

# print("End")

# for s in MCKeys:
# 	print(s)
