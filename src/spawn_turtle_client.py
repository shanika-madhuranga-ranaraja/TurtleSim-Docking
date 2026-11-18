#!/usr/bin/env python3

import time

import rclpy
from rclpy.node import Node
from turtlesim.srv import Spawn, Kill


class SpawnTurtleClient(Node):

    def __init__(self):
        super().__init__('spawn_turtle_client')

        self.declare_parameter('initial_pose_turtle1', [5.0, 1.0, 0.0])
        self.declare_parameter('initial_pose_turtle2', [10.0, 1.0, 0.0])
        self.declare_parameter('initial_pose_turtle3', [1.0, 1.0, 0.0])

        self.spawn_client = self.create_client(Spawn, '/spawn_turtle')

        self.kill_client = self.create_client(Kill, '/kill')

    def wait_for_services(self):
        while not self.kill_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for TurtleSim /kill service...')

        while not self.spawn_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for project /spawn_turtle service...')

    def call_and_wait(self, client, request):
        future = client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        return future.result()

    def kill_default_turtle1(self):
        request = Kill.Request()
        request.name = 'turtle1'

        self.get_logger().info('Removing TurtleSim default turtle1...')
        self.call_and_wait(self.kill_client, request)
        time.sleep(0.2)

    def spawn_one_turtle(self, name, pose):
        request = Spawn.Request()
        request.x = float(pose[0])
        request.y = float(pose[1])
        request.theta = float(pose[2])
        request.name = name

        response = self.call_and_wait(self.spawn_client, request)

        if response is not None and response.name == name:
            self.get_logger().info(
                f'/spawn_turtle completed for {name}.'
            )
        else:
            self.get_logger().error(
                f'/spawn_turtle failed for {name}.'
            )

    def run(self):
        self.wait_for_services()
        self.kill_default_turtle1()

        turtle1_pose = self.get_parameter('initial_pose_turtle1').value
        turtle2_pose = self.get_parameter('initial_pose_turtle2').value
        turtle3_pose = self.get_parameter('initial_pose_turtle3').value

        self.spawn_one_turtle('turtle1', turtle1_pose)
        self.spawn_one_turtle('turtle2', turtle2_pose)
        self.spawn_one_turtle('turtle3', turtle3_pose)

        self.get_logger().info(
            'All three turtles were requested through /spawn_turtle.'
        )


def main(args=None):
    rclpy.init(args=args)
    node = SpawnTurtleClient()

    try:
        node.run()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
