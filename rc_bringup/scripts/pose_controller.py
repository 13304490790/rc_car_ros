#! /usr/bin/env python
# coding: utf-8
"""
This pos controller for like-car robot
"""

import math
import numpy as np
from PID import PID
import time
import rospy
import tf
from geometry_msgs.msg import Twist, Pose, TwistStamped, PoseStamped
from geometry_msgs.msg import Twist
from dynamic_reconfigure.server import Server
from rc_bringup.cfg import PoseControllerConfig

#value
velocity = float()
cmd_vel_msg = Twist()
current_pose = Pose()
current_course = float()
goal_pose = Pose()

init_flag = False
max_vel = 1.1 # m/s
min_vel = -1.5 # m/s
max_angle = math.radians(25)

#PID
pid_pose = PID()
pid_course = PID()

pid_pose.setWindup(max_vel)
pid_course.setWindup(max_angle)

goal_tolerance = 0.4

finish_flag = True

kP_pose = 1.0
kI_pose = 0.0
kD_pose = 0.2

kP_course = 0.5
kI_course = 0.0
kD_course = 0.2

#errors
error_course = float()
error_dist = float()

#topics
cmd_vel_topic = "/cmd_vel"
vel_topic = "velocity"
goal_topic = "move_base_simple/goal"
#tf
base_link = "/map"
child_link = "/base_link"

# geometry methods
def vector_from_course(rot):
    """
    Get vector of car direction
    :param rot: course angle
    :return: return vector
    """
    rotate = np.array([[math.cos(rot), -math.sin(rot)],
    [math.sin(rot), math.cos(rot)]])

    pos = np.array([[10.0],[0.0]])
    vector = np.dot(rotate,pos)
    return vector

def angle_between_vec(p1, p2):
    ang1 = np.arctan2(*p1[::-1])
    ang2 = np.arctan2(*p2[::-1])
    res = (ang1 - ang2) % (2 * np.pi)
    if res > math.pi:
        res -= 2.0 * math.pi
    if res < -math.pi:
        res += 2.0 * math.pi
    return res

def get_distance_to(a,b):
    """
    get distance to goal point
    :type a: Pose
    :type b: Pose
    :type dist: float
    :param a: current pose
    :param b: goal pose
    :param dist: distance
    :return: dist
    """
    pos = np.array([[b.position.x - a.position.x],
                    [b.position.y - a.position.y]])
    dist = np.linalg.norm(pos)
    return dist

def get_errors():
    """
    Get errors for controller
    """
    global current_pose, goal_pose, current_course, \
        error_course, error_dist

    #get error from course
    v1 = vector_from_course(current_course)
    v2 = [goal_pose.position.x-current_pose.position.x, goal_pose.position.y-current_pose.position.y]
    error_course = angle_between_vec(v1,v2)

    #get error from distance
    error_dist = get_distance_to(current_pose, goal_pose)

# Controller
def get_control():
    """
    This is main controller
    :return: cmd_vel
    """
    global velocity, cmd_vel_msg, error_dist, \
        error_course, pid_pose, \
        pid_course, finish_flag, \
        goal_tolerance

    setPIDk()
    if (abs(error_course) > math.radians(80)):
        error_dist = -error_dist
        print("error_course > 80")
        error_course = -error_course
    
    pid_pose.update(error_dist)
    cmd_vel_msg.linear.x = -pid_pose.output

    pid_course.update(error_course)
    cmd_vel_msg.angular.z = pid_course.output

    # print("out angle:", pid_course.output)
    # clip velicity between min < cmd_vel < max
    cmd_vel_msg.linear.x = np.clip(cmd_vel_msg.linear.x, min_vel, max_vel)

    if(abs(error_dist) < goal_tolerance):
        finish_flag = True

    print("error_dist:", error_dist, "error_course", math.degrees(error_course))
    return  cmd_vel_msg

def setPIDk():
    """
    update PID coefficients
    :return:
    """
    global pid_pose, pid_course
    global kP_pose, kI_pose, kD_pose, \
        kP_course, kI_course, kD_course

    pid_pose.setKp(kP_pose)
    pid_pose.setKi(kI_pose)
    pid_pose.setKd(kD_pose)

    pid_course.setKp(kP_course)
    pid_course.setKi(kI_course)
    pid_course.setKd(kD_course)

