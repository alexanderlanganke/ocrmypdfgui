#!/usr/bin/env python3

from ocrmypdf import hookimpl

class ocrmypdf_progressbar_singlefile:

    def __init__(self, **kwargs):
        callback = None
        singlefile_progress = None
        singlefile_progress_info = None

        print("initialized progressbar_singlefile")
        print(kwargs)
        print(kwargs['total'])
        self.args = kwargs

    @classmethod
    def set_callback(cls, cb, singlefile_progress, singlefile_progress_info):
        print("set_callback")
        cls.callback = cb
        cls.singlefile_progress = singlefile_progress
        cls.singlefile_progress_info = singlefile_progress_info

    def __enter__(self):
        print("Entering Progressbar")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print("Exiting Progressbar")
        return False

    def update(self, _arg=None):
        print("Updating")
        self.callback(self.args, self.singlefile_progress, self.singlefile_progress_info)
        return


@hookimpl
def get_progressbar_class():
    print("Hook activated")
    return ocrmypdf_progressbar_singlefile
