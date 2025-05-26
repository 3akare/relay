# relay

**Relay** is a build automation and package manager for C/C++ projects, leveraging Python for the CLI, CMake for the build system, and vcpkg for dependency management.

-----

## Installation

Relay offers two main installation methods: downloading pre-built binaries (recommended for most users) or building from source.

### Option 1: Install with Pre-built Binaries (Recommended)
Download the appropriate pre-built executable for your operating system:
* **For macOS (x64):**
    ```bash
    curl -LJO https://github.com/3akare/relay/releases/latest/download/relay-macos-x64.zip && \
    unzip -o relay-macos-x64.zip && \
    sudo mkdir -p /opt && \
    sudo mv relay /opt/relay && \
    sudo ln -sf /opt/relay/relay /usr/local/bin/relay && \
    rm relay-macos-x64.zip && \
    echo "Relay installed! Try: relay --version"
    ```
* **For Linux (x64):**
    ```bash
    curl -LJO https://github.com/3akare/relay/releases/latest/download/relay-linux-x64.zip && \
    unzip relay-linux-x64.zip && \
    sudo mkdir -p /opt && \
    sudo mv relay /opt/relay && \
    sudo ln -sf /opt/relay/relay /usr/local/bin/relay && \
    rm relay-linux-x64.zip && \
    echo "Relay installed! Try: relay --version"
    ```
---

### Option 2: Install from Source

To install Relay globally on your system from source, you will need **Python 3**, **CMake**, and **vcpkg** installed.

1.  **Clone the Relay repository:**

    ```bash
    git clone https://github.com/3akare/relay.git
    cd relay
    ```

2.  **Ensure Prerequisites:**
    Make sure you have the following installed and accessible in your `PATH`:

      * Python 3
      * CMake
      * vcpkg (and set the `VCPKG_ROOT` environment variable to your vcpkg installation directory, preferably the Git clone)
      * PyInstaller
        ```bash
        pip install pyinstaller
        ```

3.  **Run the Installation Script:**
    Execute the build and install script from the project root. This script uses PyInstaller to create a self-contained executable folder and installs it to `/opt/relay`, then creates a symbolic link in `/usr/local/bin`.

    ```bash
    chmod +x scripts/build_and_install.sh
    sudo scripts/build_and_install.sh
    ```

4.  **Verify Installation:**
    Open a new terminal window and run:

    ```bash
    relay --version
    ```

    If the version number is displayed, Relay is installed correctly.

-----

## Usage

Relay provides several commands to manage your C/C++ projects.

```bash
C/C++ package manager

positional arguments:
  {new,build,b,run,r,install,i,add,remove,rm,update,clean}
                        Available commands
    new                 Create a new relay package
    build (b)           Compile the current package
    run (r)             Run a binary or example of the local package (make then run)
    install (i)         Install dependencies listed in Relay.toml via vcpkg
    add                 Name of the dependency to add (e.g., 'fmt', 'zlib')
    remove (rm)         Remove a dependency from the project
    update              Update project dependencies
    clean               Remove build artifacts and cached files

options:
  -h, --help            show this help message and exit
  --version, -V         Print version info and exit
  --toolchain TOOLCHAIN
                        Specify the build toolchain triplet (e.g., x64-windows, x64-linux). Defaults to VCPKG_DEFAULT_TRIPLET environment variable or guesses based on OS.
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

-----

## Uninstallation

To uninstall Relay, you need to remove the installed files from your system.

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