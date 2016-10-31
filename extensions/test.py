#!/usr/bin/env python


from warp_common import ExtensionContext


def __load__(warp_home_dir, logger, **kwargs):
    print '### loading test extension module...'
    return ExtensionContext( warp_home_dir, __name__, 'test extension', logger)


def _ext1(self, args):
    '''No-op sample extension function'''
    print 'stub for dynamically loaded extension #1...'


def _ext2(self, args):
    '''No-op sample extension function'''
    print 'stub for dynamically loaded extension #2...'    
