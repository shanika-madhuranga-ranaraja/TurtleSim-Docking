#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from turtlesim.srv import Spawn


class SpawnTurtleService(Node):
    """Project service that forwards spawn requests to TurtleSim's /spawn service."""

    def __init__(self):
        super().__init__('spawn_turtle_service')

        self.server = self.create_service(
            Spawn,
            '/spawn_turtle',
            self.spawn_callback
        )

        self.get_logger().info(
            'Spawn turtle service is ready on /spawn_turtle.'
        )

    def spawn_callback(self, request, response):
        """Receive a project /spawn_turtle request and call TurtleSim /spawn."""

        # A small helper node is used so the service callback can wait for the
        # built-in TurtleSim /spawn response without blocking this service's
        # own ROS executor.
        helper_node = Node('turtlesim_spawn_forwarder')
        spawn_client = helper_node.create_client(Spawn, '/spawn')

        while not spawn_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for TurtleSim /spawn service...')

        turtlesim_request = Spawn.Request()
        turtlesim_request.x = request.x
        turtlesim_request.y = request.y
        turtlesim_request.theta = request.theta
        turtlesim_request.name = request.name

        future = spawn_client.call_async(turtlesim_request)
        rclpy.spin_until_future_complete(helper_node, future)

        try:
            turtlesim_response = future.result()
            response.name = turtlesim_response.name

            self.get_logger().info(
                f'Spawned {response.name}: '
                f'x={request.x:.2f}, y={request.y:.2f}, '
                f'theta={request.theta:.2f}'
            )
        except Exception as error:
            response.name = ''
            self.get_logger().error(
                f'Failed to spawn {request.name}: {error}'
            )

        helper_node.destroy_node()
        return response


def main(args=None):
    rclpy.init(args=args)
    node = SpawnTurtleService()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
