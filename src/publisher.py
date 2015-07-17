#!/usr/bin/env python3
#
# Copyright 2015 Ryan Hass
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import rospy
import trex
from std_msgs.msg import String, Bool, 

def publisher():
	pub = rospy.Publisher('trex', String, queue_size=1000)
	rospy.init_node('trex', anonymous=True)
	rate = rospy.Rate(1000) # 1 kHz
       	while not rospy.is_shutdown():
		state = trex.__trex_status
		pub.publish(', '.join(str(x) for x in state)
		rospy.loginfo("Published T'Rex Controller State")
		rate.sleep()

if __name__ = '__main__':
	try:
		publisher()
	except rospy.ROSInterruptException:
		pass
