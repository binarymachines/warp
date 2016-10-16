#!/usr/bin/env python

import re
import sys
import json
import os


SALTS_FILE = 'roles/wordpress/files/salts.txt'
saltKeyRegex = re.compile(r"(define\(\')[A-Z_]*\'")
saltValueRegex = re.compile(r"'([^']*)'\);$")


def parseSaltsFile(fileHandle):
    results = {}
    
    for line in fileHandle.readlines():
        keyMatch = saltKeyRegex.search(line.rstrip())
        valueMatch = saltValueRegex.search(line.rstrip())
        
        keySection = line[keyMatch.start():keyMatch.end()]
        valueSection = line[valueMatch.start():valueMatch.end()-2]

        key = keySection.split("'")[1]
        value = valueSection.strip("'")
        
        results[key] = value

    return results


def main():
    data = None
    saltFilePath = os.path.join(os.getcwd(), SALTS_FILE)
    with open(saltFilePath, 'r') as saltsFile:
        data = parseSaltsFile(saltsFile)   


    for key in data.keys():
        pass
        #print '%s: %s\n' % (key, data[key])

    sys.stdout.write('%s\n' % json.dumps(data))
    sys.stdout.flush()

if __name__ == '__main__':
   main()
