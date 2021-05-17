#!/usr/bin/env python3

from ocrmypdf import hookimpl

class ocrmypdf_progressbar_singlefile:

    def __init__(self, **kwargs):
        print("initialized progressbar_singlefile")


    def __enter__(self):
        print("Entering Progressbar")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print("Exiting Progressbar")
        return False

    def update(self, _arg=None):
        print("Updating")
        return


@hookimpl
def get_progressbar_class():
    print("Hook activated")
    return ocrmypdf_progressbar_singlefile
