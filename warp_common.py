#!/usr/bin/env python



        
class ExtensionContext(object):
    def __init__(self, warp_home_dir, extension_name, description, logger):
        self.warp_home = warp_home_dir
        self.name = extension_name
        self.description = description
        self.logger = logger

