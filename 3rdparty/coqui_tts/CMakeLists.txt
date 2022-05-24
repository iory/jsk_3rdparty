cmake_minimum_required(VERSION 2.8.3)
project(coqui_tts)

find_package(catkin REQUIRED COMPONENTS
  catkin_virtualenv)

if (${catkin_virtualenv_VERSION} VERSION_LESS "0.3.0")
  message(STATUS "${PROJECT_NAME} requires catkin_virtualenv >= 0.3.0")
  return()
endif()

catkin_package()

catkin_generate_virtualenv(
  INPUT_REQUIREMENTS requirements.in
  PYTHON_INTERPRETER python3
  USE_SYSTEM_PACKAGES FALSE
  ISOLATE_REQUIREMENTS FALSE
  CHECK_VENV FALSE
)

catkin_install_python(PROGRAMS bin/synthesize.py node_scripts/coqui_tts_server.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})

install(PROGRAMS bin/text2wave bin/models.json
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})

install(DIRECTORY launch
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
  USE_SOURCE_PERMISSIONS)

install(FILES requirements.in requirements.txt
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})
