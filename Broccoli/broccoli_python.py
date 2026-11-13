#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Broccoli's own Python, for the code runner of the packaged app.

The packaged app has no `python3` of its own to hand code to: its Python lives inside the app's
programs, and the app's main program started a second time is a second Broccoli, not an
interpreter. This file is packaged as one more program next to it (BroccoliPython, like the two
workers) and behaves like the `python3` command, so Settings › General › Code runners can point at
it and the code the models write runs on the Python and the libraries that are already in the app.

It understands what a runner command line uses:

    BroccoliPython [options] -c CODE [args...]
    BroccoliPython [options] -m MODULE [args...]
    BroccoliPython [options] SCRIPT [args...]
    BroccoliPython [options] [-]            (the program is read from standard input)

Options are read the way python3 reads them. -I / -E / -s / -S / -P are accepted and already
true (a packaged Python reads no PYTHON* variables and has no site folders); -u makes the output
unbuffered; -B, -O, -q, -b, -d, -v, -x, -i, -X … and -W … are accepted and ignored.

Charts (matplotlib), packaged only: the packaging tool gives matplotlib a new empty folder on
every start and deletes it at the end, so the list of this Mac's fonts was built again on every
run that draws — about 11 seconds on a Mac with many fonts, as long as the code runner waits at
all. Here the folder is a lasting one in Broccoli's caches, one per place the app sits in (the
list names fonts inside the app), and the first run on a Mac starts building the list on its own,
apart from the code it was asked to run, so that a run that is stopped for taking too long does not
stop the list from ever being finished.

