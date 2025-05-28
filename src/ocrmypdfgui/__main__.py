#!/usr/bin/env python3
import sys
import logging
from ocrmypdfgui.gui import run
#from gui import run

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logging.debug("Application starting up")

def main(args=None):
	if args is None:
		args = sys.argv[1:]
		run()

if __name__ == '__main__':
	sys.exit(main())
