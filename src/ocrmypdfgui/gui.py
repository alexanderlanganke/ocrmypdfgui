#!/usr/bin/env python3


import os
import sys
import string
from ocrmypdfgui.ocr import start_job
from ocrmypdfgui.ocr import get_api_options
from ocrmypdfgui.plugin_progressbar import ocrmypdf_progressbar_singlefile
from pytesseract import get_languages
import json
from tkinter import *
from tkinter.filedialog import askdirectory
from tkinter.filedialog import askopenfilename
from tkinter.ttk import *
from tkinter import messagebox

class ocrmypdfgui:
	def __init__(self, myParent):
		#init variables
#		self.script_dir = os.path.dirname(os.path.realpath(__file__))
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
		self.ocrmypdfapioptions_info = StringVar()
		self.load_settings()
		self.ocrmypdfapioptions = get_api_options()

		#Get installed tesseract languages on System using pytesseract get_languages() method
		self.ocrmypdflanguages = list()
		for i in get_languages():
			if i != "osd":
				self.ocrmypdflanguages.append(i)


		#BUILD GUI MAIN WINDOW
		window_width = 1000
		window_height = 550

		# get the screen dimension
		screen_width = myParent.winfo_screenwidth()
		screen_height = myParent.winfo_screenheight()

		# find the center point
		center_x = int(screen_width/2 - window_width / 2)
		center_y = int(screen_height/2 - window_height / 2)

		# set the position of the window to the center of the screen
		myParent.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
		myParent.resizable(True, False)
		myParent.minsize(window_width, window_height)
		#myParent.geometry("2000x1000+50+50")
		#MENUBAR
		menubar = Menu(myParent)
		filemenu = Menu(menubar, tearoff=0)
		filemenu.add_command(label="Settings", command=lambda: self.open_settings(myParent))
		filemenu.add_separator()
		filemenu.add_command(label="Exit", command=myParent.quit)
		menubar.add_cascade(label="File", menu=filemenu)

		myParent.config(menu=menubar)

		#WINDOW
		self.container_main = Frame(myParent)
		self.container_main.pack(fill="both")
		#Topcontainer which contains the Output Textarea
		self.container_textarea = Frame(self.container_main)
		self.container_textarea.pack(fill="both")
		self.outputarea = Text(self.container_textarea)
		self.outputarea.pack(fill="both")

		#Second container which contains Information
		self.container_informationarea = Frame(self.container_main)
		self.container_informationarea.pack(fill="both")

		self.dir_path_label = Label(self.container_informationarea, textvariable=self.dir_path)
		self.dir_path_label.pack(side=TOP)
		self.label_currentfile = Label(self.container_informationarea, textvariable=self.currentfile, wraplength=800)
		self.label_currentfile.pack(side=TOP)
		#self.label_ocroptions = Label(self.container_informationarea, textvariable=self.ocrmypdfapioptions_info, wraplength=1500)
		#self.label_ocroptions.pack(side=TOP)

		#Third container which contains the Buttons
		self.container_buttons = Frame(self.container_main)
		self.container_buttons.pack()

		#Choose Path
		self.button1 = Button(self.container_buttons, text="Choose Batch OCR Directory", command=lambda: self.choose_batch_directory(self, self.dir_path) )
		self.button1.pack(side=LEFT)

		#Choose File
		self.button2 = Button(self.container_buttons, text="Choose Single File", command=lambda: self.choose_file(self, self.dir_path) )
		self.button2.pack(side=LEFT)

		#Start OCR
		self.button3 = Button(self.container_buttons, text="Start OCR Job", command=lambda: start_job(self.dir_path.get(), self.currentfile, self.batch_progress, self.singlefile_progress, self.outputarea, self.ocrmypdfsettings) )
		self.button3.pack(side=LEFT)



		#Fourth container for progress information
		self.container_progress = Frame(self.container_main, height=200)
		self.container_progress.pack(side=BOTTOM, fill='x')

		self.container_progress_top = Frame(self.container_progress)
		self.container_progress_top.pack(side=TOP, fill='x')
		self.container_progress_top_bar = Frame(self.container_progress_top)
		self.container_progress_top_bar.pack(side=LEFT)
		self.container_progress_top_information = Frame(self.container_progress_top)
		self.container_progress_top_information.pack(side=RIGHT)

		self.progressbar_singlefile = Progressbar(self.container_progress_top_bar, orient="horizontal", length=700, mode="determinate", variable=self.singlefile_progress)
		self.progressbar_singlefile.pack(side=LEFT)
		self.label_info_singlefile = Label(self.container_progress_top_information, textvariable=self.singlefile_progress_info)
		self.label_info_singlefile.pack(side=RIGHT)

		self.container_progress_bottom = Frame(self.container_progress)
		self.container_progress_bottom.pack(side=BOTTOM, fill='x')
		self.container_progress_bottom_bar = Frame(self.container_progress_bottom)
		self.container_progress_bottom_bar.pack(side=LEFT)
		self.container_progress_bottom_information = Frame(self.container_progress_bottom)
		self.container_progress_bottom_information.pack(side=RIGHT)

		self.progressbar_batch = Progressbar(self.container_progress_bottom_bar, orient="horizontal", length=700, mode="determinate", variable=self.batch_progress)
		self.progressbar_batch.pack(side=LEFT)
		self.label_info_batch = Label(self.container_progress_bottom_information, textvariable=self.batch_progress)
		self.label_info_batch.pack(side=LEFT)
		self.label_info_batch_percent= Label(self.container_progress_bottom_information, text="%")
		self.label_info_batch_percent.pack(side=RIGHT)




		def increment_progress_bar(self, args, singlefile_progress, singlefile_progress_info):
			print("increment_progress_bar")
			print(args['total'])
			if args['desc'] == "OCR":
				print("OCR Running")
				percent = float(args['unit_scale']) * 700
				print(percent)
				precision = float(singlefile_progress.get()) + percent
				singlefile_progress_info.set("OCR Running")

				singlefile_progress.set(precision)
			elif args['desc'] == "Scanning contents":
				print("Scanning Contents")
				singlefile_progress_info.set("Scanning Contents")

		ocrmypdf_progressbar_singlefile.set_callback(increment_progress_bar, self.singlefile_progress, self.singlefile_progress_info)

	def open_settings(self, myParent):
		settings=Toplevel(myParent) # Child window
		#settings.geometry("400x500")  # Size of the window
		settings.title("Settings")
		myContainer2 = Frame(settings)
		myContainer2.pack(fill=BOTH)

		container_top = Frame(myContainer2)
		container_top.pack(side=TOP, fill=BOTH)
		container_bottom = Frame(myContainer2)
		container_bottom.pack(side=BOTTOM, fill=BOTH)

		container_textbox = Frame(container_top)
		container_textbox.pack(side=LEFT, fill="x")

		container_checkobx = Frame(container_top)
		container_checkobx.pack(side=RIGHT, fill="x")



		dynamic_widgets = {}
		#print(self.ocrmypdfapioptions)
		for k, v in self.ocrmypdfapioptions.items():
			#dynamically create widgets here
			if v == "bool":
				dynamic_widgets[k] = {}
				dynamic_widgets[k]["value"] = BooleanVar()
				dynamic_widgets[k]["widget"] = Checkbutton(container_checkobx, text=k, variable=dynamic_widgets[k]["value"])
				dynamic_widgets[k]["widget"].pack()
				dynamic_widgets[k]["type"] = "bool"

				if self.ocrmypdfsettings.get(k) is True:
					dynamic_widgets[k]["value"].set(self.ocrmypdfsettings[k])


		for k, v in self.ocrmypdfapioptions.items():
				#dynamically create widgets here
			if v == "str" and k != "keywords" and k != "unpaper_args" and k != "pages":
				dynamic_widgets[k] = {}
				dynamic_widgets[k]["value"] = StringVar()
				dynamic_widgets[k]["widget"] = Entry(container_textbox, textvariable=dynamic_widgets[k]["value"])
				dynamic_widgets[k]["value"].set("")
				dynamic_widgets[k]["widget"].pack()
				dynamic_widgets[k]["type"] = "str"
				dynamic_widgets[k]["label"] = Label(container_textbox, text=k)
				dynamic_widgets[k]["label"].pack()
				if self.ocrmypdfsettings.get(k):
					dynamic_widgets[k]["value"].set(self.ocrmypdfsettings[k])

		for k, v in self.ocrmypdfapioptions.items():
				#dynamically create widgets here
			if v == "typing.Iterable[str]" and k=="language":
				dynamic_widgets[k] = {}

				listbox = Listbox(container_textbox, selectmode=MULTIPLE, width=20, height=10)
				count=0
				activated = list()
				for i in self.ocrmypdflanguages:
					listbox.insert(count, i)
					if self.ocrmypdfsettings.get(k):
						#If settings are available -> read the language part.
						for a in self.ocrmypdfsettings["language"]:
							if i == a:
								#if current language we are adding to the listbox is the settings
								# -> select it after creating the lixtbox
								print(i)
								print(count)
								activated.append(count)
						for index in activated:
							listbox.selection_set(index)
					count+=1
				listbox.pack()
				dynamic_widgets[k]["value"] = listbox
				dynamic_widgets[k]["type"] = "list"
				dynamic_widgets[k]["label"] = Label(container_textbox, text=k)
				dynamic_widgets[k]["label"].pack()

		savebutton = Button(container_bottom, text="Save Settings", command=lambda: self.save_settings(settings, dynamic_widgets) )
		savebutton.pack(fill=BOTH)

	def save_settings(self, w, dynamic_widgets):
		settings = {}
		#print(dynamic_widgets)
		for k, v in dynamic_widgets.items():
			try:
				if(v["type"] == "list"):
					settings[k] = [v["value"].get(i) for i in v["value"].curselection()]

				else:
					settings[k] = v["value"].get()
			except:
				print("Error Creating settings Dict")
				messagebox.showerror(title="Error", message="Error creating settings dictionary.")
				break

		try:
