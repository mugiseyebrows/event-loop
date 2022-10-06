import argparse
import subprocess
import eventloop
from eventloop import on_file_changed
import datetime
from colorama import Fore, Back, Style, init as colorama_init
import os
import sys
import shutil

# set DEBUG_ONCHANGE=1
# set DEBUG_ONCHANGE=0
# DEBUG_ONCHANGE=1
# DEBUG_ONCHANGE=0
if os.environ.get('DEBUG_ONCHANGE') == "1":
    debug_print = print
else:
    debug_print = lambda *args, **kwargs: None

def split(vs, sep):
    r = []
    for v in vs:
        if v == sep:
            yield r
            r = []
        else:
            r.append(v)
    yield r

WIN_BUILTINS = ['echo', 'dir', 'type']

def replace(cmd_orig, path):
    cmd = cmd_orig[:]
    if sys.platform == 'win32' and cmd[0] in WIN_BUILTINS:
        cmd = ['cmd','/c'] + cmd
    cmd = [path if arg == 'FILE' else arg for arg in cmd]
    return cmd

def now_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class Logger(eventloop.base.Logger):

    def print_error(self, msg):
        print(Fore.WHITE + now_str() + " " + Fore.RED + msg + Fore.RESET)

def main():
    colorama_init()
    logger = Logger()
    example_text = """
examples:
  python -m eventloop.onchange D:\\dev\\app -- echo FILE
  onchange D:\\dev\\app -- echo FILE
  onchange D:\\dev\\app -i *.cpp *.ui --cwd D:\\dev\\app\\build -- ninja ^&^& ctest
    """
    parser = argparse.ArgumentParser(prog="onchange", epilog=example_text, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('src', help="directory or file to watch")
    parser.add_argument('-i','--include', nargs='+', help="include globs")
    parser.add_argument('-e','--exclude', nargs='+', help="exclude globs")
    parser.add_argument('-c','--cwd', help='cwd for command')
    parser.add_argument('-t', '--timeout', type=float, default=1)
    parser.add_argument('-n', '--non-recursive', action='store_true', help="non recursive (do not look for changes in subdirectories)")
    parser.add_argument('cmd', nargs='+', help="command to execute")
    args = parser.parse_args()
    #print(args); exit(0)
    cmds = list(split(args.cmd, '&&'))

    for cmd in cmds:
        executable = cmd[0]
        if sys.platform == 'win32' and executable in WIN_BUILTINS:
            pass
        elif os.path.isfile(executable):
            pass
        elif shutil.which(executable):
            pass
        else:
            logger.print_error("{} not found".format(executable))
            return

    debug_print("cmds", cmds)

    recursive = not args.non_recursive

    @on_file_changed(args.src, recursive=recursive, include=args.include, exclude=args.exclude, timeout=args.timeout)
    def handler(path):
        debug_print("handler for {}".format(path))
        for cmd in cmds:
            cmd = replace(cmd, path)
            debug_print("cmd", cmd)
            try:
                proc = subprocess.run(cmd, cwd=args.cwd)
                if proc.returncode != 0:
                    break
            except FileNotFoundError as e:
                logger.print_error("{} not found".format(cmd[0]))
                break
