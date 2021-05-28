#!/usr/bin/env python3


import os
import sys
import string
from ocr import start_job
from ocr import get_api_options
from plugin_progressbar import ocrmypdf_progressbar_singlefile
import json
from tkinter import *
from tkinter.filedialog import askdirectory
from tkinter.filedialog import askopenfilename
from tkinter.ttk import *
from tkinter import messagebox

class ocrmypdfgui:
	def __init__(self, myParent):
		#init variables
		self.script_dir = os.path.dirname(os.path.realpath(__file__))
		self.dir_path = StringVar()
		self.dir_path.set("")
		self.batch_progress = StringVar()
		self.batch_progress.set(0.0)
		self.singlefile_progress = StringVar()
		self.singlefile_progress.set(0.0)
		self.singlefile_progress_info = StringVar()
		self.singlefile_progress_info.set("Idle")
		self.currentfile = StringVar()
		self.ocrmypdfsettings = {}
		self.load_settings()
		self.ocrmypdfapioptions = get_api_options()


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
		self.containerinfo = Frame(self.myContainer1)
		self.containerinfo.pack(side=BOTTOM)

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
		self.button3 = Button(self.containerbottom, text="Start OCR Job", command=lambda: start_job(self.dir_path.get(), self.currentfile, self.batch_progress, self.singlefile_progress, self.ocrmypdfsettings) )
		self.button3.pack(side=LEFT)
		self.label_currentfile = Label(self.containerinfo, textvariable=self.currentfile)
		self.label_currentfile.pack(side=BOTTOM)

		#Progress
		#Batch
		self.progressbar_batch = Progressbar(self.container_bar_batch, orient="horizontal", length=100, mode="determinate", variable=self.batch_progress)
		self.progressbar_batch.pack(side=LEFT)
		self.label_info_batch = Label(self.container_bar_batch, textvariable=self.batch_progress)
		self.label_info_batch.pack(side=LEFT)
		self.label_info_batch_percent= Label(self.container_bar_batch, text="%")
		self.label_info_batch_percent.pack(side=RIGHT)
		#SingleFile
		self.progressbar_singlefile = Progressbar(self.container_bar_singlefile, orient="horizontal", length=100, mode="determinate", variable=self.singlefile_progress)
		self.progressbar_singlefile.pack(side=LEFT)
		self.label_info_singlefile = Label(self.container_bar_singlefile, textvariable=self.singlefile_progress_info)
		self.label_info_singlefile.pack(side=RIGHT)

		def increment_progress_bar(self, args, singlefile_progress, singlefile_progress_info):
			print("increment_progress_bar")
			print(args['total'])
			if args['desc'] == "OCR":
				print("OCR Running")
				percent = float(args['unit_scale']) * 100
				print(percent)
				precision = float(singlefile_progress.get()) + percent
				singlefile_progress_info.set("OCR Running")

				singlefile_progress.set(precision)
			elif args['desc'] == "Scanning contents":
				print("Scanning Contents")
				singlefile_progress_info.set("Scanning Contents")


			#self.singlefile_progress.set(float(self.singlefile_progress.get())+1)

		ocrmypdf_progressbar_singlefile.set_callback(increment_progress_bar, self.singlefile_progress, self.singlefile_progress_info)

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
				dynamic_widgets[k] = {}
				dynamic_widgets[k]["value"] = BooleanVar()
				dynamic_widgets[k]["widget"] = Checkbutton(myContainer2, text=k, variable=dynamic_widgets[k]["value"])
				dynamic_widgets[k]["widget"].pack()
				dynamic_widgets[k]["type"] = "bool"

				if self.ocrmypdfsettings.get(k) is True:
					dynamic_widgets[k]["value"].set(self.ocrmypdfsettings[k])


		for k, v in self.ocrmypdfapioptions.items():
				#dynamically create widgets here
			if v == "str" and k != "keywords" and k != "unpaper_args" and k != "pages":
				dynamic_widgets[k] = {}
				dynamic_widgets[k]["value"] = StringVar()
				dynamic_widgets[k]["widget"] = Entry(myContainer2, textvariable=dynamic_widgets[k]["value"])
				dynamic_widgets[k]["value"].set("")
				dynamic_widgets[k]["widget"].pack()
				dynamic_widgets[k]["type"] = "str"
				dynamic_widgets[k]["label"] = Label(myContainer2, text=k)
				dynamic_widgets[k]["label"].pack()
				if self.ocrmypdfsettings.get(k):
					dynamic_widgets[k]["value"].set(self.ocrmypdfsettings[k])

		savebutton = Button(myContainer2, text="Save Settings", command=lambda: self.save_settings(settings, dynamic_widgets) )
		savebutton.pack()

	def save_settings(self, w, dynamic_widgets):
		settings = {}
		for k, v in dynamic_widgets.items():
			try:
				settings[k] = v["value"].get()
			except:
				print("Error Creating settings Dict")
				messagebox.showerror(title="Error", message="Error creating settings dictionary.")
				break

		try:
			json.dump(settings, open("settings.ini", "w"))
			print("Saved")
		except:
			print("Error Saving to file.")
			messagebox.showerror(title="Error", message="Error saving settings to disk.")
		self.load_settings()
		#w.destroy()

	def load_settings(self):
		#Open Settings File
		if os.path.isfile(os.path.join(os.path.dirname(__file__), 'settings.ini')) == True:
			print("Settings found")
			with open(os.path.join(os.path.dirname(__file__), 'settings.ini')) as f:
				self.ocrmypdfsettings = json.load(f)
			print("Settings Loaded")

		else:
			print("Settings not found")
			pass

	def choose_batch_directory(self, myParent, dir_path):
		#Runs Pathpicker and sets path variable
		dir_path.set(askdirectory())
		#root.update_idletasks()
		print(dir_path.get())

	def choose_file(self, myParent, dir_path):
		#Runs Filepicker and sets path variable
		dir_path.set(askopenfilename(filetypes=[("PDF files", ".pdf")]))
		#self.update_idletasks()
		print(dir_path.get())



def run():
	root = Tk()
	root.title("ocrmypdfgui")
	ocrmypdfgui(root)
	root.mainloop()
