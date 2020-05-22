import RPi.GPIO as GPIO
import MySQLdb
import evdev
import time, sys
import signal
#import lcddriver
from evdev.device import InputDevice
from evdev.util import categorize
from evdev import ecodes
from datetime import date
from select import select

GPIO.setwarnings(False)

magnetic = 18
servo = 4
button = 20
dev = map(InputDevice, ('/dev/input/by-id/usb-13ba_Barcode_Reader-event-kbd', '/dev/input/by-id/usb-HXGCoLtd_27db-event-kbd'))
dev = {d.fd : d for d in dev}
#lcd = lcddriver.lcd()

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(magnetic, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    GPIO.setup(button, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    GPIO.setup(servo, GPIO.OUT)

def destroy():
    GPIO.cleanup()

def setAngle(angle):
    p = GPIO.PWM(servo, 50)
    p.start(0)
    duty = float(angle) / 10 + 2.5
    GPIO.output(servo, True)
    p.ChangeDutyCycle(duty)
    time.sleep(0.5)
    GPIO.output(servo, False)
    p.ChangeDutyCycle(0)
    p.stop()
    print("servo gerak")

def rfid():
    GPIO.add_event_detect(magnetic, GPIO.FALLING, callback=magswitch)
    keys = { 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 7, 9: 8, 10: 9 , 11: 0,}
    db = MySQLdb.connect("localhost", "admin", "rumahkaca", "greenhouse")
    cur = db.cursor()
    code = []
    uid = ""
    button_state = GPIO.input(button)
    while True:
        waktu_aktual = time.strftime("%H:%M:%S", time.localtime())
        tanggal = date.today()
        r, w, x = select(dev, [], [])

        for fd in r:
            for event in dev[fd].read():
                if fd == 3:
                    if event.type == ecodes.EV_KEY:
                        if event.value == 0:
                            if event.code != 96:
                                try:
                                    code.append(keys[event.code])
                                    if len(code) >= 10:
                                        uid = "".join(map(str, code))
                                        print("Kartu Terbaca. ID:", uid)
                                        cur.execute("SELECT kode_rfid, id_user FROM manajerial WHERE kode_rfid = '%s'" % uid)
                                        user = cur.fetchone()
                                        
                                        if not user:
                                            print("Kartu Belum Terdaftar! [",uid,"]", waktu_aktual)
                                            #lcd.clear()
                                            #lcd.lcd_display_string("Akses ditolak!", 1)
                                            continue

                                        else:                            
                                            #cur.execute("INSERT INTO log_akses (kode_rfid, waktu_masuk) VALUES ('%s', CURRENT_TIMESTAMP)" % (user[0], ))
                                            db.commit()
                                            print("Akses Masuk Diterima")
                                            setAngle(90)
                                except:
                                    code = []
                                    uid = ""
                                    
                                    
                elif fd == 4:
                    if event.type == ecodes.EV_KEY:
                        if event.value == 00:
                            if event.code != 96:
                                try:
                                    code.append(keys[event.code])
                                    if len(code) >= 10:
                                        uid = "".join(map(str, code))
                                        print("Kartu terbaca. ID:", uid)
                                        cur. execute("SELECT kode_rfid FROM manajerial WHERE kode_rfid = '%s'" % uid)
                                        user = cur.fetchone()
                                    
                                        if not user:                
                                            print("Kartu Belum Terdaftar! [",uid,"]",waktu_aktual)
                                            #lcd.lcd_display_string("Akses ditolak!", 1)
                                            continue
                                            
                                        else:
                                            cur.execute("SELECT waktu_keluar FROM log_akses l WHERE m.kode_rfid = '%s' ORDER BY waktu_masuk DESC LIMIT 1 FOR UPDATE" % uid)
                                            verify = cur.fetchone()
                                            
                                            if not verify:
                                                print("Akses ditolak!")
                                            
                                            else:
                                                #cur.execute("""UPDATE log_akses SET waktu_keluar = NOW() WHERE kode_rfid = '%s' AND waktu_keluar is NULL""" % user)
                                                db.commit()
                                                print("Akses Keluar Diterima")
                                                setAngle(0)

                                except:
                                    code = []
                                    uid = ""

def magswitch(channel):
    state = 0
    if GPIO.input(magnetic) == 1:
        print("Pintu Terbuka")
    
    else:
        print("Initating lock")
        time.sleep(3)
        if GPIO.input != 1:
            if state == 0:
                print("Mengunci pintu")
                state = 1
                setAngle(0)


if __name__ == '__main__':
    setup()
    try:
        rfid()
    except KeyboardInterrupt:
        destroy()