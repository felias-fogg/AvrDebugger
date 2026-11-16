#!/bin/bash
# Checks a pair of stubs against what cortex-debug needs from them:
#
#     bash fallback/check.sh <bin folder>
#
# The folder holds avr-gdb and pyavrocd, as shell scripts or as .exe files.
# Run from the repository root; message.txt is the reference text.
set -u
BIN="$1"
MSG="$(dirname "$0")/message.txt"
WORK=$(mktemp -d)
fail=0

# As the GDB: the version check has to pass, everything after it has to fail.
printf '1-gdb-version\n2-gdb-set target-async on\n3-interpreter-exec console "set print demangle on"\n' \
    | "$BIN/avr-gdb" -q --interpreter=mi2 x.elf | tr -d '\r' > "$WORK/gdb.out"
for want in '^~"GNU gdb .* [0-9]+\.[0-9]+' '^1\^done$' '^2\^error,msg=' '^3\^error,msg='; do
    grep -Eq "$want" "$WORK/gdb.out" || { echo "avr-gdb: no line matching $want"; fail=1; }
done

# As the server: the text has to be message.txt, and it has to come at once,
# while the stub is still waiting.
"$BIN/pyavrocd" -c "gdb_port 50000" -s nop --device atmega328p > "$WORK/server.out" 2>&1 &
PID=$!
sleep 3
tr -d '\r' < "$WORK/server.out" > "$WORK/server.txt"
# A Windows checkout may have turned message.txt into CRLF.
tr -d '\r' < "$MSG" > "$WORK/message.txt"
if cmp -s "$WORK/server.txt" "$WORK/message.txt"; then
    echo "pyavrocd: prints message.txt"
else
    echo "pyavrocd: output differs from message.txt"; diff "$WORK/server.txt" "$WORK/message.txt"; fail=1
fi
kill "$PID" 2>/dev/null
wait "$PID" 2>/dev/null

[ "$fail" = 0 ] && echo "avr-gdb: version check passes, later commands fail"
rm -rf "$WORK"
exit "$fail"
