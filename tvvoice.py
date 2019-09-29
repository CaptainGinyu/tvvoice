from aiy.board import Board, Led
from aiy.cloudspeech import CloudSpeechClient
from aiy.voice.audio import play_wav

import os
import re

import pywebostv.discovery
from pywebostv.connection import WebOSClient
from pywebostv.controls import InputControl, MediaControl

os.chdir('/home/pi/tvvoice')

board = Board()
speech_client = CloudSpeechClient()
tvClient = None
tvInputControl = None
tvMediaControl = None
store = {}

# 0 for not connected, 1 for in process of connecting, 2 for connected
connection_status = 0

def finish():
    # add shutting down sound here
    print('shutting down')
    play_wav('goodbye.wav')
    os.system('sudo shutdown -h now')
    
def changeChannelSingleDigit(d, tvInputControl):
    if d == '1':
        tvInputControl.num_1()
    elif d == '2':
        tvInputControl.num_2()
    elif d == '3':
        tvInputControl.num_3()
    elif d == '4':
        tvInputControl.num_4()
    elif d == '5':
        tvInputControl.num_5()
    elif d == '6':
        tvInputControl.num_6()
    elif d == '7':
        tvInputControl.num_7()
    elif d == '8':
        tvInputControl.num_8()
    elif d == '9':
        tvInputControl.num_9()
    elif d == '0':
        tvInputControl.num_0()

def changeChannel(num1, num2, tvInputControl):
    # num1 and num2 should be strings
    for d in num1:
        changeChannelSingleDigit(d, tvInputControl)
    if num2:
        tvInputControl.dash()
        for d in num2:
            changeChannelSingleDigit(d, tvInputControl)

def voiceToTvCmd():
    global speech_client, tvInputControl, tvMediaControl
    
    if not tvInputControl or not tvMediaControl:
        return
    
    text = speech_client.recognize(language_code = 'en-US', hint_phrases = ('change channel', 'change volume'))

    if text is None:
        return

    text = text.lower()
    
    if text == 'change channel' or text == 'change volume':
        play_wav('selectsound.wav')
        print('ok')
        num_text = speech_client.recognize(language_code = 'en-US', hint_phrases = None)
        
        if num_text is None:
            print('no number spoken')
            play_wav('errorsound.wav')
            return
        
        if text == 'change channel':
            num_regex = re.search('^(\d+)$ | ^(\d+)\.(\d+)$ | ^(\d+)\s-\s(\d+)$', num_text, re.VERBOSE)
            num1 = None
            num2 = None
            if num_regex:
                if num_regex.group(1):
                    num1 = num_regex.group(1)
                elif num_regex.group(2) and num_regex.group(3):
                    num1 = num_regex.group(2)
                    num2 = num_regex.group(3)
                elif num_regex.group(4) and num_regex.group(5):
                    num1 = num_regex.group(4)
                    num2 = num_regex.group(5)
                changeChannel(num1, num2, tvInputControl)
                print('channel changed')
            else:
                print('invalid channel number')
                play_wav('errorsound.wav')
        elif text == 'change volume':
            num_regex = re.search('^(\d+)$', num_text, re.VERBOSE)
            if num_regex and num_regex.group(1):
                vol = int(num_regex.group(1))
                tvMediaControl.set_volume(vol)
                print('volume changed')
            else:
                print('invalid volume number')
                play_wav('errorsound.wav')

def conn_attempt():
    global board, connection_status, tvClient, tvInputControl, tvMediaControl
    
    print('Attempting to connect')
    connection_status = 1
    board.led.state = Led.PULSE_QUICK
    board.button._pressed_callback = None
    
    client_list = WebOSClient.discover()
    
    if len(client_list) != 1:
        play_wav('errorsound.wav')
        print('connection failed: more than 1 tv found')
        connection_status = 0
        board.led.state = Led.OFF
        return
    
    tvClient = client_list[0]
    try:
        tvClient.connect()
        for status in tvClient.register(store):
            if status == WebOSClient.PROMPTED:
                play_wav('ding.wav')
                print('See TV prompt and press yes')
            elif status == WebOSClient.REGISTERED:
                play_wav('ding.wav')
                print('Successful connection')
                board.led.state = Led.ON
                connection_status = 2
                tvInputControl = InputControl(tvClient)
                tvInputControl.connect_input()
                tvMediaControl = MediaControl(tvClient)
    except Exception:
        play_wav('errorsound.wav')
        print('connection failed: you probably pressed no on the prompt')
        connection_status = 0
        board.led.state = Led.OFF
        return

def main():
    global board, connection_status
    
    connection_status = 0
    board.led.state = Led.OFF
    
    play_wav('bell.wav')
    print('starting...')
    
    while True:
        if connection_status == 2:
            board.button._pressed_callback = finish
            voiceToTvCmd()
        elif connection_status == 0:
            board.button._pressed_callback = conn_attempt

if __name__ == '__main__':
    main()