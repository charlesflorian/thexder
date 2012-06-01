"""
data.py
Data manager for Thexder

Created by Chris Rose on 2012-05-31.
Copyright (c) 2012 Off By One Services. All rights reserved.
"""
import logging
import os

isfile = os.path.isfile
join = os.path.join

log = logging.getLogger(__name__)

class DataManager(object):

    def __init__(self, data_dir):
        self.data_dir = data_dir

    def load_file(self, name):
        if not self.has_data_file(name):
            raise ValueError("No such data file: {}".format(name))

        with open(self.data_file_name(name), 'rb') as fh:
            return fh.read()

    def has_data_file(self, name):
        return self.data_file_name(name) is not None

    def data_file_name(self, name):
        # try the name's case, and then try case-insensitive search
        if isfile(join(self.data_dir, name)):
            return join(self.data_dir, name)

        candidates = os.listdir(self.data_dir)

        for c in candidates:
            if c.lower() == name.lower():
                return join(self.data_dir, c)
