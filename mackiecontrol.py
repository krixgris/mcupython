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
		self.pitchMsg = mido.Message(type='pitchwheel', channel=self.key, pitch=4672)


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
class MackieTrack:
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

	def __repr__(self):
		return f"{self.select.mcType} {str(MCTracks(self.key))} ({MCTracks(self.key)})"
	def __int__(self):
		return self.key

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