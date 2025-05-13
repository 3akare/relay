
# relay
**relay** is a build automation and package manager for C/C++ projects, leveraging Python for the CLI, CMake for the build system, and vcpkg for dependency management.

## Installation
To install Relay globally on your system, you will need **Python 3**, **CMake**, and **vcpkg** installed.

### 1. Clone the Relay repository

```bash
git clone https://github.com/3akare/relay.git
cd relay
```

### 2. Ensure Prerequisites

Make sure you have the following installed and accessible in your `PATH`:

* Python 3
* CMake
* vcpkg (and set the `VCPKG_ROOT` environment variable to your vcpkg installation directory, preferably the Git clone)
* PyInstaller
```bash
pip install pyinstaller
```

### 3. Run the Installation Script

Execute the build and install script from the project root. This script uses PyInstaller to create a self-contained executable and installs it to `/usr/local/bin`.

```bash
chmod +x scripts/build_and_install.sh
sudo scripts/build_and_install.sh
```

### 4. Verify Installation

Open a new terminal window and run:

```bash
relay --version
```
If the version number is displayed, Relay is installed correctly.

## Usage
relay provides several commands to manage your C/C++ projects.
```bash
usage: relay [-h] [--version] [--toolchain TOOLCHAIN] [-v] {new,build,b,run,r} ...

C/C++ package manager

positional arguments:
  {new,build,b,run,r}   Available commands
    new                 Create a new relay package
    build (b)           Compile the current package
    run (r)             Run a binary or example of the local package (make then run)

options:
  -h, --help            Show this help message and exit
  --version, -V         Print version info and exit
  --toolchain TOOLCHAIN
                        Specify the build toolchain triplet (e.g., x64-windows, x64-linux).
                        Defaults to VCPKG_DEFAULT_TRIPLET environment variable or guesses based on OS.
  -v, --verbose         Use verbose output
```

### Example Commands

**Create a new project:**

```bash
relay new embedded_c

cd embedded_c
```
**Build the project (with a specific toolchain):**

```bash
relay build # relay will try to guess the toolchain based in your system and machine
``` 
or
```bash
relay --toolchain x64-osx build
```
**Run the project executable:**

```bash
relay run # relay will try to guess the toolchain based in your system and machine
```
or
```bash
relay --toolchain x64-osx run
```

## Uninstallation

To uninstall Relay, you need to remove the installed files from your system. This typically involves removing the directory from `/opt` and the symbolic link from `/usr/local/bin`.

### Recommended: Use Uninstallation Script

If you have a script at `scripts/uninstall.sh`:

```bash
chmod +x scripts/uninstall.sh
sudo scripts/uninstall.sh
```
### Manual Uninstallation
```bash
sudo rm -rf /opt/relay      # Removes the installed application directory
sudo rm /usr/local/bin/relay  # Removes the symbolic link
```