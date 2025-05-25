#!/usr/bin/env python3

from ocrmypdf import hookimpl
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, GLib

class ocrmypdf_progressbar_singlefile:

    def __init__(self, **kwargs):
        # callback, singlefile_progress, singlefile_progress_info are class variables, remove them from here.
        print("initialized progressbar_singlefile")
        print(kwargs)
        self.total = kwargs.get('total')
        self.desc = kwargs.get('desc', 'Processing...') # Default description
        self.unit = kwargs.get('unit')
        self.disable = kwargs.get('disable', False)
        self.current_step = 0.0 # For incremental updates if 'completed' is not given
        # self.args stores all kwargs, which is fine for desc, but specific progress needs calculation
        self.args = kwargs

    @classmethod
    def set_callback(cls, cb): # Removed singlefile_progress, singlefile_progress_info
        print("set_callback")
        cls.update_gui_callback = cb
        # Remove cls.singlefile_progress and cls.singlefile_progress_info

    def __enter__(self):
        print("Entering Progressbar")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print("Exiting Progressbar")
        return False

    def update(self, n=1, *, completed=None):
        if self.disable or not hasattr(self.__class__, 'update_gui_callback'):
            return

        progress_fraction = 0.0
        current_description = self.args.get('desc', self.desc) # Use self.desc as fallback

        if completed is not None:
            if self.total and self.total > 0:
                progress_fraction = float(completed) / float(self.total)
            elif self.unit == '%' and self.total == 100: # If total is 100, completed is likely the percentage
                 progress_fraction = float(completed) / 100.0
            else: # Fallback if total is not set as expected, assume completed is a fraction
                progress_fraction = float(completed) if float(completed) <=1.0 else float(completed)/100.0


        elif self.total and self.total > 0:
            self.current_step += n
            progress_fraction = float(self.current_step) / float(self.total)
        
        progress_fraction = min(max(0.0, progress_fraction), 1.0)

        # The description might be updated if OCRmyPDF re-initializes the progress bar for new stages.
        # The 'desc' from self.args (kwargs from __init__) is the most reliable here.
        GLib.idle_add(lambda: self.__class__.update_gui_callback(current_description, progress_fraction))
        return


@hookimpl
def get_progressbar_class():
    print("Hook activated")
    return ocrmypdf_progressbar_singlefile
