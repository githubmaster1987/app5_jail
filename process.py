import os
import subprocess
import re
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Do something.")
    parser.add_argument('-c', '--checkmiss', type=int, required=False, default=0, help='Generate Missing File')

    args = parser.parse_args()
    index_number = args.checkmiss

    processname = 'python auto.py -c {}'.format(index_number)
    tmp = os.popen("ps -Af").read()

    proccount = tmp.count(processname)

    if proccount > 0:
      print(proccount, ' processes running of ', processname, 'type')
    else:
      os.system(processname)