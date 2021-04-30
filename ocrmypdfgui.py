#!/usr/bin/env python3

import logging
import warnings
from PIL import Image
warnings.simplefilter('ignore', Image.DecompressionBombWarning)

import os
import sys
import ocrmypdf
from tkinter import *
from tkinter.filedialog import askdirectory
from tkinter.filedialog import askopenfilename


class ocrmypdfgui:
	def __init__(self, myParent):
		#init variables
		self.script_dir = os.path.dirname(os.path.realpath(__file__))
		self.dir_path = StringVar()
		self.dir_path.set("~/Documents")

		#BUILD GUI MAIN WINDOW
		root.geometry("%dx%d%+d%+d" % (500, 500,0,0))
		#MENUBAR
		menubar = Menu(root)
		filemenu = Menu(menubar, tearoff=0)
		filemenu.add_separator()
		filemenu.add_command(label="Exit", command=root.quit)
		menubar.add_cascade(label="File", menu=filemenu)

		root.config(menu=menubar)

		#WINDOW
		self.myContainer1 = Frame(myParent)
		self.myContainer1.pack()
		self.containertop = Frame (self.myContainer1)
		self.containertop.pack(side=TOP)
		self.containerbottom = Frame(self.myContainer1)
		self.containerbottom.pack(side=BOTTOM)

		self.containerleft = Frame(self.containertop)
		self.containerleft.pack(side=LEFT)
		self.containerright = Frame(self.containertop)
		self.containerright.pack(side=RIGHT)

		self.container_bar = Frame(self.containerbottom)
		self.container_bar.pack(side=BOTTOM)

		self.container_percent = Frame(self.container_bar)
		self.container_percent.pack(side=BOTTOM)

		self.dir_path_label = Label(self.containerleft, textvariable=self.dir_path)
		self.dir_path_label.pack()
		self.text = Text(self.containerbottom, undo = True, height = 20, width = 70)
		self.text.pack(expand = True)

		#Choose Path
		self.button1 = Button(self.containerbottom, text="Choose Batch OCR Directory", command=lambda: self.choose_batch_directory(self, self.dir_path) )
		self.button1.pack(side=LEFT)

		#Choose File
		self.button2 = Button(self.containerbottom, text="Choose Single File", command=lambda: self.choose_file(self, self.dir_path) )
		self.button2.pack(side=LEFT)

		#Start OCR
		self.button3 = Button(self.containerbottom, text="Start OCR Job", command=lambda: self.batch_ocr(self, self.dir_path.get()) )
		self.button3.pack(side=LEFT)

		self.label_info = Label(self.container_bar, text="Idle")
		self.label_info.pack(side=LEFT)


	def choose_batch_directory(self, myParent, dir_path):
		#Runs Pathpicker and sets path variable
		dir_path.set(askdirectory())
		root.update_idletasks()
		print ("test directory")
		print(dir_path.get())

	def choose_file(self, myParent, dir_path):
		#Runs Filepicker and sets path variable
		dir_path.set(askopenfilename(filetypes=[("PDF files", ".pdf")]))
		root.update_idletasks()
		print ("test filepicker")
		print(dir_path.get())


	def ocr_run(self, myParent, file_path):
		#runs ocrmypdf on given file
		try:
			result = ocrmypdf.ocr(file_path, file_path, clean=True, language="deu+eng", deskew=True)
			self.text.insert("end", "OCR complete.\n")
			root.update_idletasks()

			print("OCR complete.\n")
			return result
		except ocrmypdf.exceptions.PriorOcrFoundError:
			self.text.insert("end", "Prior OCR - Skipping\n")
			root.update_idletasks()

			print("Prior OCR - Skipping\n")
			return "Error"
		except ocrmypdf.exceptions.EncryptedPdfError:
			self.text.insert("end", "PDF File is encrypted. Skipping.\n")
			root.update_idletasks()

			print("PDF File is encrypted. Skipping.\n")
			return "Error"

		except:
			e = sys.exc_info()[0]
			print(e)
			return "Error"

	def batch_ocr(self, myParent, dir_path):
		# walks through given path and uses OCR Function on every pdf in path
		self.text.insert("1.0", "Starting. \n")
		root.update_idletasks()

		if(os.path.isfile(dir_path)==True):
			#Run OCR on single file
			file_ext = os.path.splitext(dir_path)[1]
			if file_ext == '.pdf':
				self.text.insert("end", "Path:" + dir_path + "\n")
				root.update_idletasks()

				print("Path:" + dir_path + "\n")
				self.ocr_run(self, dir_path)
		elif(os.path.isdir(dir_path)==True):
			for dir_name, subdirs, file_list in os.walk(dir_path):
				print(file_list)

				for filename in file_list:
					file_ext = os.path.splitext(filename)[1]
					if file_ext == '.pdf':
						full_path = dir_name + '/' + filename
						self.text.insert("end", "Path:" + full_path + "\n")
						root.update_idletasks()

						print("Path:" + full_path + "\n")
						self.ocr_run(self, full_path)
		else:
			print("Error")

root = Tk()
root.title("ocrmypdfgui 0.1")
ocrmypdfgui = ocrmypdfgui(root)
root.mainloop()
