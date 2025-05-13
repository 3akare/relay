# basic main.c content
MAIN_C_TEMPLATE = """\
#include "{project_name}.h"

int main() {{
    printf(MSG);
    return 0;
}}
"""

# basic [project_name].h content
MAIN_H_TEMPLATE = """\
#ifndef _{include_guard}_
#define _{include_guard}_

#include <stdio.h>
#define MSG "Hello, World!\\n"

#endif
"""
# basic CMakeLists.txt content
CMAKELISTS_TEMPLATE = """\
cmake_minimum_required(VERSION 3.15)
project({project_name} VERSION 0.1.0 LANGUAGES C)

# Set C standards (adjust as needed)
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
# set(CMAKE_C_EXTENSIONS OFF) # Prefer standard C

# Add include directories for your own headers
include_directories(include)

# Use vcpkg's integration for finding packages
# This requires CMAKE_TOOLCHAIN_FILE to be set when configuring CMake
# find_package(<package_name> CONFIG REQUIRED) # Add your dependency find_package calls here
# find_package(ZLIB REQUIRED) # Find the ZLIB library

# Define your executable target - using main.c
add_executable({project_name} src/main.c)

# Link libraries from find_package calls
# target_link_libraries({project_name} PRIVATE ZLIB::ZLIB) # Link your executable to the ZLIB library

# Optional: Install the executable
install(TARGETS {project_name} DESTINATION bin)

# Optional: Add subdirectories for examples or tests
# add_subdirectory(examples)
# add_subdirectory(tests)
"""

# basic Relay.toml content

RELAY_TOML_TEMPLATE = """\
[package]
name = "{project_name}"
version = "0.1.0"

[dependencies]
"""