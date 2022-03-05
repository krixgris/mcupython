#midiconfig.py
#
from dataclasses import dataclass


@dataclass
class MidiConfig:
	HWINPUT:str = 'X-Touch One'
	HWOUTPUT:str = 'X-Touch One'
	DAWINPUT:str = 'Midihub MH-2AX2PAE Port 2'
	DAWOUTPUT:str = 'Midihub MH-2AX2PAE Port 2'

	AUTOBANK:int = 0
	DEBUGMODE:int = 1 # 1 - Debug mode, anything else will be interpreted as false
	
	DEBUGINPUT:str = 'Arturia KeyStep 32'
	DEBUGOUTPUT:str = 'Arturia KeyStep 32'