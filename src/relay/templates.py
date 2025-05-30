MAIN_C_TEMPLATE = """\
#include "{project_name}.h"

int main() {{
    printf(MSG);
    return 0;
}}
"""

MAIN_H_TEMPLATE = """\
#ifndef _{include_guard}_
#define _{include_guard}_

#include <stdio.h>
#define MSG "Hello, World!\\n"

#endif
"""

CMAKELISTS_TEMPLATE = """\
cmake_minimum_required(VERSION 3.15)
project({project_name} VERSION 0.1.0 LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

include_directories(include)

file(GLOB_RECURSE SOURCE_FILES CONFIGURE_DEPENDS src/*.c)

add_executable({project_name} ${{SOURCE_FILES}})

install(TARGETS {project_name} DESTINATION bin)

# DO NOT REMOVE THIS
# <RELAY_DEPENDENCIES_LINK_START>
# <RELAY_DEPENDENCIES_LINK_END> 

# DO NOT REMOVE THIS
# <RELAY_DEPENDENCIES_FIND_START>
# <RELAY_DEPENDENCIES_FIND_END>
"""

RELAY_TOML_TEMPLATE = """\
[project]
name = "{project_name}"
version = "0.1.0"

[dependencies]
"""

CLANG_FORMAT_TEMPLATE = """\
BasedOnStyle: Google
UseTab: Never
IndentWidth: 4
TabWidth: 2
"""

GITIGNORE = """\
build/
vcpkg_installed/
"""