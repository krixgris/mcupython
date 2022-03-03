#mackiekeys.py
#
#
from dataclasses import asdict, dataclass
from enum import Enum, IntEnum, auto, unique
from abc import ABC, abstractclassmethod


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
class MCKeys(IntEnum):
	TRACK_1 = 24
	TRACK_2 = 25
	TRACK_3 = 26
	TRACK_4 = 27
	TRACK_5 = 28
	TRACK_6 = 29
	TRACK_7 = 30
	TRACK_8 = 31
	
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
	F1 = 54
	F2 = 55
	F3 = 56
	F4 = 57
