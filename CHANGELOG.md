# Changelog

## 0.2.0

- A second platform in the package: *megaAvrDebugger* (`AvrDebugger:megaavr`) for the
  Nano Every and the Uno WiFi Rev2, with core and variants from Arduino megaAVR Boards,
  avrdude 8.3 instead of its 6.3, the UPDI programmers, and the same debug tools.
- The repository has a folder per platform, `avr/` and `megaavr/`; each release
  attaches two archives, `AvrDebugger-<version>.tar.bz2` and
  `megaAvrDebugger-<version>.tar.bz2`.

## 0.1.1
- The fallback kit unpacks into debugger/fallback, and its message points to https://pyavrocd.io.

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
