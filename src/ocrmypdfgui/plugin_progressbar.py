#!/usr/bin/env python3

import ocrmypdf

class ocrmypdf_progressbar_singlefile():

    def __init__(self, **kwargs):
        print("initialized progressbar_singlefile")


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def update(self, _arg=None):
        return


@ocrmypdf.hookimpl
def get_progressbar_class():
    return ocrmypdf_progressbar_singlefile
