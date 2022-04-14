cmake_minimum_required(VERSION 2.8.3)
project(rnnoise)

find_package(catkin REQUIRED)

catkin_python_setup()

catkin_package()

set(MD5SUM_DIR ${PROJECT_SOURCE_DIR}/md5sum)
# set(INSTALL_DIR ${CATKIN_DEVEL_PREFIX}/${CATKIN_PACKAGE_SHARE_DESTINATION})
set(INSTALL_DIR ${PROJECT_SOURCE_DIR})

add_custom_command(
  OUTPUT rnnoise_installed
  COMMAND make -f ${PROJECT_SOURCE_DIR}/Makefile
  MD5SUM_DIR=${MD5SUM_DIR}
  INSTALL_DIR=${INSTALL_DIR}
)
add_custom_target(all_installed ALL DEPENDS rnnoise_installed)

install(DIRECTORY
  ${INSTALL_DIR}/include
  ${INSTALL_DIR}/lib
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
  USE_SOURCE_PERMISSIONS)
