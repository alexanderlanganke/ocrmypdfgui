#!/usr/bin/env python3
# Original version by DeliciousPickle@github; modified

# This script must be edited to meet your needs.

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


class ocrmypdf_batch:
	def __init__(self, myParent):
		#init variables
		self.script_dir = os.path.dirname(os.path.realpath(__file__))
		self.dir_path = StringVar()
		self.dir_path.set("~")

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

		#self.option = OptionMenu(self.containerright, self.show, "Choose Show", *self.show_options)
		#self.option.pack()

		#self.season_label = Label(self.containerleft, text="Season:")
		#self.season_label.pack()
		#self.season_box = Entry(self.containerright, textvariable=self.season)
		#self.season_box.pack()

		#self.episode_label = Label(self.containerleft, text="Episode:")
		#self.episode_label.pack()
		#self.episode_box = Entry(self.containerright, textvariable=self.episode)
		#self.episode_box.pack()

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
		#self.bar = Progressbar(self.container_bar, orient ="horizontal",length = 200, mode ="determinate")
		#self.bar.pack()
		#self.label_percent = Label(self.container_percent, text="")
		#self.label_percent.pack(side=RIGHT)

	def choose_batch_directory(self, myParent, dir_path):
		#Runs Pathpicker and sets path variable
		dir_path.set(askdirectory())
		root.update_idletasks()
		print ("test directory")
		print(dir_path.get())

	def choose_file(self, myParent, dir_path):
		#Runs Filepicker and sets path variable
		dir_path.set(askopenfilename())
		root.update_idletasks()
		print ("test filepicker")
		print(dir_path.get())


	def ocr_run(self, myParent, file_path):
		#runs ocrmypdf on given file
		try:
			result = ocrmypdf.ocr(file_path, file_path, clean=True, language="deu+eng", deskew=True)
			self.text.insert("end", "OCR complete.\n")
			print("OCR complete.\n")
			return result
		except ocrmypdf.exceptions.PriorOcrFoundError:
			self.text.insert("end", "Prior OCR - Skipping\n")
			print("Prior OCR - Skipping\n")
			return "Error"
		except ocrmypdf.exceptions.EncryptedPdfError:
			self.text.insert("end", "PDF File is encrypted. Skipping.\n")
			print("PDF File is encrypted. Skipping.\n")
			return "Error"

		except:
			e = sys.exc_info()[0]
			print(e)
			return "Error"

	def batch_ocr(self, myParent, dir_path):
		# walks through given path and uses OCR Function on every pdf in path
		self.text.insert("1.0", "Starting. \n")

		for dir_name, subdirs, file_list in os.walk(dir_path):
			#self.text.insert("end", "Found directory:" + dir_name + "\n")

			for filename in file_list:
				file_ext = os.path.splitext(filename)[1]
				if file_ext == '.pdf':
					full_path = dir_name + '/' + filename
					self.text.insert("end", "Path:" + full_path + "\n")
					print("Path:" + full_path + "\n")
					self.ocr_run(self, full_path)


root = Tk()
root.title("OCR-MyPDF 0.1")
ocrmypdf_batch = ocrmypdf_batch(root)
root.mainloop()