#			json.dump(settings, open(os.path.join(os.path.dirname(__file__), 'settings.ini'), "w"))
			json.dump(settings, open(os.path.join(os.path.expanduser('~'), '/.ocrmypdfgui/settings.ini'), "w"))

			print("Saved")
		except:
			print("Error Saving to file.")
			messagebox.showerror(title="Error", message="Error saving settings to disk.")
		self.load_settings()

	def load_settings(self):
		#Open Settings File
#		if os.path.isfile(os.path.join(os.path.dirname(__file__), 'settings.ini')) == True:
		if os.path.isfile(os.path.join(os.path.expanduser('~'), '/.ocrmypdfgui/settings.ini'))) == True:

			print("Settings found")
#			with open(os.path.join(os.path.dirname(__file__), 'settings.ini')) as f:
			with open(os.path.join(os.path.expanduser('~'), '/.ocrmypdfgui/settings.ini')) as f:

				self.ocrmypdfsettings = json.load(f)

			self.ocrmypdfapioptions_info.set(self.dict_to_string(self.ocrmypdfsettings))
			print("Settings Loaded")

		else:
			print("Settings not found")
			pass


	def dict_to_string(self, dict):
		string = ""
		for key, value in dict.items():
			string = string + key + "=" + str(value) + "; "
		return string

	def choose_batch_directory(self, myParent, dir_path):
		#Runs Pathpicker and sets path variable
		dir_path.set(askdirectory(initialdir='~', title='Select Directory',))

	def choose_file(self, myParent, dir_path):
		#Runs Filepicker and sets path variable
		dir_path.set(askopenfilename(initialdir='~', title='Select File', filetypes=[("PDF files", ".pdf")]))



def run():
	root = Tk()
	root.title("ocrmypdfgui")
	ocrmypdfgui(root)
	root.mainloop()
