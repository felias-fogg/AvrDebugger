# Fallback kit for debug-enabled cores

A core that takes its debug tools from AvrDebugger points to them with
`{runtime.tools.avr-debugger.path}`. When AvrDebugger is not installed, that
variable is not set, and the core's `platform.txt` supplies a folder of its own:

```
runtime.tools.avr-debugger.path={runtime.platform.path}/INSTALL-the-AvrDebugger-package
```

This kit fills that folder with stubs. When the user clicks Debug, the IDE
then brings its gdb-server terminal to the front, and there the user reads
what to install (`message.txt`). Without the stubs, the IDE only shows a
popup saying that `…/INSTALL-the-AvrDebugger-package/bin/avr-gdb` could not
be started.

## Using it in a core

Each AvrDebugger release carries the kit as `AvrDebugger-fallback-<version>.tar.gz`.
Unpack it in the root folder of the core and commit the result:

```
tar -xzf AvrDebugger-fallback-<version>.tar.gz
git add INSTALL-the-AvrDebugger-package
```

The folder then holds `bin/avr-gdb` and `bin/pyavrocd` (shell scripts for
macOS and Linux, committed executable) and `bin/avr-gdb.exe` and
`bin/pyavrocd.exe` (Windows, x86_64). On Windows, the IDE starts
`bin/avr-gdb` and finds `bin/avr-gdb.exe`. The core's `.gitattributes`
should keep the two scripts at LF:

```
INSTALL-the-AvrDebugger-package/bin/avr-gdb  text eol=lf
INSTALL-the-AvrDebugger-package/bin/pyavrocd text eol=lf
```

## How the stubs work

cortex-debug starts GDB first and asks for its version. If that fails, it
gives up without a word, and the server is never started. So the stub GDB
answers the version check, and every command after it with success. Then
cortex-debug starts the stub server, which prints the message and exits.
cortex-debug ends the session in order and shows the popup "GDB Server Quit
Unexpectedly. See gdb-server output for more details", with the gdb-server
terminal in front. (A stub GDB that fails the commands after the version
check crashed cortex-debug's debug adapter instead.)

`stub.c` is the Windows version of both scripts. It tells its role by the
argument `--interpreter=mi2`, which only GDB gets. `check.sh` checks a
`bin` folder of stubs, and the release workflow runs it on Linux, macOS and
Windows.
