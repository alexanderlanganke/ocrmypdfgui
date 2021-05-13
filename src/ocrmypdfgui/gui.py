#!/usr/bin/env python3


import os
import sys
import string
import ocr
from tkinter import *
from tkinter.filedialog import askdirectory
from tkinter.filedialog import askopenfilename
from tkinter.ttk import *


class ocrmypdfgui:
	def __init__(self, myParent):
		#init variables
		self.script_dir = os.path.dirname(os.path.realpath(__file__))
		self.dir_path = StringVar()
		self.dir_path.set("~/Documents")
		self.batch_progress = StringVar()
		self.batch_progress.set(0.0)
		self.singlefile_progress = StringVar()
		self.ocrmypdfsettings = {}
		self.ocrmypdfapioptions = ocr.get_api_options()
		self.ocrmypdfapioptions_bool = ["deskew", "clean"] # Instantiate list, fill with settings
		self.ocrmypdfapioptions_optionsdict = {"lang": {0:"eng", 1:"deu", 2:"fr"}} #List options as dict
		self.load_settings()

		#BUILD GUI MAIN WINDOW
		#myParent.geometry("%dx%d%+d%+d" % (500, 500,0,0))
		#MENUBAR
		menubar = Menu(myParent)
		filemenu = Menu(menubar, tearoff=0)
		filemenu.add_command(label="Settings", command=lambda: self.open_settings(myParent))
		filemenu.add_separator()
		filemenu.add_command(label="Exit", command=myParent.quit)
		menubar.add_cascade(label="File", menu=filemenu)

		myParent.config(menu=menubar)

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

		self.container_bar_batch = Frame(self.containerbottom)
		self.container_bar_batch.pack(side=BOTTOM)
		self.container_bar_singlefile = Frame(self.containerbottom)
		self.container_bar_singlefile.pack(side=BOTTOM)

		self.dir_path_label = Label(self.containerleft, textvariable=self.dir_path)
		self.dir_path_label.pack()
		#self.text = Text(self.containerbottom, undo = True, height = 20, width = 70)
		#self.text.pack(expand = True)

		#Choose Path
		self.button1 = Button(self.containerbottom, text="Choose Batch OCR Directory", command=lambda: self.choose_batch_directory(self, self.dir_path) )
		self.button1.pack(side=LEFT)

		#Choose File
		self.button2 = Button(self.containerbottom, text="Choose Single File", command=lambda: self.choose_file(self, self.dir_path) )
		self.button2.pack(side=LEFT)

		#Start OCR
		self.button3 = Button(self.containerbottom, text="Start OCR Job", command=lambda: ocr.start_job(self.dir_path.get(), self.batch_progress) )
		self.button3.pack(side=LEFT)

		#Progress
		#Batch
		self.progressbar_batch = Progressbar(self.container_bar_batch, orient="horizontal", length=100, mode="determinate", variable=self.batch_progress)
		self.progressbar_batch.pack(side=LEFT)
		self.label_info_batch = Label(self.container_bar_batch, textvariable=self.batch_progress)
		self.label_info_batch.pack(side=LEFT)
		self.label_info_batch_percent= Label(self.container_bar_batch, text="%")
		self.label_info_batch_percent.pack(side=RIGHT)
		#SingleFile
		self.progressbar_singlefile = Progressbar(self.container_bar_singlefile, orient="horizontal", length=100, mode="determinate")
		self.progressbar_singlefile.pack(side=LEFT)
		self.label_info_singlefile = Label(self.container_bar_singlefile, textvariable=self.singlefile_progress)
		self.label_info_singlefile.pack(side=RIGHT)

	def open_settings(self, myParent):
		settings=Toplevel(myParent) # Child window
		#settings.geometry("200x200")  # Size of the window
		settings.title("Settings")
		myContainer2 = Frame(settings)
		myContainer2.pack()

		dynamic_widgets = {}
		#i=1
		for k, v in self.ocrmypdfapioptions.items():
			#dynamically create widgets here
			if v == "bool":
				dynamic_widgets[k] = Checkbutton(myContainer2, text=k)#settings, text=k, variable=dynamic_widgets[i]["setting"])
				dynamic_widgets[k].pack()
				#i=i+1
		for k, v in self.ocrmypdfapioptions.items():
				#dynamically create widgets here
			if v == "str":
				dynamic_widgets[k] = Entry(myContainer2)#settings, text=k, variable=dynamic_widgets[i]["setting"])
				dynamic_widgets[k].insert(0, k)
				dynamic_widgets[k].pack()

		savebutton = Button(myContainer2, text="Save Settings", command=lambda: self.save_settings(settings, dynamic_widgets) )
		savebutton.pack()

	def save_settings(self, w, dynamic_widgets):

		print("Settings Saved")
		w.destroy()

	def load_settings(self):
		print("Settings Loaded")

		#Open Settings File
		settings= os.path.join(os.path.dirname(__file__), 'settings.ini')
		f = open(settings)
		lines = f.read().splitlines()
		f.close()

		#Iterate over Settings and Import into Settings Dictionary

		for items in lines:
			temp_string = items.split('-:-')
			if(temp_string[1] == "bool"):
				try:
					key = temp_string[0]
					value = temp_string[2]
					self.ocrmypdfsettings[key] = value
				except:
					print("nothing left to append")
					traceback.print_exc(file=sys.stdout)
			elif(temp_string[1] == "list"):
				try:
					key = temp_string[0]
					value = temp_string[2]
					self.ocrmypdfsettings[key] = []
					list_split = value.split(',')
					self.ocrmypdfsettings[key] = list_split

				except:
					print("nothing left to append")
					traceback.print_exc(file=sys.stdout)
			else:
				print("Error loading Settings")

			for value in self.ocrmypdfsettings:
				print("Type of value" + str(type(key)))



	def choose_batch_directory(self, myParent, dir_path):
		#Runs Pathpicker and sets path variable
		dir_path.set(askdirectory())
		#root.update_idletasks()
		print ("test directory")
		print(dir_path.get())

	def choose_file(self, myParent, dir_path):
		#Runs Filepicker and sets path variable
		dir_path.set(askopenfilename(filetypes=[("PDF files", ".pdf")]))
		#self.update_idletasks()
		print ("test filepicker")
		print(dir_path.get())



def run():
	root = Tk()
	root.title("ocrmypdfgui")
	ocrmypdfgui(root)
	root.mainloop()