Run from source (python3 broccoli_python.py …) it does the same on the running Python: the checks
use it that way.
"""
import os
import sys

PROGRAM_NAME = 'BroccoliPython'
BUNDLE_ID = 'com.ryanthehito.broccoli'      # = BROCCOLI_BUNDLE_ID in Broccoli.py (the caches folder's name)
_FONT_LIST_CODE = ('import os, sys\ntry:\n    import matplotlib.font_manager\nfinally:\n'
                   '    try:\n        os.unlink(sys.argv[1])\n    except OSError:\n        pass\n')
_FLAGS_WITHOUT_VALUE = set('IEsSPBOqbdvxiuR')
_FLAGS_WITH_VALUE = set('XW')

USAGE = (
    f'usage: {PROGRAM_NAME} [option] ... [-c cmd | -m mod | file | -] [arg] ...\n'
    'Broccoli\'s own Python (the one inside the app). Options are read like python3\'s:\n'
    '-c cmd : program passed in as a string\n'
    '-m mod : run a library module as a script\n'
    'file   : program read from a script file\n'
    '-      : program read from standard input\n'
    '-u     : unbuffered standard output and error\n'
    '-V     : print the Python version and exit\n'
    '-I -E -s -S -P -B -O -q -b -d -v -x -i -X opt -W arg : accepted\n'
)


class _CommandLine:
    def __init__(self):
        self.mode = 'stdin'      # 'command' | 'module' | 'script' | 'stdin' | 'version' | 'help'
        self.target = ''
        self.rest = []
        self.isolated = False    # -I or -P: the current folder is not put on the module path
        self.unbuffered = False
        self.error = ''


def parse_command_line(arguments):
    """python3's own reading of its arguments: options up to the first of -c / -m / a file / '-',
    everything after it belongs to the program."""
    parsed = _CommandLine()
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument == '--':
            index += 1
            if index < len(arguments):
                parsed.mode, parsed.target, parsed.rest = 'script', arguments[index], arguments[index + 1:]
            return parsed
        if argument == '-':
            parsed.mode, parsed.rest = 'stdin', arguments[index + 1:]
            return parsed
        if argument in ('--version', '-V', '-VV'):
            parsed.mode = 'version'
            return parsed
        if argument in ('--help', '-h', '-?'):
            parsed.mode = 'help'
            return parsed
        if not argument.startswith('-') or len(argument) < 2:
            parsed.mode, parsed.target, parsed.rest = 'script', argument, arguments[index + 1:]
            return parsed
        if argument.startswith('--'):
            parsed.error = f'unknown option {argument}'
            return parsed
        position = 1
        while position < len(argument):
            flag = argument[position]
            position += 1
            if flag in ('c', 'm'):
                value = argument[position:]
                if not value:
                    index += 1
                    if index >= len(arguments):
                        parsed.error = f'argument expected for the -{flag} option'
                        return parsed
                    value = arguments[index]
                parsed.mode = 'command' if flag == 'c' else 'module'
                parsed.target, parsed.rest = value, arguments[index + 1:]
                return parsed
            if flag in _FLAGS_WITH_VALUE:
                if position >= len(argument):
                    index += 1
                    if index >= len(arguments):
                        parsed.error = f'argument expected for the -{flag} option'
                        return parsed
                break
            if flag == 'V':
                parsed.mode = 'version'
                return parsed
            if flag in ('h', '?'):
                parsed.mode = 'help'
                return parsed
            if flag not in _FLAGS_WITHOUT_VALUE:
                parsed.error = f'unknown option -{flag}'
                return parsed
            if flag in ('I', 'P'):
                parsed.isolated = True
            elif flag == 'u':
                parsed.unbuffered = True
        index += 1
    return parsed


def _prepare_streams(unbuffered):
    """Text goes out as UTF-8 whatever the locale of the app that started us (an app opened from
    Finder has none), and what cannot be encoded is escaped instead of ending the program."""
    for name in ('stdout', 'stderr'):
        stream = getattr(sys, name, None)
        if stream is None or not hasattr(stream, 'reconfigure'):
            continue
        try:
            options = {'encoding': 'utf-8', 'errors': 'backslashreplace'}
            if unbuffered:
                options.update(line_buffering=True, write_through=True)
            stream.reconfigure(**options)
        except Exception:
            pass
    stream = getattr(sys, 'stdin', None)
    if stream is not None and hasattr(stream, 'reconfigure'):
        try:
            stream.reconfigure(encoding='utf-8', errors='surrogateescape')
        except Exception:
            pass


def _keep_matplotlib_folder(arguments):
    """Packaged: matplotlib's folder is a lasting one, and its font list gets built once (see the
    top of this file). Never in the way of the program: any failure here is passed over."""
    if not getattr(sys, 'frozen', False) or sys.platform != 'darwin':
        return
    try:
        import zlib

        place = getattr(sys, '_MEIPASS', '') or os.path.dirname(sys.executable)
        folder = os.path.join(os.path.expanduser('~'), 'Library', 'Caches', BUNDLE_ID, PROGRAM_NAME,
                              'matplotlib-%08x' % zlib.crc32(os.fsencode(place)))
        os.makedirs(folder, exist_ok=True)
        os.environ['MPLCONFIGDIR'] = folder
        if arguments[:3] == ['-I', '-c', _FONT_LIST_CODE]:
            return                                   # this run is the one building the list
        if any(name.startswith('fontlist-') for name in os.listdir(folder)):
            return
        marker = os.path.join(folder, 'building')
        try:
            import time

            if time.time() - os.path.getmtime(marker) < 600:
                return                               # another run is building it right now
            os.unlink(marker)
        except OSError:
            pass
        import importlib.util

        if importlib.util.find_spec('matplotlib') is None:
            return
        os.close(os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
        import subprocess

        # on its own (new session, no ties to our output): it outlives a run that is stopped
        subprocess.Popen([sys.executable, '-I', '-c', _FONT_LIST_CODE, marker],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True, close_fds=True)
    except Exception:
        pass


def _fresh_main_module():
    """A new __main__ for the program, as python3 gives it: what it defines is its own, and
    pickle / dataclasses / inspect find it under that name."""
    import types

    module = types.ModuleType('__main__')
    module.__dict__.update(__builtins__=__builtins__, __spec__=None, __loader__=None, __package__=None)
    sys.modules['__main__'] = module
    return module


def _run_source(source, filename, argv):
    import linecache

    # the traceback of a program given as text shows its lines (python3 3.13 does; 3.11 shows none)
    linecache.cache[filename] = (len(source), None, source.splitlines(True), filename)
    sys.argv = argv
    module = _fresh_main_module()
    exec(compile(source, filename, 'exec'), module.__dict__)


def _run(parsed):
    if parsed.mode == 'command':
        if not parsed.isolated:
            sys.path.insert(0, '')
        _run_source(parsed.target, '<string>', ['-c', *parsed.rest])
        return
    if parsed.mode == 'stdin':
        if not parsed.isolated:
            sys.path.insert(0, '')
        _run_source(sys.stdin.read(), '<stdin>', ['-' if parsed.rest else '', *parsed.rest])
        return
    import runpy

    if parsed.mode == 'module':
        if not parsed.isolated:
            sys.path.insert(0, os.getcwd())
        sys.argv = [parsed.target, *parsed.rest]
        runpy.run_module(parsed.target, run_name='__main__', alter_sys=True)
        return
    script = parsed.target
    if not os.path.exists(script):
        raise _CannotOpen(f"{PROGRAM_NAME}: can't open file {os.path.abspath(script)!r}: "
                          '[Errno 2] No such file or directory')
    if not parsed.isolated:
        sys.path.insert(0, os.path.dirname(os.path.abspath(script)))
    sys.argv = [script, *parsed.rest]
    runpy.run_path(script, run_name='__main__')


class _CannotOpen(Exception):
    pass


def _print_traceback():
    """The traceback python3 prints: the program's frames, without this file's own."""
    import traceback

    kind, error, trace = sys.exc_info()
    own = {main.__code__, _run.__code__, _run_source.__code__}
    while trace is not None and trace.tb_frame.f_code in own:
        trace = trace.tb_next
    while trace is not None and (trace.tb_frame.f_code.co_filename.startswith('<frozen runpy')
                                 or os.path.basename(trace.tb_frame.f_code.co_filename) == 'runpy.py'):
        trace = trace.tb_next
    traceback.print_exception(kind, error, trace)


def _flush():
    for name in ('stdout', 'stderr'):
        try:
            getattr(sys, name).flush()
        except Exception:
            pass


def main(arguments=None):
    arguments = list(sys.argv[1:] if arguments is None else arguments)
    if arguments[:1] == ['--multiprocessing-fork']:
        # a child of the program's own multiprocessing (started with this executable): let
        # multiprocessing run it
        import multiprocessing

        multiprocessing.freeze_support()
        return 0
    parsed = parse_command_line(arguments)
    _prepare_streams(parsed.unbuffered)
    _keep_matplotlib_folder(arguments)
    if parsed.error:
        sys.stderr.write(f'{PROGRAM_NAME}: {parsed.error}\n{USAGE}')
        return 2
    if parsed.mode == 'version':
        print('Python ' + sys.version.split()[0])
        return 0
    if parsed.mode == 'help':
        sys.stdout.write(USAGE)
        return 0
    try:
        _run(parsed)
    except SystemExit as leaving:
        code = leaving.code
        if code is None:
            return 0
        if isinstance(code, int):
            return code
        sys.stderr.write(str(code) + '\n')
        return 1
    except KeyboardInterrupt:
        _print_traceback()
        return 130
    except _CannotOpen as problem:
        sys.stderr.write(str(problem) + '\n')
        return 2
    except BaseException:
        _print_traceback()
        return 1
    return 0


if __name__ == '__main__':
    _status = main()
    _flush()
    # like python3 at its end: threads the program left running are waited for by the
    # interpreter's normal shutdown, and the exit status is the program's
    sys.exit(_status)
