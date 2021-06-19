#!/usr/bin/env python3
import sys
from ocrmypdfgui.gui import run

def main(args=None):
	if args is None:
		args = sys.argv[1:]
		run()

if __name__ == '__main__':
	sys.exit(main())
