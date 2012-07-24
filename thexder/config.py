import os
import sys
import argparse

def base_argument_parser():
    parser = argparse.ArgumentParser(description="Thexder")
    parser.add_argument('-d', '--data-dir', default=os.path.join(os.getcwd(), 'data'))
    return parser

_app_config = None

def set_app_config_from_cli(parser, args=sys.argv[1:]):
    global _app_config
    _app_config = parser.parse_args()


def app_config():
    return _app_config
