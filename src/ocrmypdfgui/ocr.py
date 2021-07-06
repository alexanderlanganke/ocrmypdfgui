#!/usr/bin/env python3
import threading
import ocrmypdf
import os
import sys
import warnings
import inspect

from PIL import Image
warnings.simplefilter('ignore', Image.DecompressionBombWarning)


def start_job(dir_path, currentfile, progressbar_batch, progressbar_singlefile, outputarea, ocrmypdfsettings):
	t = threading.Thread(target=batch_ocr, args=(dir_path, progressbar_batch, progressbar_singlefile, outputarea, ocrmypdfsettings, currentfile), daemon=True)
	t.start()

def ocr_run(file_path, ocrmypdfsettings):
	print(ocrmypdfsettings)
	#runs ocrmypdf on given file
	try:
		ocr = ocrmypdf.ocr(file_path, file_path, **ocrmypdfsettings, plugins=["ocrmypdfgui.plugin_progressbar"])
		print("OCR complete.\n")
		return "OCR complete.\n"
	except ocrmypdf.exceptions.PriorOcrFoundError:

		print("Prior OCR - Skipping\n")
		return "Prior OCR - Skipping\n"
	except ocrmypdf.exceptions.EncryptedPdfError:

		print("PDF File is encrypted. Skipping.\n")
		return "PDF File is encrypted. Skipping.\n"

	except ocrmypdf.exceptions.BadArgsError:
		print("Bad arguments.\n")

	except:
		e = sys.exc_info()[0]
		print(e)
		return "Error.\n"

def batch_ocr(dir_path, progressbar_batch, progressbar_singlefile, outputarea, ocrmypdfsettings, currentfile):
	# walks through given path and uses OCR Function on every pdf in path
	progressbar_batch.set(0.0)	#resets Progressbar
	progress_precision = 0.0

	if(os.path.isfile(dir_path)==True):
		#Run OCR on single file
		file_ext = os.path.splitext(dir_path)[1]
		if file_ext == '.pdf':

			print("Path:" + dir_path + "\n")
			outputarea.insert("end", "File: " + dir_path + " - ")
			outputarea.see("end")
			currentfile.set("Current File:" + dir_path )
			result = ocr_run(dir_path, ocrmypdfsettings)
			outputarea.insert("end", result)
			outputarea.see("end")
			progressbar_batch.set(100)
	elif(os.path.isdir(dir_path)==True):
		number_of_files = 0
		for dir_name, subdirs, file_list in os.walk(dir_path):
			for filename in file_list:
				file_ext = os.path.splitext(filename)[1]
				if file_ext == '.pdf':
					number_of_files=number_of_files+1

			if number_of_files >0:
				percent = 100/number_of_files
		for dir_name, subdirs, file_list in os.walk(dir_path):
			print(file_list)

			for filename in file_list:
				file_ext = os.path.splitext(filename)[1]
				if file_ext == '.pdf':
					full_path = dir_name + '/' + filename

					print("Path:" + full_path + "\n")
					currentfile.set("Current File:" + full_path )
					outputarea.insert("end", "File: " + full_path + " - ")
					outputarea.see("end")

					result = ocr_run(full_path, ocrmypdfsettings)
					outputarea.insert("end", result)
					outputarea.see("end")

					progress_precision = progress_precision + percent
					print(progress_precision)
					progressbar_batch.set(round(progress_precision))
					progressbar_singlefile.set(0.0)

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
