# Importing Modules

import os
import time
import csv
import RPi.GPIO as GPIO
import evdev
import sys

from time import sleep
from pyfingerprint.pyfingerprint import PyFingerprint
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306, ssd1325, ssd1331, sh1106

# Subject

subject = ""

# OLED display stuff

serial = i2c(port=1, address=0x3C)
device = ssd1306(serial, rotate=0)

# Keyboard stuff

L1 = 5
L2 = 6
L3 = 13
L4 = 19

C1 = 12
C2 = 16
C3 = 20
C4 = 21

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(L1, GPIO.OUT)
GPIO.setup(L2, GPIO.OUT)
GPIO.setup(L3, GPIO.OUT)
GPIO.setup(L4, GPIO.OUT)

GPIO.setup(C1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(C2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(C3, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(C4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Initialising the fingerprint sensor

try:
    f = PyFingerprint('/dev/ttyUSB0', 57600, 0xFFFFFFFF, 0x00000000)
except Exception as e:
    f = PyFingerprint('/dev/ttyUSB1', 57600, 0xFFFFFFFF, 0x00000000)
except Exception as e:
    print(str(e))
    
# Making the data folder
    
if not os.path.exists('data/'):
    os.makedirs('data/')

# Grabbing the time
 
date = time.strftime("%d-%m-%Y", time.localtime())    
    
# Funtions

def subject_select(): # Select Subject
	global subject
	with canvas(device) as draw:
		draw.text((0, 0), ":SELECT SUBJECT:", fill="white")
		draw.text((0, 20), "1 - BSCH101 CHEM", fill="white")
		draw.text((0, 30), "2 - BSM201 MATH", fill="white")
		draw.text((0, 40), "3 - ESCS201 COMP", fill="white")
		draw.text((0, 50), "4 - HMHU201 ENG", fill="white")
	sleep(0.2)
	while True:
		if read_keypad() == "1":
			subject = "BSCH101"
			break
		if read_keypad() == "2":
			subject = "BSM201"
			break
		if read_keypad() == "3":
			subject = "ESCS201"
			break
		if read_keypad() == "4":
			subject = "HMHU201"
			break
	with canvas(device) as draw: draw.text((0, 0), "SELECTED " + subject, fill="white")
	print("SELECTED " + subject)
	sleep(1)

def read_keypad():
    keys = [
        ["1", "2", "3", "A"],
        ["4", "5", "6", "B"],
        ["7", "8", "9", "C"],
        ["*", "0", "#", "D"]
    ]
    lines = [L1, L2, L3, L4]
    columns = [C1, C2, C3, C4]
    output = ""
    for i, line in enumerate(lines):
        GPIO.output(line, GPIO.HIGH)
        for j, column in enumerate(columns):
            if GPIO.input(column) == 1:
                output = keys[i][j]
                print(output)
        GPIO.output(line, GPIO.LOW)
    return output 

def show_data(): #Shows The number of fingerprints
	print('COUNT: ' + str(f.getTemplateCount()) + '\n')
	print("SUBJECT: " + subject)
	with canvas(device) as draw: 
		draw.text((0, 0), "COUNT: " + str(f.getTemplateCount()), fill="white")
		draw.text((0, 10), "SUBJECT: " + subject, fill="white")
	sleep(2)
	
def clear_database(): #Clears the database 
	f.clearDatabase()
	with canvas(device) as draw: draw.text((0, 0), "DATA CLEARED", fill="white")
	file1 = open('studentdata.csv','w')
	file1.close()
	print('All Data Cleared\n')
	sleep(3)

def attendance(): #Takes attendance
	if subject == "": subject_select()
	time_tuple = time.localtime()
	samay = time.strftime('%H:%M', time_tuple)
	print('TIME: ',samay)
	
	try:
		print('PLACE FINGER...\n')
		time.sleep(1)
	
		while (f.readImage() == False):
			with canvas(device) as draw:
				draw.text((0, 0), "PLACE FINGER...", fill="white")
				draw.text((0, 10), subject + " " + samay, fill="white")
				sleep(0.1)
			pass
		
		f.convertImage()  
		result = f.searchTemplate()
		
		if result[0] == -1:
			print('NO MATCH TRY AGAIN...' + '\n')
			with canvas(device) as draw:
				draw.text((0, 0), "NO MATCH", fill="white")
				draw.text((0, 10), "TRY AGAIN...", fill="white")
			sleep(3)
			return None
		
		else:
			if not os.path.exists(f'data/{date}_{subject}.csv'):
				with open(f'data/{date}_{subject}.csv', 'w') as file2:
					csvout = csv.writer(file2)
					csvout.writerow(['Roll','Name','Subject','Time In','Time Out'])
	
			print('FOUND TEMPLATE' + str(result[0]+1) + '\n')
		
			with open('studentdata.csv','r') as file1:
				with open(f'data/{date}_{subject}.csv', 'r') as file2:
					csvread = csv.reader(file1)
					csvread2 = csv.reader(file2)
					csvwrite2 = csv.writer(file2)
	
					for row in csvread:
						if row[0] == str(result[0]+1):
							roll = str(row[1])
							name = str(row[2])
							dept = str(row[3])
							year = str(row[4])
							print('Roll no: ',roll)
							print('Name: ',name)
							print('Department: ',dept)
							print('Year: ',year)
							print('Time: ',samay)
							
			with canvas(device) as draw:
				draw.text((0, 0), "REGISTERING...", fill="white")
				draw.text((0, 20), name, fill="white")
				draw.text((0, 30), roll, fill="white")
				draw.text((0, 40), dept, fill="white")
				draw.text((0, 50), year, fill="white")
			sleep(3)  
			
		with open(f'data/{date}_{subject}.csv', 'r') as file:
			reader = csv.reader(file)
			rows = list(reader)
		present = 1    
		
		for i in rows:
			if i[1] == name:
				i.append(samay)
				present = 0
				break
		
		if present == 1:
			rows.append([roll,name,subject,samay])        
        
		with open(f'data/{date}_{subject}.csv', 'w') as file:
			writer = csv.writer(file)
			writer.writerows(rows)
									
	except Exception as e:
		print('Operation Failed- Exception message: '+str(e) + '\n')       

def main_menu() :
	while True:
		with canvas(device) as draw:
			draw.text((0, 0), "1 - ATTENDENCE", fill="white")
			draw.text((0, 10), "2 - SELECT SUBJECT", fill="white")
			draw.text((0, 20), "3 - SHOW DATA", fill="white")
			draw.text((0, 30), "4 - SHUT DOWN", fill="white")
			
		if read_keypad() == "1": 
			attendance()
		if read_keypad() == "2": 
			subject_select()
		if read_keypad() == "3":
			show_data()
		if read_keypad() == "4":
			return 1

# Main Funtion

if __name__ == '__main__':
	if main_menu() == 1:
		os.system("sudo shutdown now")
		sys.exit()
