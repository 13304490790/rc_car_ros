#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Get linear speed from TF
"""

import rospy
import tf
from geometry_msgs.msg import TwistStamped, Twist

import copy

vel_topic = "/drone/velocity"
base_link = "map"
child_link = "base_link"

prev_pose = list()
current_pos = [0.0, 0.0, 0.0]
velocity = TwistStamped()

listener = tf.TransformListener()

if __name__ == '__main__':

    rospy.init_node('tf_to_velocity_node', anonymous=True)

    # Get ros args
    name_node = rospy.get_name()
    vel_topic = rospy.get_param(name_node + '/vel_topic ', vel_topic)
    base_link = rospy.get_param(name_node + '/base_link', base_link)
    child_link = rospy.get_param(name_node + '/child_link', child_link)

    # Publisher to topic
    vel_pub = rospy.Publisher(vel_topic, TwistStamped, queue_size=1)

    old_time = rospy.get_time()
    rate = rospy.Rate(10)   # 10 hz

    while not rospy.is_shutdown():
        try:
            (trans, rot) = listener.lookupTransform(base_link, child_link, rospy.Time(0))
            current_pos[0] = trans[0]
            current_pos[1] = trans[1]
            current_pos[2] = trans[2]
            if not prev_pose:
                prev_pose = copy.deepcopy(current_pos)
        except:
            print ("false")

        if prev_pose != current_pos and prev_pose:
            try:
                dt = rospy.get_time() - old_time
                velocity.header = rospy.Header()
                velocity.twist.linear.x = (current_pos[0]-prev_pose[0]) / dt
                velocity.twist.linear.y = (current_pos[1]-prev_pose[1]) / dt
                velocity.twist.linear.z = (current_pos[2]-prev_pose[2]) / dt
            except ZeroDivisionError:
                pass
            prev_pose = copy.deepcopy(current_pos)
            vel_pub.publish(velocity)
            old_time = rospy.get_time()
        rate.sleep()