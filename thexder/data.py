"""
data.py
Data manager for Thexder

Created by Chris Rose on 2012-05-31.
Copyright (c) 2012 Off By One Services. All rights reserved.
"""
import logging
import os
import shutil
from datetime import datetime
from contextlib import contextmanager

from . import config

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

    def data_file_name(self, name, force=False):
        # try the name's case, and then try case-insensitive search
        if isfile(join(self.data_dir, name)):
            return join(self.data_dir, name)

        candidates = os.listdir(self.data_dir)

        for c in candidates:
            if c.lower() == name.lower():
                return join(self.data_dir, c)

        if force:
            return join(self.data_dir, name.upper())

    def backup(self, name):
        backup_name = '{}.backup-{}'.format(name, datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
        shutil.copy(self.data_file_name(name),
                    join(self.data_dir, backup_name))

    @contextmanager
    def write(self, name):
        existing_data_file = self.data_file_name(name)
        if existing_data_file:
            self.backup(existing_data_file)

        with open(self.data_file_name(name, force=True), 'wb') as fh:
            yield fh

manager = None

def default_data_manager():
    global manager
    if manager is None:
        manager = DataManager(config.app_config().data_dir)

    return manager
