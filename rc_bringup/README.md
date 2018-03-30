# The main ROS node for autonomous control of the robot car
These methods do not pretend to be original, most of it I borrowed from the project of the [Erle rover](http://erlerobotics.com/blog/erle-rover/)


## Launch files
1. **bringup.launch**	- Launches main modules for work in autonomous mode 
2. **create_map.launch** - Launches for create map via hector slam
2. **tf.launch**	- setup tf
3. **mapping_default.launch**	- Hector slam node for created map  
4. **navigation.launch**- Launch costmap and move_base ("move_base" yet disabled for debugging)
5. **localizacion.launch** - AMCL (include of navigation.launch)
6. **move_base.launch**	- move_base (include of navigation.launch)
7. **odom_laser.launch**	- get tf transform of lidar
8. **rplidar.launch**	- run lidar
9. **view_navigation.launch**	- open rviz (for desktop)

## Nodes:

### 1. rc_control.py<br/>
**Description:** The pyhton script for remote control car which is directly connected to the PWM outputs pin of the RPI.<br/>
Ideally, you need to adjust the input data so that it matches the actual speed, this can be done by finding the relationship between the speed of the car and the output pulse.<br/>

#### Subscribed Topics:
rc_car/cmd_vel([geometry_msgs:Twist](http://docs.ros.org/api/geometry_msgs/html/msg/Twist.html))<br/>
where:

```
linear:
    x: forwand + / - backward 
    y: 0.0
    z: 0.0
  angular:
    x: 0.0
    y: 0.0
    z: rotate
```
#### Publisher:
**Output param**: PWM pulse

#### Parameters:
~cmd_vel (string, default: "rc_car/cmd_vel")<br/>
&emsp;&emsp;*The topic of subscribed.<br/>*
~motor_power (float, default: "0.2")<br/>
&emsp;&emsp;*The maximum power that is fed to the motor.<br/>*
~servo_pin (int, default:"4")<br/>
&emsp;&emsp;*The pin out of servo PWM<br/>*
~middle_servo (int, default:"1500")<br/>
&emsp;&emsp;*The midle position of servo<br/>*
~servo_offset (int, default:"47")<br/>
&emsp;&emsp;*The offset of servo for to correct the middle pose<br/>*
~motor_pin (int, default:"7")<br/>
&emsp;&emsp;*The pin out of motor PWM<br/>*
~middle_motor (int, default:"1550")<br/>
&emsp;&emsp;*Zero position of motor<br/>*



### 2. tf_to_vel.py<br/>
**Description:** The pyhton script for Get linear speed from TF.<br/>

#### Subscribed Topics:
tf([tf/tfMessage.msg](http://docs.ros.org/api/tf/html/msg/tfMessage.html))<br/>

#### Publisher Topics:
vel_topic [geometry_msgs:TwistStamped](http://docs.ros.org/api/geometry_msgs/html/msg/TwistStamped.html)<br/>

#### Parameters:
~vel_topic (string, default: "rc_car/velocity")<br/>
&emsp;&emsp;*Topic for publication.<br/>*
~base_link (string, default: "map")<br/>
&emsp;&emsp;*The perant tf.<br/>*
~child_link (string, default: "base_link")<br/>
&emsp;&emsp;*The child tf.<br/>*

