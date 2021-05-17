#!/usr/bin/env python3
import threading
import ocrmypdf
import os
import sys
import warnings
import inspect

from PIL import Image
warnings.simplefilter('ignore', Image.DecompressionBombWarning)


def start_job(dir_path, progressbar_batch, ocrmypdfsettings):
	t = threading.Thread(target=batch_ocr, args=(dir_path, progressbar_batch, ocrmypdfsettings), daemon=True)
	t.start()

def ocr_run(file_path, ocrmypdfsettings):
	#runs ocrmypdf on given file
	try:

		ocr = ocrmypdf.ocr(file_path, file_path, **ocrmypdfsettings, plugins=["ocrmypdfgui.plugin_progressbar"])

		print("OCR complete.\n")
		return "end", "OCR complete.\n"
	except ocrmypdf.exceptions.PriorOcrFoundError:

		print("Prior OCR - Skipping\n")
		return "Prior OCR - SKipping\n"
	except ocrmypdf.exceptions.EncryptedPdfError:

		print("PDF File is encrypted. Skipping.\n")
		return "PDF File is encrypted. Skipping.\n"

	except ocrmypdf.exceptions.BadArgsError:
		print("Bad arguments.")

	except:
		e = sys.exc_info()[0]
		print(e)
		return "Error"

def batch_ocr(dir_path, progressbar_batch, ocrmypdfsettings):
	# walks through given path and uses OCR Function on every pdf in path
	progressbar_batch.set(0.0)	#resets Progressbar
	progress_precision = 0.0

	if(os.path.isfile(dir_path)==True):
		#Run OCR on single file
		file_ext = os.path.splitext(dir_path)[1]
		if file_ext == '.pdf':

			print("Path:" + dir_path + "\n")
			ocr_run(dir_path, ocrmypdfsettings)
			progressbar_batch.set(100)
	elif(os.path.isdir(dir_path)==True):
		number_of_files = 0
		for dir_name, subdirs, file_list in os.walk(dir_path):
			for filename in file_list:
				file_ext = os.path.splitext(filename)[1]
				if file_ext == '.pdf':
					number_of_files=number_of_files+1

			percent = 100/number_of_files
		for dir_name, subdirs, file_list in os.walk(dir_path):
			print(file_list)

			for filename in file_list:
				file_ext = os.path.splitext(filename)[1]
				if file_ext == '.pdf':
					full_path = dir_name + '/' + filename

					print("Path:" + full_path + "\n")
					ocr_run(full_path, ocrmypdfsettings)
					progress_precision = progress_precision + percent
					progressbar_batch.set(round(progress_precision))

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
	        if str(param.annotation)[8:-2] == "bool" or str(param.annotation)[8:-2] == "int" or str(param.annotation)[8:-2] == "float" or str(param.annotation)[8:-2] == "str":
	            dict[param.name] = str(param.annotation)[8:-2]

	return dict
