#!/usr/bin/env python3

from ocrmypdf import hookimpl

class ocrmypdf_progressbar_singlefile:

    def __init__(self, **kwargs):
        print("initialized progressbar_singlefile")
        print(kwargs)
        print(kwargs['total'])
        #print(kwargs['desc'])
        #print(kwargs['unit'])
        #print(100/kwargs['total'])
        self.total = kwargs['total']

    def __enter__(self):
        print("Entering Progressbar")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print("Exiting Progressbar")
        return False

    def update(self, _arg=None):
        print("Updating")
        print(self.total)
        #singlefile_progress.set(singlefile_progress.get()+self.total)
        return


@hookimpl
def get_progressbar_class():
    print("Hook activated")
    return ocrmypdf_progressbar_singlefile
