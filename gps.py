'''
  Use adafruiy gps
'''
import serial
import adafruit_gps

class AdafruitGPS():
    def __init__(self):
        print("abba")
        ser = serial.Serial("/dev/tty.usbserial-240", 9600)

        self.serial_num = ''
        ser.write(b'PMTK605*31')
        print(ser.read(ser.in_waiting).decode('utf-8'), end="==============")

        # print("serial_num:", self.serial_num)
        # print(ser.name)
        last_ri = ser.ri
        while True:
            if ser.ri != last_ri:
                last_ri = ser.ri
                if last_ri:
                    print("\n---------- Pulse high ----------")
                else:
                    print("\n---------- Pulse low ----------")
            if ser.in_waiting:
                    print(ser.read(ser.in_waiting).decode('utf-8'), end="")



if __name__ == "__main__":
    x = AdafruitGPS()

