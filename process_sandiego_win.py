import os
import subprocess
import re
import argparse
import psutil

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Do something.")
    parser.add_argument('-i', '--index', type=int, required=True, help='Index of letter from 10 ~ 36')

    args = parser.parse_args()
    index = args.index
    processname = 'python random_sandiego.py -i {}'.format(index)

    process_running = False 
    for process in psutil.process_iter():
        try:
            cmdline = process.cmdline()
            for t in cmdline:
                if "random_sandiego" in t:
                    print cmdline

                    if cmdline[3] == str(index):
                        process_running = True
        except:
            pass

    if process_running == True:
        print(' processes running of ', processname, 'type')
    else:
        os.system(processname)