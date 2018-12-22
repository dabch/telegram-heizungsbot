#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import random
import datetime
import telepot
import glob
import time
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, ForceReply
import configparser

print('loading config from config.ini')
config = configparser.ConfigParser()
config.read('config.ini')
BOT_TOKEN = config['DEFAULT']['TOKEN']


temperature_name = ['Warmwasserebene', 'Heizebene']

threshold_warning_lower = [45, 35]                      # threshold to trigger a warning
threshold_warning_upper = [46, 36]   # threshold to reset the warning trigger, allowing the next warning to be triggered
warned = [False] * len(temperature_name)                # current state of warning for each temperature sensor

allowed_chat_ids = [9074693]


base_dir = '/sys/bus/w1/devices/'
device_folders = glob.glob(base_dir + '28*')
print(device_folders)


markup = ReplyKeyboardMarkup(keyboard=[['Temperaturabfrage']]) # needed for custom keyboard
    
def read_temp_raw(folder):
    f = open(folder + '/w1_slave', 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp():
    temp = []
    for i, folder  in enumerate(device_folders):
        lines = read_temp_raw(folder)
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = read_temp_raw()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
        temp.extend([temp_c])
    return temp

def handle(msg):
    print("Got command from %d" % msg['chat']['id'])
    chat_id = msg['chat']['id']
    command = msg['text']    
    
    if chat_id in allowed_chat_ids:
        bot.sendMessage(chat_id, 'Temperatur wird gemessen \u23F3')
        temperatures = read_temp()
        print(temperatures)
        for i, temp in enumerate(temperatures):
            bot.sendMessage(chat_id, '\U0001F321 Temperatur auf ' + temperature_name[i] + ': ' + str(temp) + ' °C', reply_markup=markup)
#        print(command)
    else:
        print('ignoring message from unauthorized person')

def send_message_to_all(message):
    for chat_id in allowed_chat_ids:
        bot.sendMessage(chat_id, message, reply_markup=markup)

bot = telepot.Bot(BOT_TOKEN)
bot.message_loop(handle)

while True:
    temperatures = read_temp()
    for i, temp in enumerate(temperatures):
        if not warned[i]:
            if temp < threshold_warning_lower[i]:
                send_message_to_all('Warnung: Temperatur auf ' + temperature_name[i] + ' zu niedrig: ' + str(temp) + ' °C \u2744 \u26C4')
                warned[i] = True
        elif warned[i]:
            if temp > threshold_warning_upper[i]:
                send_message_to_all('Temperatur auf ' + temperature_name[i] + ' wieder in Ordnung: ' + str(temp) + ' \U0001F6C0 \U0001F60D')
                warned[i] = False        
    time.sleep(60) # sleep 1 minute
