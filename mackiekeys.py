#mackiekeys.py
#
#
from dataclasses import asdict, dataclass
from enum import Enum, IntEnum, auto, unique
from abc import ABC, abstractclassmethod

#
#	General MCU "Good to know"
#
#	G#6 (104) Note on means fader is touched, G#6 note off means released. this *might* be the first fader only, as I only have a single fader. multiple fader units likely use more
#	Pitchwheel data goes from -8192 up to 8188
#
#	CH SELECT sends the corresponding channel, so if current track is TRACK_7 then it sends TRACK_7
#
#	Similarly, vpot click sends from G#0 (32) up to D#1 (39) depending on selected track. Only an "issue" for single fader controllers such as the X-Touch One
#
#	Keep in mind that the actual HW will send note_on, note_off pairs, and this might not be what we get back from DAW
#	Likely daw wont care about the note_off, so this might be unnecessary to keep track of if we want to mimic behaviour
#

@unique
class MCJogWheel(IntEnum):
	CC = 63
	BACK = 65
	FWD = 1

@unique
class MCTracksFaderCH(IntEnum):
	"""CHANNELS, not CC nor Notes"""
	FADER_TRACK_1 = 0
	FADER_TRACK_2 = 1
	FADER_TRACK_3 = 2
	FADER_TRACK_4 = 3
	FADER_TRACK_5 = 4
	FADER_TRACK_6 = 5
	FADER_TRACK_7 = 6
	FADER_TRACK_8 = 7

	FADER_MASTER = 8

@unique
class MCTracksVPotCC(IntEnum):
	"""Note that these are CC, and not notes and I assume these run up to just before note 24 to keep logic simpler"""
	VPOT_CC_TRACK_1 = 16
	VPOT_CC_TRACK_2 = 17
	VPOT_CC_TRACK_3 = 18
	VPOT_CC_TRACK_4 = 19
	VPOT_CC_TRACK_5 = 20
	VPOT_CC_TRACK_6 = 21
	VPOT_CC_TRACK_7 = 22
	VPOT_CC_TRACK_8 = 23

@unique
class MCTracksSMR(IntEnum):
	"""NOTES, depends on selected channel"""
	TRACK_1_REC = 0
	TRACK_2_REC = 1
	TRACK_3_REC = 2
	TRACK_4_REC = 3
	TRACK_5_REC = 4
	TRACK_6_REC = 5
	TRACK_7_REC = 6
	TRACK_8_REC = 7

	TRACK_1_SOLO = 8
	TRACK_2_SOLO = 9
	TRACK_3_SOLO = 10
	TRACK_4_SOLO = 11
	TRACK_5_SOLO = 12
	TRACK_6_SOLO = 13
	TRACK_7_SOLO = 14
	TRACK_8_SOLO = 15

	TRACK_1_MUTE = 16
	TRACK_2_MUTE = 17
	TRACK_3_MUTE = 18
	TRACK_4_MUTE = 19
	TRACK_5_MUTE = 20 
	TRACK_6_MUTE = 21
	TRACK_7_MUTE = 22
	TRACK_8_MUTE = 23



@unique
class MCTracks(IntEnum):
	TRACK_1:int = 24
	TRACK_2:int = 25
	TRACK_3:int = 26
	TRACK_4:int = 27
	TRACK_5:int = 28
	TRACK_6:int = 29
	TRACK_7:int = 30
	TRACK_8:int = 31

@unique
class MCTracksVPots(IntEnum):
	# Encoder clicks send notes
	VPOT_TRACK_1 = 32
	VPOT_TRACK_2 = 33
	VPOT_TRACK_3 = 34
	VPOT_TRACK_4 = 35
	VPOT_TRACK_5 = 36
	VPOT_TRACK_6 = 37
	VPOT_TRACK_7 = 38
	VPOT_TRACK_8 = 39


