import os
import subprocess
import re
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Do something.")
    parser.add_argument('-i', '--index', type=int, required=True, help='Index of letter from 10 ~ 36')
    
    args = parser.parse_args()
    index = args.index

    processname = 'python random_sandiego.py -i {}'.format(index)
    tmp = os.popen("ps -Af").read()

    proccount = tmp.count(processname)

    if proccount > 0:
      print(proccount, ' processes running of ', processname, 'type')
    else:
      os.system(processname)