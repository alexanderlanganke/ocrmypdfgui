#!/usr/bin/env python3
import sys
import gui

def main(args=None):
	if args is None:
		args = sys.argv[1:]
	gui.run()

if __name__ == '__main__':
	sys.exit(main())