@unique
class MCKeys(IntEnum):
	"""NOTES - Contains all Mackie note events"""
	TRACK_1_REC = 0
	TRACK_2_REC = 1
	TRACK_3_REC = 2
	TRACK_4_REC = 3
	TRACK_5_REC = 4
	TRACK_6_REC = 5
	TRACK_7_REC = 6
	TRACK_8_REC = 7

	TRACK_1_SOLO = 8
	TRACK_2_SOLO = 9
	TRACK_3_SOLO = 10
	TRACK_4_SOLO = 11
	TRACK_5_SOLO = 12
	TRACK_6_SOLO = 13
	TRACK_7_SOLO = 14
	TRACK_8_SOLO = 15

	TRACK_1_MUTE = 16
	TRACK_2_MUTE = 17
	TRACK_3_MUTE = 18
	TRACK_4_MUTE = 19
	TRACK_5_MUTE = 20 
	TRACK_6_MUTE = 21
	TRACK_7_MUTE = 22
	TRACK_8_MUTE = 23
	
	TRACK_1 = 24
	TRACK_2 = 25
	TRACK_3 = 26
	TRACK_4 = 27
	TRACK_5 = 28
	TRACK_6 = 29
	TRACK_7 = 30
	TRACK_8 = 31
	
	VPOT_TRACK_1 = 32
	VPOT_TRACK_2 = 33
	VPOT_TRACK_3 = 34
	VPOT_TRACK_4 = 35
	VPOT_TRACK_5 = 36
	VPOT_TRACK_6 = 37
	VPOT_TRACK_7 = 38
	VPOT_TRACK_8 = 39

	FADERBANKMODE_ROUTING = 40
	FADERBANKMODE_SENDS = 41
	FADERBANKMODE_PANS = 42
	FADERBANKMODE_PLUGIN = 43
	FADERBANKMODE_EQ = 44
	FADERBANKMODE_INSTRUMENT = 45
	
	PREVBANK = 46
	NEXTBANK = 47
	PREVTRACK = 48
	NEXTTRACK = 49

	DISPLAY_NAME = 52 # Toggles lcd display top row to show for instance Pan etc..or the values of Pan
	DISPLAY_BEATS = 53 # Time based or beats

	F1 = 54
	F2 = 55
	F3 = 56
	F4 = 57
	F5 = 58
	F6 = 59
	F7 = 60
	F8 = 61

	#
	# Span 62-69 is unknown for now
	# Guesstimations suggest part of the range, or the full range covers F5-F8 as well as shifted-versions of F1-F8
	#

	UNDO = 70
	REDO = 71

	SAVE = 72 #untested
	REVERT = 73 #untested

	TRACKCONTROL_READAUTO = 74
	TRACKCONTROL_WRITEAUTO = 75

	SENDS = 76 #untested
	PROJECT = 77 #seems to go back to project window from for instance mixer, maybe instrument too? needs testing
	MIXER = 78 # opens mixconsole 1
	MOTOR = 79 # Can be useful to switch off when doing crazy things
	INSTRUMENT = 80 # Not sure, some vst connection
	MASTER = 81 # Not the same as master button, need to figure out
	SOLO_DEFEAT = 82 # Needs investigating, as solo defeat tends to be per track 
	SHIFT = 83 #untested


	TRANSPORT_TO_STARTOFCYCLE = 84 #untested
	TRANSPORT_TO_ENDOFCYCLE = 85 #untested
	TRANSPORT_CYCLE = 86
	TRANSPORT_PUNCH = 87

	MARKERS_PREV = 88
	MARKERS_ADD = 89
	MARKERS_NEXT = 90

	TRANSPORT_RRW = 91
	TRANSPORT_FFW = 92
	TRANSPORT_STOP = 93
	TRANSPORT_PLAY = 94
	TRANSPORT_REC = 95

	UP = 96
	DOWN = 97
	LEFT = 98
	RIGHT = 99
	MIDDLE = 100

	SCRUB = 101
	#
	# Span 102-103 is unknown for now
	#
	FADER_1_TOUCH = 104
	FADER_2_TOUCH = 105
	FADER_3_TOUCH = 106
	FADER_4_TOUCH = 107
	FADER_5_TOUCH = 108
	FADER_6_TOUCH = 109
	FADER_7_TOUCH = 110
	FADER_8_TOUCH = 111
	FADER_MASTER_TOUCH = 112
	#
	# Span 112-127 is unknown for now
	#
