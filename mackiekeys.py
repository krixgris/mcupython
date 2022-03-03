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
	PREVBANK = 46
	NEXTBANK = 47
	PREVTRACK = 48
	NEXTTRACK = 49
	F1 = 54
	F2 = 55
	F3 = 56
	F4 = 57