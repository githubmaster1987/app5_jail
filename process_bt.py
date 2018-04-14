import os
import subprocess
import re
import argparse
import psutil

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Do something.")
    parser.add_argument('-m', '--method', type=int, required=False, default=0,
                        help='0: random, 1: first, 2: last')

    args = parser.parse_args()
    method = args.method
    processname = 'python bot.py -m {}'.format(method)


    process_running = False 
    for process in psutil.process_iter():
        try:
            cmdline = process.cmdline()
            for t in cmdline:
                if "bot" in t:
                    print cmdline

                    if cmdline[3] == str(method):
                        process_running = True
        except:
            pass

    if process_running == True:
        print(' processes running of ', processname, 'type')
    else:
        os.system(processname)