# ROS callback
def vel_clb(data):
    """
    Get current velocity from rc car
    :type data: TwistStamped
    """
    global velocity
    velocity = math.sqrt(data.twist.linear.x ** 2 + data.twist.linear.y ** 2)

def goal_clb(data):
    """
    Get goal pose
    :type data: PoseStamped
    """
    global goal_pose, init_flag, current_pose, finish_flag
    goal_pose = data.pose
    init_flag = True
    finish_flag = False

def cfg_callback(config, level):
    global max_vel, min_vel, max_angle, kP_pose, kI_pose, kD_pose,kP_course, kI_course, kD_course

    print("config")
    max_vel = float(config["max_vel"])
    min_vel = float(config["min_vel"])
    max_angle = math.radians(float(config["max_angle"]))

    kP_pose = float(config["kP_pose"])
    kI_pose = float(config["kI_pose"])
    kD_pose = float(config["kD_pose"])
    kP_course = float(config["kP_course"])
    kI_course = float(config["kI_course"])
    kD_course = float(config["kD_course"])
    return config

if __name__ == "__main__":

    # init ros node
    rospy.init_node('rc_pos_controller', anonymous=True)
    rate = rospy.Rate(20)  # 10hz

    # Get ros args
    vel_topic = rospy.get_param('~vel_topic ', vel_topic)
    cmd_vel_topic = rospy.get_param('~cmd_vel', cmd_vel_topic)
    goal_topic = rospy.get_param('~goal_topic', goal_topic)
    base_link = rospy.get_param('~base_link', base_link)
    child_link = rospy.get_param('~child_link', child_link)

    max_vel = rospy.get_param('~max_vel', max_vel)
    min_vel = rospy.get_param('~min_vel', min_vel)
    max_angle = rospy.get_param('~max_angle', max_angle)
    goal_tolerance = rospy.get_param('~goal_tolerance', goal_tolerance)

    kP_pose = rospy.get_param('~kP_pose', kP_pose)
    kI_pose = rospy.get_param('~kI_pose', kI_pose)
    kD_pose = rospy.get_param('~kD_pose', kD_pose)
    kP_course = rospy.get_param('~kP_course', kP_course)
    kI_course = rospy.get_param('~kI_course', kI_course)
    kD_course = rospy.get_param('~kD_course', kD_course)

    # start subscriber
    rospy.Subscriber(vel_topic, TwistStamped, vel_clb)
    rospy.Subscriber(goal_topic, PoseStamped, goal_clb)
    vec_pub = rospy.Publisher(cmd_vel_topic, Twist,  queue_size=10)
    cfg_srv = Server(PoseControllerConfig, cfg_callback)

    listener = tf.TransformListener()
    old_ros_time = rospy.get_time()

    try:
        while not rospy.is_shutdown():
            dt = rospy.get_time() - old_ros_time

            try:
                (trans, rot) = listener.lookupTransform(base_link, child_link, rospy.Time(0))
                current_pose.position.x = trans[0]
                current_pose.position.y = trans[1]
                current_pose.position.z = trans[2]
                current_pose.orientation.x = rot[0]
                current_pose.orientation.y = rot[1]
                current_pose.orientation.z = rot[2]
                current_pose.orientation.w = rot[3]
                # # convert euler from quaternion
                (roll, pitch, yaw) = tf.transformations.euler_from_quaternion(rot)
                current_course = yaw
                print(current_pose)
            except:
                print("tf not found")
                continue

            if(not init_flag):
                print("not init")
                continue

            old_ros_time = rospy.get_time()

            get_errors()

            cmd_vel_msg = get_control()

            if finish_flag:
                print("finish_flag True")
                cmd_vel_msg.linear.x = 0.0

            vec_pub.publish(cmd_vel_msg) # publish msgs to the robot
            rate.sleep()
    except KeyboardInterrupt:   # if put ctr+c
        exit(0)