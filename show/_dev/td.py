#!/usr/bin/env python3
"""Pošle Python kód do běžícího TouchDesigneru (DJ_Show.toe → /project1/dev_bridge) a vypíše výstup.
Použití:  python3 td.py 'print(op("/project1"))'   nebo   python3 td.py -f soubor.py"""
import os, sys, time, uuid
D = os.path.dirname(os.path.abspath(__file__))
code = open(sys.argv[2], encoding='utf-8').read() if sys.argv[1] == '-f' else sys.argv[1]
tag = '# ' + uuid.uuid4().hex
out = os.path.join(D, 'out.txt')
open(os.path.join(D, 'cmd.py'), 'w', encoding='utf-8').write(tag + '\n' + code)
t0 = time.time()
while time.time() - t0 < float(os.environ.get('TD_TIMEOUT', 30)):
    try:
        s = open(out, encoding='utf-8').read()
        if s.startswith(tag) and s.rstrip().endswith('#DONE'):
            print(s[len(tag) + 1:].rstrip()[:-5].rstrip()); sys.exit(0)
    except OSError: pass
    time.sleep(0.15)
print('TIMEOUT: TouchDesigner neodpověděl'); sys.exit(1)
