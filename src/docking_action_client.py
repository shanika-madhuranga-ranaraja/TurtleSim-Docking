#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from turtlesim.msg import Pose
from project1.action import Docking


class DockingActionClient(Node):

    def __init__(self):
        super().__init__('docking_action_client')

        self.declare_parameter('action_name', '/dock')
        self.declare_parameter(
            'initial_pose',
            [0.0, 0.0, 0.0]
        )
        self.declare_parameter(
            'docking_pose',
            [0.0, 0.0, 0.0]
        )
        self.declare_parameter(
            'initial_pose_tolerance',
            0.20
        )

        self.action_name = self.get_parameter(
            'action_name'
        ).value

        self.initial_pose = self.get_parameter(
            'initial_pose'
        ).value

        self.docking_pose = self.get_parameter(
            'docking_pose'
        ).value

        self.initial_pose_tolerance = float(
            self.get_parameter(
                'initial_pose_tolerance'
            ).value
        )

        self.goal_sent = False

        self.action_client = ActionClient(
            self,
            Docking,
            self.action_name
        )

        self.pose_sub = self.create_subscription(
            Pose,
            'pose',
            self.pose_callback,
            10
        )

        self.get_logger().info(
            'Waiting for correct initial turtle pose...'
        )

    def pose_callback(self, msg):
        if self.goal_sent:
            return

        distance_from_start = math.hypot(
            msg.x - self.initial_pose[0],
            msg.y - self.initial_pose[1]
        )

        if distance_from_start <= self.initial_pose_tolerance:
            self.goal_sent = True

            self.get_logger().info(
                'Correct initial pose detected. '
                'Sending docking goal.'
            )

            self.send_goal()

    def send_goal(self):
        self.action_client.wait_for_server()

        goal_msg = Docking.Goal()
        goal_msg.x = float(self.docking_pose[0])
        goal_msg.y = float(self.docking_pose[1])
        goal_msg.psi = float(self.docking_pose[2])

        future = self.action_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        )

        future.add_done_callback(
            self.goal_response_callback
        )

    def goal_response_callback(self, future):
        goal_handle = future.result()

        if not goal_handle.accepted:
            self.get_logger().info('Goal rejected.')
            return

        self.get_logger().info('Goal accepted.')

        result_future = goal_handle.get_result_async()

        result_future.add_done_callback(
            self.result_callback
        )

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback

        self.get_logger().info(
            f'{feedback.stage} | '
            f'x={feedback.current_x:.2f}, '
            f'y={feedback.current_y:.2f}, '
            f'theta={feedback.current_theta:.2f}, '
            f'd={feedback.distance_remaining:.2f}'
        )

    def result_callback(self, future):
        result = future.result().result

        self.get_logger().info(
            f'Result: success={result.success} | '
            f'{result.message}'
        )


def main(args=None):
    rclpy.init(args=args)

    node = DockingActionClient()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
