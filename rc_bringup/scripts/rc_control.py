#! /usr/bin/env python
# coding: utf-8
"""
This is Ros node for pwm control rc car
"""

import RPi.GPIO as GPIO
import pigpio
import time
import numpy as np

import rospy
from geometry_msgs.msg import Twist
from rc_bringup.msg import CarPwmContol

# init params

servo_pin = 4 # inut pin of servo
motor_pin = 17 # inut pin of motor

middle_servo = 1500
middle_motor = 1550
offset = 47.0 # offset of servo
revers_servo = False # recers of servo direction
revers_val = 1

max_vel = 1.0 # max speed if car
cmd_vel_topic = "rc_car/cmd_vel" # output topic
pwm_topic = "rc_car/pwm"

intercept_remote = False

pi = pigpio.pi()
pi.set_servo_pulsewidth(servo_pin, middle_servo) # middle servo angle
pi.set_servo_pulsewidth(motor_pin, middle_motor) # zero speed for motor (different depending on ESC)

vel_msg = Twist()
pwm_msg = CarPwmContol()

rate = 5
time_clb = 0.0

def get_angle_to_mills(angle):
    """
    calculate angle degres to pulse
    """
    return (angle / 18) + 2.5

def vel_clb(data):
    """
    Get velocity value from topic
    :param data: velocity value
    :type data: Twist

    """
    global  vel_msg, time_clb, max_vel
    vel_msg = data
    vel_msg.angular.x = np.clip(vel_msg.angular.z, -1.0, 1.0)
    vel_msg.linear.x = np.clip(vel_msg.linear.x-vel_msg.linear.y, -max_vel, max_vel)
    set_rc_remote()
    time_clb = 0.0

def vel_clb_pwm(data):
    """
    Get PWM value from topic
    :param data: velocity value
    :type data: RcCarControl

    """
    global  pwm_msg, time_clb
    pwm_msg = data
    set_rc_remote(True)
    time_clb = 0.0

def set_rc_remote(use_pwm = False):
    """
    Recalculation velocity data to pulse and set to PWM servo and motor
    :return:
    """
    global vel_msg, pwm_msg, intercept_remote, revers_val
    if use_pwm:
        if(pwm_msg.ServoPWM > 0):
                pi.set_servo_pulsewidth(servo_pin, pwm_msg.ServoPWM)
        if(pwm_msg.MotorPWM > 0):
            pi.set_servo_pulsewidth(motor_pin, pwm_msg.MotorPWM)
    else:
        # send servo
        servo_val = valmap(vel_msg.angular.z, 1*revers_val, -1*revers_val, 1000+offset, 2000+offset)
        pi.set_servo_pulsewidth(servo_pin, servo_val)
        # send motor
        if(intercept_remote and 0.0 <= vel_msg.linear.x < 0.1):
           print("return")
           return
        motor_val = valmap(vel_msg.linear.x, -2.4, 2.4, 1400, 1700)
        pi.set_servo_pulsewidth(motor_pin, motor_val)

def valmap(value, istart, istop, ostart, ostop):
    """
    Re-maps a number from one range to another.
    That is, a value of istart would get mapped to ostart,
    a value of istop to ostop, values in-between to values in-between, etc.
    :param value: value
    :param istart:  the lower bound of the value’s current range
    :param istop: the upper bound of the value’s current range
    :param ostart: the lower bound of the value’s target range
    :param ostop: the upper bound of the value’s target range
    :return: The mapped value.
    """
    val = ostart + (ostop - ostart) * ((value - istart) / (istop - istart))
    return np.clip(val, ostart, ostop)

if __name__ == "__main__":
    try:
        rospy.init_node("rc_control")
        rate = rospy.Rate(rate)

        # get args from ros params
        name_node = rospy.get_name()
        cmd_vel_topic = rospy.get_param(name_node + '/cmd_vel', cmd_vel_topic)
        pwm_topic = rospy.get_param(name_node + '/pwm_topic', pwm_topic)
        servo_pin = rospy.get_param(name_node + '/servo_pin', servo_pin)
        middle_servo = rospy.get_param(name_node + '/middle_servo', middle_servo)
        offset = rospy.get_param(name_node + '/servo_offset', offset)
        motor_pin = rospy.get_param(name_node + '/motor_pin', motor_pin)
        middle_motor = rospy.get_param(name_node + '/middle_motor', middle_motor)
        max_vel = rospy.get_param(name_node + '/max_vel', max_vel)
        revers_servo = rospy.get_param(name_node + '/revers_servo', revers_servo)
		
        if(revers_servo == True):
				revers_val = -1
        else:
				revers_val = 1
		
        rospy.Subscriber(cmd_vel_topic, Twist, vel_clb)
        rospy.Subscriber(pwm_topic, CarPwmContol, vel_clb_pwm)

		

        print ("RC_control params: \n"
               "cmd_vel_topic: %s \n"
               "pwm_toppic: %s \n"
               "servo_pin: %d \n"
               "middle_servo: %d \n"
               "servo_offset: %d \n"
               "motor_pin: %d \n"
               "middle_motor: %d \n"
               "max_vel: %f \n"
               "revers servo: %f \n" % (cmd_vel_topic, pwm_topic,servo_pin,middle_servo,offset,motor_pin,middle_motor,max_vel,revers_servo))
        while not rospy.is_shutdown():
            try:
                time_clb += 0.2
                if(time_clb > 1.0):     # if data does not come to close pwm
                    vel_msg = Twist()
                    set_rc_remote()
            except:
                time_clb += 0.2
                if(time_clb > 1.0):     # if something is wrong to close pwm
                    vel_msg = Twist()
                    set_rc_remote()
                print("error")
            rate.sleep()

    except KeyboardInterrupt:   # if put ctr+c
        print("ctrl+C exit")
        pi.set_servo_pulsewidth(servo_pin, 0)
        pi.set_servo_pulsewidth(motor_pin, 0)
        pi.stop()
        GPIO.cleanup()
    finally: # if exit
        print("exit")
        pi.set_servo_pulsewidth(servo_pin, 0)
        pi.set_servo_pulsewidth(motor_pin, 0)
        pi.stop()
        GPIO.cleanup()
