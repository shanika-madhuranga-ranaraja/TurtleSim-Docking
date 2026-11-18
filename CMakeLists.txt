cmake_minimum_required(VERSION 3.8)
project(project1)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(rclpy REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(turtlesim REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "action/Docking.action"
)

ament_export_dependencies(rosidl_default_runtime)

install(PROGRAMS
  src/spawn_turtle_service.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME spawn_turtle_service
)

install(PROGRAMS
  src/spawn_turtle_client.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME spawn_turtle_client
)

install(PROGRAMS
  src/docking_action_server.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME docking_action_server
)

install(PROGRAMS
  src/docking_action_client.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME docking_action_client
)

install(DIRECTORY
  launch
  config
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
