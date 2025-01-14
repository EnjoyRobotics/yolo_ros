# Copyright 2023 Enjoy Robotics Zrt - All Rights Reserved
#
# Unauthorized copying of this file, via any medium is strictly prohibited
# Modifications to this file is to be shared with the code owner.
# Proprietary and confidential
# Owner: Enjoy Robotics Zrt maintainer@enjoyrobotics.com, 2023

# Non-ros modules
import requests

# Ros modules
import rclpy
from rclpy.node import Node

# Ros comms
from yolo_msgs.msg import DetectionArray

class PersonNotifier(Node):
    """!@brief Node that calls an endpoint to notify about a person detection."""

    def __init__(self, *args, **kwargs):
        super().__init__('person_notifier', *args, **kwargs)

        self.declare_parameter('notify_url', 'http://127.0.0.1:5200/start_conversation')
        self.declare_parameter('notify_timeout', 0.5)
        self.declare_parameter('area_threshold', 100000)

        self.notify_url = self.get_parameter('notify_url').value
        self.notify_timeout = self.get_parameter('notify_timeout').value

        self.area_threshold = self.get_parameter('area_threshold').value

        self.sub = self.create_subscription(DetectionArray, 'yolo/detections', self.detections_callback, 10)

        self.last_response_time = self.get_clock().now()

    def detections_callback(self, msg):
        """!@brief Callback for the detection messages."""
        # If the last response was less than the timeout, do not notify
        if (self.get_clock().now() - self.last_response_time).nanoseconds < self.notify_timeout * 1e9:
            return

        for detection in msg.detections:
            if (detection.class_name == 'person' and detection.score > 0.6 and
                    detection.bbox.size.x * detection.bbox.size.y > self.area_threshold):
                self.notify_person_detected()

    def notify_person_detected(self):
        """!@brief Call the get endpoint to notify about a person detection."""
        self.get_logger().info('Person detected, notifying the endpoint')
        try:
            response = requests.get(self.notify_url, timeout=0.5)
            response.raise_for_status()

            self.last_response_time = self.get_clock().now()
        except requests.exceptions.RequestException as e:
            self.get_logger().error(f'Error while notifying the endpoint: {e}')


def main():
    rclpy.init()
    try:
        rclpy.spin(PersonNotifier())
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()

