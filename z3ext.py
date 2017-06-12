#!/usr/bin/env python3
import re
import os.path
from itertools import *
import subprocess
import importlib
import argparse

import sys
import os
sys.path.insert(1,os.getcwd())

funclib = None

def readfile(fname):
    if(not os.path.isfile(fname)):
        print("FILE NOT FOUND")
        return
    res = ''
    with open(fname) as f:
        res = f.read()
    return res


def resolveNmodify(s, *modipat):
    for pattern, modify in modipat:
        #print(pattern)
        stillmatching = True
        depth = 0
        while stillmatching and depth < 10:
            stillmatching = False
            depth += 1
            for match in pattern.finditer(s):
                s = modify(s, match)
                stillmatching = True
    return s

includespattern = re.compile(r'^[ \t\r\f\v]*!\(include\s+\"(?P<fname>.+)\"\)', flags=re.MULTILINE)
def resolveincludes(s, match):
    return s.replace(match.group(0), readfile(match.group('fname')))

pyfuncpattern = re.compile(r'^[ \t\r\f\v]*!\(python\s+\"(?P<funcname>.+)\"\)', flags=re.MULTILINE)
def resolvepyruns(s, match):
    if funclib is None:
        raise ImportError("No function library imported, but python function makro used in z3e file")
    functions = funclib.getfunctions()
    func = functions[match.group("funcname")]
    return s.replace(match.group(0), func())

bashscriptpattern = re.compile(r'^[ \t\r\f\v]*!\(bash\s+\"(?P<cmd>.+)\"\)', flags=re.MULTILINE)
def resolvebashscripts(s, match):
    command = match.group("cmd")
    print(command)
    proc = subprocess.run(command, stdout=subprocess.PIPE, check=True, shell=True)
    return s.replace(match.group(0), proc.stdout.decode("utf-8"))
    
def doit(basefilestr, of):
    final = resolveNmodify(basefilestr,
                       (includespattern, resolveincludes),
                       (pyfuncpattern, resolvepyruns),
                       (bashscriptpattern, resolvebashscripts)
                      )
    of.write(final)

def main():
    global funclib
    parser = argparse.ArgumentParser(description='Z3Extended resolver: Resolves z3e files'+ 
                                                 'and outputs plain z3 files')
    parser.add_argument('--funclib', type=str, nargs='?',
                    help='the library which defines the callable functions')
    parser.add_argument('--in', dest='input',  type=open, nargs='?', default=sys.stdin,
                    help='input file (default=StdIN)')
    parser.add_argument('--out', dest='output', type=argparse.FileType('w'), nargs='?', default=sys.stdout,
                    help='output file (default=StdOUT)')
    parser.add_argument('--version', action='version', version='%(prog)s 0.11b')
    args = parser.parse_args()
    if args.funclib is not None:
        direc = os.path.dirname(args.funclib)
        base = os.path.basename(args.funclib)
        if direc != "" and direc is not None and direc not in sys.path:
            sys.path.insert(1, direc)
        funclib = importlib.import_module(os.path.splitext(base)[0])
    
    basefilestr = args.input.read()
    doit(basefilestr, args.output)

if __name__ == "__main__":
    main()
