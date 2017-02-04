#!/usr/bin/env python




class Stack:

    def __init__(self):
        self.items = []

    def is_empty(self):
        return self.items == []

    def push(self, item):
        self.items.append(item)

    def push_all(self, item_array):
        for i in item_array:
            self.push(i)

    def pop(self):
        return self.items.pop()

    def peek(self):
        return self.items[len(self.items)-1]

    def size(self):
        return len(self.items)

    def last_valid_index(self):
        return len(self.items) - 1 

    def index(self, i):
        return self.items[i]

    def clear(self):
        self.items = []

    def clone(self):
         s = Stack()
         s.items = list(self.items)
         return s


        
class ExtensionContext(object):
    def __init__(self, warp_home_dir, extension_name, description, logger):
        self.warp_home = warp_home_dir
        self.name = extension_name
        self.description = description
        self.logger = logger

