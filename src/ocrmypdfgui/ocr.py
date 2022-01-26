#!/usr/bin/env python3
import threading
import ocrmypdf
import os
import sys
import warnings
import inspect
import gi
import time

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, GLib

from PIL import Image
warnings.simplefilter('ignore', Image.DecompressionBombWarning)


def start_job(dir_path, progressbar_batch, print_to_textview, ocrmypdfsettings):
	t = threading.Thread(target=batch_ocr, args=(dir_path, progressbar_batch, print_to_textview, ocrmypdfsettings), daemon=True)
	t.start()
	return t


def ocr_run(file_path, ocrmypdfsettings, print_to_textview):
	print(ocrmypdfsettings)
	#runs ocrmypdf on given file
	try:
		print("Start OCR - " + file_path)
#		ocr = ocrmypdf.ocr(file_path, file_path, **ocrmypdfsettings, plugins=["plugin_progressbar"])
		ocr = ocrmypdf.ocr(file_path, file_path, **ocrmypdfsettings, plugins=["ocrmypdfgui.plugin_progressbar"])
		GLib.idle_add(print_to_textview, "OCR complete.\n")

		print("OCR complete.\n")
		return "OCR complete.\n"

	except ocrmypdf.exceptions.PriorOcrFoundError:
		GLib.idle_add(print_to_textview, "Prior OCR - Skipping\n")
		print("Prior OCR - Skipping\n")
		return "Prior OCR - Skipping\n"

	except ocrmypdf.exceptions.EncryptedPdfError:
		GLib.idle_add(print_to_textview, "PDF File is encrypted. Skipping.\n")
		print("PDF File is encrypted. Skipping.\n")
		return "PDF File is encrypted. Skipping.\n"

	except ocrmypdf.exceptions.BadArgsError:
		GLib.idle_add(print_to_textview, "Bad arguments.\n")
		print("Bad arguments.\n")

	except:
		e = sys.exc_info()
		GLib.idle_add(print_to_textview, str(e))
		GLib.idle_add(print_to_textview, "\n")
		#time.sleep(0.2)
		print(e)
		return "Error.\n"

def batch_ocr(dir_path, progressbar_batch, print_to_textview, ocrmypdfsettings):
	# walks through given path and uses OCR Function on every pdf in path
	GLib.idle_add(progressbar_batch, 0.0) #resets progressbar_batch
	progress_precision = 0.0
	percent_step = 0.0
	if(os.path.isfile(dir_path)==True):
		#Run OCR on single file
		file_ext = os.path.splitext(dir_path)[1]
		if file_ext == '.pdf':

			print("Path:" + dir_path + "\n")
			GLib.idle_add(print_to_textview, "File: " + dir_path + " - ")

			result = ocr_run(dir_path, ocrmypdfsettings, print_to_textview)
			GLib.idle_add(progressbar_batch, 1.0) #Sets progressbar_batch to 100%
	elif(os.path.isdir(dir_path)==True):
		number_of_files = 0
		for dir_name, subdirs, file_list in os.walk(dir_path):
			for filename in file_list:
				file_ext = os.path.splitext(filename)[1]
				if file_ext == '.pdf':
					number_of_files=number_of_files+1

			if number_of_files >0:
				percent_step = 1/number_of_files	#1 = 100%
				print("percent_step: " + str(percent_step) + " - " + "number_of_files: " + str(number_of_files))
		for dir_name, subdirs, file_list in os.walk(dir_path):
			print(file_list)

			for filename in file_list:
				file_ext = os.path.splitext(filename)[1]
				if file_ext == '.pdf':
					full_path = dir_name + '/' + filename

					print("Path:" + full_path + "\n")
					GLib.idle_add(print_to_textview, "File: " + full_path + " - ")
					result = ocr_run(full_path, ocrmypdfsettings, print_to_textview)
					progress_precision = progress_precision + percent_step #necessary to hit 100 by incrementing
					print(progress_precision)
					GLib.idle_add(progressbar_batch, progress_precision) #sets progressbar_batch to current progress



	else:
		print("Error")


def get_api_options():
	sig = inspect.signature(ocrmypdf.ocr)
	#print (str(sig))
	dict = {}
	for param in sig.parameters.values():
		if (param.kind == param.KEYWORD_ONLY):
			#print(param.name)
			#print(param.annotation)
			if str(param.annotation)[8:-2] == "bool" or str(param.annotation)[8:-2] == "int" or str(param.annotation)[8:-2] == "float" or str(param.annotation)[8:-2] == "str" or str(param.annotation) == "typing.Iterable[str]":
				if(str(param.annotation) == "typing.Iterable[str]"):
					dict[param.name] = str(param.annotation)
				else:
					dict[param.name] = str(param.annotation)[8:-2]

	return dict
