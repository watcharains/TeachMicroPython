import machine
from machine import Pin, PWM
import utime

M1A = PWM(Pin(3))
M1B = PWM(Pin(2))
M2A = PWM(Pin(4))
M2B = PWM(Pin(5))

M1A.freq(500)
M1B.freq(500)
M2A.freq(500)
M2B.freq(500)

def robotForWard(pwmvalue):
    print("Forward")
    M1A.duty_u16(0)     # Duty Cycle must be between 0 until 65535
    M1B.duty_u16(pwmvalue)
    M2A.duty_u16(0)
    M2B.duty_u16(pwmvalue)
    
def robotBackWard(pwmvalue):
    print("Backward")
    M1A.duty_u16(pwmvalue)     # Duty Cycle must be between 0 until 65535
    M1B.duty_u16(0)
    M2A.duty_u16(pwmvalue)
    M2B.duty_u16(0)
    
def robotStop():
    M1A.duty_u16(0)     # Duty Cycle must be between 0 until 65535
    M1B.duty_u16(0)
    M2A.duty_u16(0)
    M2B.duty_u16(0)
