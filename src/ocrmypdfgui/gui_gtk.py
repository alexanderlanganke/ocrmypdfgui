#!/usr/bin/env python3

from ocr import get_api_options
from ocr import start_job
from plugin_progressbar import ocrmypdf_progressbar_singlefile
#from ocrmypdfgui.ocr import start_job
#from ocrmypdfgui.ocr import get_api_options
#from ocrmypdfgui.plugin_progressbar import ocrmypdf_progressbar_singlefile
from pytesseract import get_languages
import json
import os
import sys
import string
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, GLib


class HeaderBarWindow(Gtk.Window):
	def __init__(self):
	#Build Window
		super().__init__(title="OCRmyPDFGui")
		self.set_border_width(10)
		self.set_default_size(1200, 675)


		hb = Gtk.HeaderBar()
		hb.set_show_close_button(True)
		hb.props.title = "OCRmyPDFGui"
		self.set_titlebar(hb)

	#Create left box
		box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		Gtk.StyleContext.add_class(box.get_style_context(), "linked")

	#Add Select File Button
		#button = Gtk.Button.new_from_icon_name("pan-end-symbolic", Gtk.IconSize.MENU)
		button = Gtk.Button.new_with_label("Select PDF")
		button.connect("clicked", self.on_click_selectpdf)
		box.add(button)

	#Add Select Folder Button
	   # button = Gtk.Button.new_from_icon_name("pan-end-symbolic", Gtk.IconSize.MENU)
		button = Gtk.Button.new_with_label("Select Folder")
		button.connect("clicked", self.on_click_selectfolder)
		box.add(button)

	#Add left box to start of Headerbar
		hb.pack_start(box)

	#Create right box
		box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		Gtk.StyleContext.add_class(box.get_style_context(), "linked")

	#Add Start OCR Button
		button = Gtk.Button.new_with_label("Start OCR")
		button.connect("clicked", self.on_click_startocr)
		box.add(button)

	#Add Hamburger Menu
		settings_selection = Gtk.ModelButton(label="Settings")
		settings_selection.connect("clicked", self.settings)
		about_selection = Gtk.ModelButton(label="About")
		about_selection.connect("clicked", self.about_application)

		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin=10, spacing=10)
		vbox.add(settings_selection)
		vbox.add(about_selection)
		vbox.show_all()

		self.popover = Gtk.Popover()
		self.popover.add(vbox)
		self.popover.set_position(Gtk.PositionType.BOTTOM)

		menu_button = Gtk.MenuButton(popover=self.popover)
		menu_icon = Gtk.Image.new_from_icon_name("open-menu-symbolic", Gtk.IconSize.MENU)
		menu_icon.show()
		menu_button.add(menu_icon)
		menu_button.show()
		box.add(menu_button)
		hb.pack_end(box)

	#Add Output Area
		grid = Gtk.Grid()
		#scrolledwindow.add(grid)
		self.textview = Gtk.TextView()
		self.textview.set_size_request(1200, 600)
		scrolledwindow = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
		#grid.add(scrolledwindow)
		grid.attach(scrolledwindow, 1, 1, 3, 1)
		scrolledwindow.add(self.textview)
		#grid.attach(self.textview, 1, 1, 3, 1)
		self.textbuffer = self.textview.get_buffer()

	#Add Progress Bar Area
		self.label_currentfile = Gtk.Label(label="Test")
		#grid.add(self.label_currentfile)
		grid.attach(self.label_currentfile, 1, 2, 1, 1)
		self.progressbar = Gtk.ProgressBar()
		#grid.add(self.progressbar)
		grid.attach(self.progressbar, 3, 2, 1, 1)

		self.add(grid)
		#scrolledwindow.add(grid)

	#Init Logic
		self.dir_path = ""
		self.currentfile = ""
		self.batch_progress = ""
		self.singlefile_progress = ""
		self.singlefile_progress_info = ""
		self.ocrmypdfsettings = {}
		self.ocrmypdfapioptions = get_api_options()
		self.ocrmypdfapioptions_info = ""
		self.load_settings()

	def about_application(self, button):
		#about page
		dialog = Gtk.AboutDialog ()
		authors = ["Alexander Langanke"]
		dialog.set_authors(authors)
		dialog.set_program_name("OCRmyPDFGui")
		dialog.set_website("https://github.com/alexanderlanganke/ocrmypdfgui")
		dialog.set_comments("I use James R. Barlow's OCRmyPDF heavily in my paperless Office and have created this Python Project as a GUI wrapper to run batch jobs on my filesystem. This is strictly a Hobby Project and is not 'official'. Feel free to use it if you like.")
		response = dialog.run()

	def increment_progress_bar(self, args, singlefile_progress, singlefile_progress_info):
		print("increment_progress_bar")
		print(args['total'])
		if args['desc'] == "OCR":
			print("OCR Running")
			percent = float(args['unit_scale']) * 700
			print(percent)
			precision = float(self.singlefile_progress) + percent
			#singlefile_progress_info.set("OCR Running")

			self.singlefile_progress = precision
		elif args['desc'] == "Scanning contents":
			print("Scanning Contents")
			#singlefile_progress_info.set("Scanning Contents")

		ocrmypdf_progressbar_singlefile.set_callback(increment_progress_bar, self.singlefile_progress, self.singlefile_progress_info)

	def settings(self, button):
		#Settings page
		print("test")

	def load_settings(self):
		#Open Settings File
