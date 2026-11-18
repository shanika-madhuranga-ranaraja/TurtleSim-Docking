#!/usr/bin/env python3

import math
import time

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, GoalResponse, CancelResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor

from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
from project1.action import Docking


def normalize_angle(angle):
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


def should_stop_straight(
    distance_to_goal,
    travelled_distance,
    planned_distance,
    tolerance
):

    if distance_to_goal <= tolerance:
        return True

    if travelled_distance >= planned_distance:
        return True

    return False


class DockingActionServer(Node):

    def __init__(self):
        super().__init__('docking_action_server')

        self.declare_parameter('action_name', '/dock')
        self.declare_parameter('linear_velocity', 0.2)
        self.declare_parameter('angular_velocity', 0.25)
        self.declare_parameter('position_tolerance', 0.1)
        self.declare_parameter('angle_tolerance', 0.005)

        self.action_name = self.get_parameter('action_name').value
        self.linear_velocity = float(
            self.get_parameter('linear_velocity').value
        )
        self.angular_velocity = float(
            self.get_parameter('angular_velocity').value
        )
        self.position_tolerance = float(
            self.get_parameter('position_tolerance').value
        )
        self.angle_tolerance = float(
            self.get_parameter('angle_tolerance').value
        )

        self.pose = None
        self.last_feedback_time = 0.0

        self.callback_group = ReentrantCallbackGroup()

        self.cmd_pub = self.create_publisher(
            Twist,
            'cmd_vel',
            10
        )

        self.pose_sub = self.create_subscription(
            Pose,
            'pose',
            self.pose_callback,
            10,
            callback_group=self.callback_group
        )

        self.action_server = ActionServer(
            self,
            Docking,
            self.action_name,
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
            callback_group=self.callback_group
        )

        self.get_logger().info(
            f'Action server ready: {self.action_name}'
        )

    def pose_callback(self, msg):
        self.pose = msg

    def goal_callback(self, goal_request):
        self.get_logger().info(
            f'Goal received: x={goal_request.x:.2f}, '
            f'y={goal_request.y:.2f}, psi={goal_request.psi:.2f}'
        )
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        self.get_logger().info('Cancel request received.')
        return CancelResponse.ACCEPT

    def stop_turtle(self):
        self.cmd_pub.publish(Twist())

    def send_feedback(self, goal_handle, goal_x, goal_y, stage):
        if self.pose is None:
            return

        now = time.time()

        # Limit feedback printing to about 5 Hz.
        if now - self.last_feedback_time < 0.2:
            return

        self.last_feedback_time = now

        feedback = Docking.Feedback()
        feedback.current_x = float(self.pose.x)
        feedback.current_y = float(self.pose.y)
        feedback.current_theta = float(self.pose.theta)
        feedback.distance_remaining = float(
            math.hypot(
                goal_x - self.pose.x,
                goal_y - self.pose.y
            )
        )
        feedback.stage = stage

        goal_handle.publish_feedback(feedback)

    def handle_cancel(self, goal_handle):
        if goal_handle.is_cancel_requested:
            self.stop_turtle()
            goal_handle.canceled()
            return True

        return False

    def rotate_to_angle(
        self,
        goal_handle,
        target_angle,
        goal_x,
        goal_y,
        stage
    ):
        while rclpy.ok():

            if self.handle_cancel(goal_handle):
                return False

            if self.pose is None:
                time.sleep(0.01)
                continue

            angle_error = normalize_angle(
                target_angle - self.pose.theta
            )

            if abs(angle_error) <= self.angle_tolerance:
                self.stop_turtle()
                return True

            cmd = Twist()

            # Fixed angular-speed magnitude.
            if angle_error > 0.0:
                cmd.angular.z = self.angular_velocity
            else:
                cmd.angular.z = -self.angular_velocity

            self.cmd_pub.publish(cmd)

            self.send_feedback(
                goal_handle,
                goal_x,
                goal_y,
                stage
            )

            time.sleep(0.01)

        return False

    def move_straight_to_goal(
        self,
        goal_handle,
        goal_x,
        goal_y
    ):
        start_x = self.pose.x
        start_y = self.pose.y

        planned_distance = math.hypot(
            goal_x - start_x,
            goal_y - start_y
        )

        self.get_logger().info(
            f'Straight section distance = {planned_distance:.3f} m'
        )

        while rclpy.ok():

            if self.handle_cancel(goal_handle):
                return False

            if self.pose is None:
                time.sleep(0.01)
                continue

            distance_to_goal = math.hypot(
                goal_x - self.pose.x,
                goal_y - self.pose.y
            )

            travelled_distance = math.hypot(
                self.pose.x - start_x,
                self.pose.y - start_y
            )

            if should_stop_straight(
                distance_to_goal,
                travelled_distance,
                planned_distance,
                self.position_tolerance
            ):
                self.stop_turtle()

                self.get_logger().info(
                    f'Straight motion stopped: '
                    f'd_goal={distance_to_goal:.3f} m, '
                    f'travelled={travelled_distance:.3f} m'
                )

                return True

            cmd = Twist()

            # Fixed linear velocity only.
            # No closed-loop steering is used here.
            cmd.linear.x = self.linear_velocity

            self.cmd_pub.publish(cmd)

            self.send_feedback(
                goal_handle,
                goal_x,
                goal_y,
                'MOVING_TO_DOCK'
            )

            time.sleep(0.01)

        return False

    def execute_callback(self, goal_handle):
        goal = goal_handle.request
        result = Docking.Result()

        while rclpy.ok() and self.pose is None:
            if self.handle_cancel(goal_handle):
                result.success = False
                result.message = (
                    'Docking cancelled before pose was received.'
                )
                return result

            time.sleep(0.01)

        # STEP 1 - calculate desired heading once.
        desired_heading = math.atan2(
            goal.y - self.pose.y,
            goal.x - self.pose.x
        )

        self.get_logger().info(
            f'Desired heading = {desired_heading:.3f} rad'
        )

        # STEP 2 - rotate to desired heading.
        if not self.rotate_to_angle(
            goal_handle,
            desired_heading,
            goal.x,
            goal.y,
            'ALIGNING_TO_GOAL'
        ):
            result.success = False
            result.message = (
                'Docking cancelled during initial alignment.'
            )
            return result

        # STEP 3 - move straight with fixed linear velocity.
        if not self.move_straight_to_goal(
            goal_handle,
            goal.x,
            goal.y
        ):
            result.success = False
            result.message = (
                'Docking cancelled while moving to the station.'
            )
            return result

        # STEP 4 - final docking orientation.
        if not self.rotate_to_angle(
            goal_handle,
            goal.psi,
            goal.x,
            goal.y,
            'FINAL_ORIENTATION'
        ):
            result.success = False
            result.message = (
                'Docking cancelled during final orientation.'
            )
            return result

        self.stop_turtle()

        goal_handle.succeed()

        result.success = True
        result.message = 'Docking completed successfully.'

        self.get_logger().info(result.message)

        return result


def main(args=None):
    rclpy.init(args=args)

    node = DockingActionServer()

    executor = MultiThreadedExecutor(num_threads=2)
    executor.add_node(node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.stop_turtle()
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
