import os, sys

# get parent's path
path = os.path.dirname(os.path.abspath('__file__'))
path = path.split('/')[:-1]
path = '/'.join(path)

# change directry
os.chdir(path)
sys.path.append(path)

# run
from lib.buckler import buckler

b = buckler(b'hogehoge')
b = b.scan()
