/*
 * Windows counterpart of the two shell stubs in this folder, copied twice as
 * avr-gdb.exe and pyavrocd.exe. It tells its role by the arguments: cortex-debug
 * starts GDB with --interpreter=mi2, the server never gets that option.
 *
 *  - as GDB: answer -gdb-version, and every other command with ^done (see avr-gdb)
 *  - as server: print message.txt, exit 1 (see pyavrocd)
 *
 * MESSAGE has to stay identical to message.txt; the workflow checks that.
 * Builds with any C compiler; the workflow uses x86_64-w64-mingw32-gcc.
 */
#include <stdio.h>
#include <string.h>
#include <ctype.h>

static const char MESSAGE[] =
    "\n"
    "                    *** The AvrDebugger package is not installed. ***\n"
    "Add the following URL to Additional Boards Manager URLs (File > Preferences):\n"
    "https://felias-fogg.github.io/AvrDebugger/package_felias-fogg_AvrDebugger_index.json\n"
    "and install AvrDebugger with the Boards Manager. Consult https://pyavrocd.io\n"
    "for information concerning debugging Arduino sketches on AVR hardware.\n"
    "\n";

static int as_gdb(void)
{
    char line[4096];

    printf("(gdb) \n");
    fflush(stdout);
    while (fgets(line, sizeof line, stdin) != NULL) {
        size_t n = 0;

        while (isdigit((unsigned char)line[n]))
            n++;
        if (strncmp(line + n, "-gdb-version", 12) == 0)
            printf("~\"GNU gdb (AvrDebugger missing) 15.2\\n\"\n%.*s^done\n(gdb) \n",
                   (int)n, line);
        else
            printf("%.*s^done\n(gdb) \n", (int)n, line);
        fflush(stdout);
    }
    return 0;
}

static int as_server(void)
{
    fputs(MESSAGE, stdout);
    fflush(stdout);
    return 1;
}

int main(int argc, char **argv)
{
    for (int i = 1; i < argc; i++)
        if (strncmp(argv[i], "--interpreter=mi", 16) == 0)
            return as_gdb();
    return as_server();
}
