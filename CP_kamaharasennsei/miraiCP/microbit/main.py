from microbit import *

while True:
    x = accelerometer.get_x()
    y = accelerometer.get_y()
    z = accelerometer.get_z()
    a = 1 if button_a.is_pressed() else 0
    b = 1 if button_b.is_pressed() else 0
    print(x, y, z, a, b)
    sleep(20)
