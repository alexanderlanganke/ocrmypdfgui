#!/usr/bin/env python3
import threading
import ocrmypdf
import os
import sys
import threading
import warnings
import plugin_progressbar

from PIL import Image
warnings.simplefilter('ignore', Image.DecompressionBombWarning)


def start_job(dir_path):
	t = threading.Thread(target=batch_ocr, args=(dir_path,), daemon=True)
	t.start()
	#batch_ocr(dir_path)

def ocr_run(file_path):
	#runs ocrmypdf on given file
	try:
		ocrmypdf.ocr(file_path, file_path, clean=True, language="deu+eng", deskew=True, plugins="plugin_progressbar.py")

		print("OCR complete.\n")
		return "end", "OCR complete.\n"
	except ocrmypdf.exceptions.PriorOcrFoundError:

		print("Prior OCR - Skipping\n")
		return "Prior OCR - SKipping\n"
	except ocrmypdf.exceptions.EncryptedPdfError:

		print("PDF File is encrypted. Skipping.\n")
		return "PDF File is encrypted. Skipping.\n"

	except:
		e = sys.exc_info()[0]
		print(e)
		return "Error"

def batch_ocr(dir_path):
	# walks through given path and uses OCR Function on every pdf in path
	#self.batch_progress.set(0.0)
	#root.update_idletasks()

	if(os.path.isfile(dir_path)==True):
		#Run OCR on single file
		file_ext = os.path.splitext(dir_path)[1]
		if file_ext == '.pdf':
			#root.update_idletasks()

			print("Path:" + dir_path + "\n")
			ocr_run(dir_path)
			#progressbar_batch['value'] = 100
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
					#root.update_idletasks()

					print("Path:" + full_path + "\n")
					ocr_run(full_path)
					#batch_progress.set(float(self.batch_progress.get())+percent)
					#self.progressbar_batch['value']=float(self.batch_progress.get())
						#root.update_idletasks()

	else:
		print("Error")
		#self.text.insert("Error\n")
			#root.update_idletasks()
