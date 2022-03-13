#hackiemackieutils.py
#
from datetime import datetime
import mido

#debug_mode:int = 1

MESSAGE_SEND_CRITICAL = 0
MESSAGE_SEND_IMPORTANT = 1
MESSAGE_SEND_DEBUG_LOW = 2
MESSAGE_SEND_DEBUG_MED = 3
MESSAGE_SEND_DEBUG_FULL = 4




class UtilityConfig:
	debug_mode = 1


def timestamp(nobrackets = False, debug_mode=False):
	t = datetime.now()
	formatStr = "%H:%M:%S"
	if(debug_mode):
		formatStr += ".%f"
	if(not nobrackets):
		formatStr = f"[{formatStr}]: "
	current_time = t.strftime(f"{formatStr}")
	
	return current_time

def print_debug(text:str,msg_debug_level:int=0,print_time=True, override_debug:bool=False):
	if(print_time):
		text = f"{timestamp()}{text}"
	if(msg_debug_level <= UtilityConfig.debug_mode or UtilityConfig.debug_mode >= MESSAGE_SEND_DEBUG_FULL or UtilityConfig.debug_mode<0):
			print(text)

def sysex_text_decode(sysex_hex_str, offset_pos=0, len=-1)->str:
	dehexify = [s for s in sysex_hex_str[20+offset_pos:].split(' ')]
	count = 0
	for i in dehexify:
		count+=1
	if(count+2<len):
		len = -1
	if(count < 3):
		return ""

	_,*dehexify,_ = dehexify

	dehexify = dehexify[:len]
	word = [bytes.fromhex(s).decode('utf-8') for s in dehexify]
	return ''.join(word).strip()

def long_sysex_message(*text):
	#first 6 defines stuff
	#data=(0,0,102,20,18, <-- means set display
	#6th byte defines position
	dataArray = [0,0,102,20,18,0]
	
	blank_text = ""
	for i in range(112):
		blank_text += " "
	row1,*row2 = text
	row1 = ''.join(row1)
	text = ""
	if(len(row2) == 0):
		if(len(row1)<8):
			row1 += "         "
			row1 = row1[0:7]
			for i in range(7):
				row1 += row1[0:7]
		text = row1 + blank_text
	else:
		row2 = ''.join(row2[0])
		if(len(row1)<8 and len(row2)<8):
			row1 += "         "
			row2 += "         "
			row1 = row1[0:7]
			row2 = row2[0:7]
			for i in range(7):
				row1 += row1[0:7]
				row2 += row2[0:7]
		text = row1 + blank_text
		text = text[0:56] + row2 + blank_text
	text = text[:112]

	for s in text:
		dataArray.append(ord(s))

	return(dataArray)


def sysex_mido_message(sysex_data):
	return mido.Message('sysex', data=sysex_data)


def __init__():
	print("On load...")