#!/usr/bin/env python3

import os

from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    params_file = os.path.join(
        get_package_share_directory('project1'),
        'config',
        'params.yaml'
    )

    turtlesim_node = Node(
        package='turtlesim',
        executable='turtlesim_node',
        name='turtlesim'
    )

    spawn_service_node = Node(
        package='project1',
        executable='spawn_turtle_service',
        name='spawn_turtle_service'
    )

    spawn_client_node = Node(
        package='project1',
        executable='spawn_turtle_client',
        name='spawn_turtle_client',
        parameters=[params_file]
    )

    server_turtle1 = Node(
        package='project1',
        executable='docking_action_server',
        name='docking_server_turtle1',
        parameters=[params_file],
        remappings=[
            ('cmd_vel', '/turtle1/cmd_vel'),
            ('pose', '/turtle1/pose')
        ]
    )

    server_turtle2 = Node(
        package='project1',
        executable='docking_action_server',
        name='docking_server_turtle2',
        parameters=[params_file],
        remappings=[
            ('cmd_vel', '/turtle2/cmd_vel'),
            ('pose', '/turtle2/pose')
        ]
    )

    server_turtle3 = Node(
        package='project1',
        executable='docking_action_server',
        name='docking_server_turtle3',
        parameters=[params_file],
        remappings=[
            ('cmd_vel', '/turtle3/cmd_vel'),
            ('pose', '/turtle3/pose')
        ]
    )

    client_turtle1 = Node(
        package='project1',
        executable='docking_action_client',
        name='docking_client_turtle1',
        parameters=[params_file],
        remappings=[
            ('pose', '/turtle1/pose')
        ]
    )

    client_turtle2 = Node(
        package='project1',
        executable='docking_action_client',
        name='docking_client_turtle2',
        parameters=[params_file],
        remappings=[
            ('pose', '/turtle2/pose')
        ]
    )

    client_turtle3 = Node(
        package='project1',
        executable='docking_action_client',
        name='docking_client_turtle3',
        parameters=[params_file],
        remappings=[
            ('pose', '/turtle3/pose')
        ]
    )

    return LaunchDescription([
        turtlesim_node,
        spawn_service_node,
        spawn_client_node,
        server_turtle1,
        server_turtle2,
        server_turtle3,
        client_turtle1,
        client_turtle2,
        client_turtle3
    ])
