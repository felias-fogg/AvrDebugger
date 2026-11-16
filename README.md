# AvrDebugger

Install AvrDebugger if you want to use a debugger with some of the more recent versions of, e.g., XMiniCore, TinyCore (see the [list of debug-enabled board packages](https://pyavrocd.io/latest/supporting-packages/)). If the Arduino IDE says in its gdb-server terminal that the AvrDebugger package is not installed, or reports that it could not start the debugger located at `…/INSTALL-the-AvrDebugger-package/bin/avr-gdb`, this package is what is missing.

In addition, AvrDebugger lets you debug the classic Arduino AVR boards -- Uno, Nano, Pro Mini, Mega, and Leonardo -- in the Arduino IDE 2: set breakpoints, step through the sketch, and look at variables and registers. 

The boards are the ones of *Arduino AVR Boards*. AvrDebugger uses their core and variants unchanged, so a sketch behaves exactly as it does there. What it adds:

- the debug tools: the GDB server [PyAvrOCD](https://pyavrocd.io), the debugger `avr-gdb`, and the simulator `simavr`;
- the debug configuration the IDE needs, and `Optimize for Debugging`;
- a current avrdude, and programmer entries for the debug probes;
- the `#pragma arduino` directives for setting build flags from the sketch.

## Supported boards

| Board in the menu                    | MCU                    | Debug interface |
| ------------------------------------ | ---------------------- | --------------- |
| Arduino UNO (debug)                  | ATmega328P             | debugWIRE       |
| Arduino Nano (debug)                 | ATmega328P, ATmega168  | debugWIRE       |
| Arduino Pro or Pro Mini (debug)      | ATmega328P, ATmega168  | debugWIRE       |
| Arduino Mega or Mega 2560 (debug)    | ATmega2560, ATmega1280 | JTAG            |
| Arduino Leonardo (debug)             | ATmega32U4             | JTAG            |

The `(debug)` marker tells them apart from the boards of Arduino AVR Boards: when you plug in a board, the IDE offers both. If you want to use other boards from the original list of Arduino AVR boards, simply add the file boards.local.txt with a line containing, for, e.g., the `micro` MCU:

```
micro.hide=false
```

Note that the boards.local.txt file will be overwritten when a new version of AvrDebugger gets installed.

## Installation

AvrDebugger needs *Arduino AVR Boards*. The IDE offers to install it when you first connect an Uno; otherwise, install it with the Boards Manager.

Install *AvrDebugger* as follows:

- Open `File -> Preferences` and enter the following URL in `Additional Boards Manager URLs`:

  ```
  https://felias-fogg.github.io/AvrDebugger/package_felias-fogg_AvrDebugger_index.json
  ```

- Open the Boards Manager (`Tools -> Board -> Boards Manager...`), search for `AvrDebugger`, and click `Install`.

With arduino-cli:

```
arduino-cli core install AvrDebugger:avr --additional-urls https://felias-fogg.github.io/AvrDebugger/package_felias-fogg_AvrDebugger_index.json
```

## Getting started

1. **Prepare the board.** debugWIRE boards need a hardware change on the RESET line; on an Uno, this means cutting the `RESET EN` solder bridge. JTAG boards need the JTAG pins enabled by a fuse: select `JTAG enabled` in `Tools -> JTAG pins` and use `Tools -> Burn Bootloader` with an ISP programmer. The [board preparation](https://pyavrocd.io/latest/board-preparation/) page has the details for each board.
2. **Connect a debug probe** -- see the [list of supported probes](https://pyavrocd.io/latest/supported-debuggers/). If you have none, a second Uno running [dw-link](https://github.com/felias-fogg/dw-link) will do for the debugWIRE boards.
3. **Select the board** under `Tools -> Board -> AvrDebugger`.
4. **Select `Sketch -> Optimize for Debugging`.** The code gets a bit bigger, but the optimizer will not disturb the structure of the program.
5. **Click the** **`Verify`** **button.** This will compile the program. This is always necessary after a change to the source code, since otherwise the debugger will load the old binary. 
6. **Click the `Debug` button.** Debugging is started, and on debugWIRE MCUs, you may be asked to power-cycle (remove and replug power or USB) the MCU. The sketch is uploaded, and execution stops at the beginning of `main`.

How to use the debugger is explained in the [PyAvrOCD manual](https://pyavrocd.io/latest/debugging/).

On debugWIRE boards, the RESET line cannot be used while debugging, and neither can ISP programming. To return to normal operation, type `monitor debugwire disable` into the `Debug Console` before you end the debug session.

### Without hardware

Select `Tools -> Programmer -> Simulator (simavr)`, and the `Debug` button starts the sketch in a simulated MCU instead.

## Programmers

AvrDebugger adds the following programmers to those of Arduino AVR Boards:

- `dw-link (ISP mode)` -- an Arduino UNO turned into a debug probe using the [dw-link sketch](https://felias-fogg.github.io/dw-link/latest/),
- ISP and JTAG modes of `Atmel-ICE`, `Power Debugger`, `PICkit 4`, `MPLAB SNAP`, `PICkit 5`, `PICkit Basic`, `JTAGICE mkII`, and `AVR Dragon`,
- `Simulator (simavr)`, which does not program anything but makes the `Debug` button start the simulator.

JTAG modes only work for the Mega and the Leonardo.

## Pragma directives

As in [TinyCore](https://github.com/MCUdude/TinyCore), build flags can be given in the sketch:

```c
#pragma arduino release_flags ...
#pragma arduino debug_flags ...
#pragma arduino cpp_flags ...
```

`release_flags` apply when `Optimize for Debugging` is off, `debug_flags` when it is on, and `cpp_flags` to every C++ file. For instance, `#pragma arduino cpp_flags -std=gnu++17` selects the C++ language version. See [pragma.md](https://github.com/MCUdude/TinyCore/blob/main/pragma.md) of TinyCore for more.

## License

The board definitions come from [Arduino AVR Boards](https://github.com/arduino/ArduinoCore-avr) and are, like the rest of this package, licensed under the GNU Lesser General Public License 2.1; see [LICENSE](LICENSE). The debug tools are licensed separately: PyAvrOCD under MIT, avr-gdb and simavr under the GPL.
