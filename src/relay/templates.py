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

# Add include directories for your own headers
include_directories(include)

# Recursively get all .c files from src/
file(GLOB_RECURSE SOURCE_FILES CONFIGURE_DEPENDS src/*.c)

# Define your executable target
add_executable({project_name} ${{SOURCE_FILES}})

# Find the ncurses library
# find_package(NCURSES_LIB ncurses)

# Link libraries from find_package calls
# target_link_libraries({project_name} PRIVATE ${{NCURSES_LIB}}) # Link your executable to the ZLIB library

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

#.clang format content
CLANG_FORMAT_TEMPLATE = """\
BasedOnStyle: Google
UseTab: Never
IndentWidth: 4
TabWidth: 2
"""

# .gitignore content
GITIGNORE = """\
build/
vcpkg_installed/
"""