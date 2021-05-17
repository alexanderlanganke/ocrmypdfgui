#!/usr/bin/env python3
import sys
import ocrmypdfgui.gui

def main(args=None):
	if args is None:
		args = sys.argv[1:]
	ocrmypdfgui.gui.run()

if __name__ == '__main__':
	sys.exit(main())
