#!/usr/bin/env python
# coding:utf-8
if __name__ == '__main__':
    import sys

    if sys.maxunicode > 65535:
        print 'UCS4 build'
    else:
        print 'UCS2 build'