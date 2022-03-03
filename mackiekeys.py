#mackiekeys.py
#
#
from dataclasses import asdict, dataclass
from enum import Enum, IntEnum, auto, unique
from abc import ABC, abstractclassmethod

@unique
class MCKeys(IntEnum):
	TRACK1 = 24
	TRACK2 = 25
	TRACK3 = 26
	TRACK4 = 27
	TRACK5 = 28
	TRACK6 = 29
	TRACK7 = 30
	TRACK8 = 31
	
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
