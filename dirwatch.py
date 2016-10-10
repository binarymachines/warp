#!/usr/bin/env python


import yaml
import argparse
import sys
import logging
import json



class FileCreationEventHandler(FileSystemEventHandler):

      def __init__(self, triggerCommandLine, logFilename):
            self.triggerCommandLine = triggerCommandLine
            self.logFilename = logFilename
            self.host = socket.gethostname()
            self.recursiveBit = 0
            self.triggerVars = {}


      def setRecursiveBit(self):
            self.recursiveMode = 1      


      def clearRecursiveBit(self):
         self.recursiveBit = 0
         

      def setTriggerVariable(self, variableName, value):
         self.triggerVars[variableName] = str(value)


      def invokeTrigger(self):
         commandLine = self.replaceVars()
         return commandLine


      def on_created(self, event):
         if not event.is_directory:                
                self.log('New file created in target location: %' % event.src_path)
                self.log('Invoking trigger command [ %s ]...' % self.triggerCommandLine)
                
                



def main(argv):
    parser = argparse.ArgumentParser(description = 'Directory monitoring program')
    #parser.add_argument('-i', metavar='initfile', nargs=1, required=True, help='YAML init file')
    parser.add_argument('-p', metavar='path', nargs=1, required=True, help='path to monitor')
    parser.add_argument('-t', metavar='trigger', nargs=1, required=True, help='execution target')
    
    args = parser.parse_args(argv)

    path = args.p[0]
    triggerProgram = args.t[0]

    eventHandler = FileCreationEventHandler('xml_import.py -i xml_import.yaml $file', 'fsevents.log')
    

    targetPath = args.path
   
      monitor = fsmonitor.FSMonitor(targetDirectory, eventHandler, False)
      logFilename = None
      outputFile = sys.stdout

      monitor.start()
      try:
            while True:
                  time.sleep(1)                  
                  outputFile.write('Monitoring target %s at time %s...\n' % (targetDirectory, str(datetime.datetime.now())))
      except KeyboardInterrupt:
            monitor.stop()
      finally:
            if logFilename:
                  outputFile.close()
                  
      monitor.observer.join()

    
    


if __name__ == '__main__':
   main(sys.argv[1:]) 
