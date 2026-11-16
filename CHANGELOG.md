# Changelog

## 0.1.0

- First version: the debug tools (PyAvrOCD, avr-gdb, simavr) as the tool
  `avr-debugger`, avrdude 8.3, and the Uno, Nano, Pro Mini, Mega and Leonardo
  with core and variants from Arduino AVR Boards.
- "Optimize for debugging", `#pragma arduino debug_flags|release_flags|cpp_flags`.
- Programmers: dw-link and the debug probes PyAvrOCD supports, ISP and JTAG.
- The fallback kit for the other cores (`fallback/`, attached to each release
  as `AvrDebugger-fallback-<version>.tar.gz`): stubs for avr-gdb and pyavrocd
  that a core puts in `INSTALL-the-AvrDebugger-package/bin`. When AvrDebugger
  is missing, the IDE then shows in its gdb-server terminal what to install,
  instead of a popup saying that avr-gdb could not be started.