#		if os.path.isfile(os.path.join(os.path.dirname(__file__), 'settings.ini')) == True:
		if os.path.isfile(os.path.join(os.path.expanduser('~'), '.ocrmypdfgui', 'settings.ini')) == True:

			print("Settings found")
#			with open(os.path.join(os.path.dirname(__file__), 'settings.ini')) as f:
			with open(os.path.join(os.path.expanduser('~'), '.ocrmypdfgui', 'settings.ini')) as f:

				self.ocrmypdfsettings = json.load(f)

			self.ocrmypdfapioptions_info = self.dict_to_string(self.ocrmypdfsettings)
			print("Settings Loaded")

		else:
			print("Settings not found")
			pass

	def on_click_selectpdf(self, button):
		#What to do on click
		dialog = Gtk.FileChooserDialog(
			title="Please choose a file", parent=self, action=Gtk.FileChooserAction.OPEN
		)
		dialog.add_buttons(
			Gtk.STOCK_CANCEL,
			Gtk.ResponseType.CANCEL,
			Gtk.STOCK_OPEN,
			Gtk.ResponseType.OK,
		)
		filter_pdf = Gtk.FileFilter()
		filter_pdf.set_name("PDF files")
		filter_pdf.add_mime_type("application/pdf")
		dialog.add_filter(filter_pdf)

		response = dialog.run()
		if response == Gtk.ResponseType.OK:
			text = dialog.get_filename()
			self.dir_path = text
		elif response == Gtk.ResponseType.CANCEL:
			print("Cancel clicked")
		dialog.destroy()


	def on_click_selectfolder(self, button):
		#What to do on click
		dialog = Gtk.FileChooserDialog(
			title="Please choose a folder", parent=self, action=Gtk.FileChooserAction.SELECT_FOLDER
		)
		dialog.add_buttons(
			Gtk.STOCK_CANCEL,
			Gtk.ResponseType.CANCEL,
			Gtk.STOCK_OPEN,
			Gtk.ResponseType.OK,
		)

		response = dialog.run()
		if response == Gtk.ResponseType.OK:
			text = dialog.get_filename()
			self.dir_path = text

		elif response == Gtk.ResponseType.CANCEL:
			print("Cancel clicked")
		dialog.destroy()

	def on_click_startocr(self, button):
		#What to do on click
		start_job(self.dir_path, self.currentfile, self.batch_progress, self.singlefile_progress, self.print_to_textview, self.ocrmypdfsettings)


	def on_click_menu(self, button):
		#What to do on click
		text = '"Click me4" button was clicked'
		self.print_to_textview(text)

	def print_to_textview(self, text):
		end_iter = self.textbuffer.get_end_iter()
		self.textbuffer.insert(end_iter, text)
		end_iter = self.textbuffer.get_end_iter()
		self.textview.scroll_to_iter(end_iter, 0, 0, 0, 0)

	def clear_textview(self):
	   #empty textview buffer
	   self.textbuffer.set_text("")

	def dict_to_string(self, dict):
		string = ""
		for key, value in dict.items():
			string = string + key + "=" + str(value) + "; "
		return string

win = HeaderBarWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
