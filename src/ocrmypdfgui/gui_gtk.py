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
from pathlib import Path
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, GLib, GdkPixbuf


class MainWindow(Gtk.Window):
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
		self.start_ocr_button = Gtk.Button.new_with_label("Start OCR")
		self.start_ocr_button.connect("clicked", self.on_click_startocr)
		box.add(self.start_ocr_button)

		self.stop_ocr_button = Gtk.Button.new_with_label("Stop OCR")
		self.stop_ocr_button.connect("clicked", self.on_click_stopocr)
		box.add(self.stop_ocr_button)


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
		self.textview = Gtk.TextView()
		self.textview.set_size_request(1200, 600)
		scrolledwindow = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
		grid.attach(scrolledwindow, 1, 1, 3, 1)
		scrolledwindow.add(self.textview)
		self.textbuffer = self.textview.get_buffer()

	#Add Progress Bar Area
		self.label_currentfile = Gtk.Label(label="Idle")
		grid.attach(self.label_currentfile, 1, 2, 1, 1)
		self.progressbar = Gtk.ProgressBar()
		grid.attach(self.progressbar, 3, 2, 1, 1)

		self.add(grid)

	#Init Logic
		self.ocr = None
		self.dir_path = ""
		self.singlefile_progress = 0
		self.ocrmypdfsettings = {}
		self.load_settings()


		def update_label_singlefile_progress_info(self, args, singlefile_progress, singlefile_progress_info):
			singlefile_progress_info.set_text(str(args['desc']))

		ocrmypdf_progressbar_singlefile.set_callback(update_label_singlefile_progress_info, self.singlefile_progress, self.label_currentfile)

	def increment_progress_bar_batch(self, step):
		print("increment_progress_bar_batch to: " + str(step))
		self.progressbar.set_fraction(step)

	def about_application(self, button):
		#about page
		dialog = Gtk.AboutDialog()
		logo = GdkPixbuf.Pixbuf.new_from_file ("../../gui/ocrmypdfgui.png")
		authors = ["Alexander Langanke"]
		dialog.set_authors(authors)
		dialog.set_logo(logo)
		dialog.set_program_name("OCRmyPDFGui")
		dialog.set_website("https://github.com/alexanderlanganke/ocrmypdfgui")
		dialog.set_comments("I use James R. Barlow's OCRmyPDF heavily in my paperless Office and have created this Python Project as a GUI wrapper to run batch jobs on my filesystem. This is strictly a Hobby Project and is not 'official'. Feel free to use it if you like.")
		response = dialog.run()

	def settings(self, button):
		#Settings page
		settings_window = SettingsWindow(self)#self.ocrmypdfsettings, self.save_settings)
		settings_window.show_all()

	def load_settings(self):
		#Open Settings File
#		if os.path.isfile(os.path.join(os.path.dirname(__file__), 'settings.ini')) == True:
		if os.path.isfile(os.path.join(os.path.expanduser('~'), '.ocrmypdfgui', 'settings.ini')) == True:

			print("Settings found")
#			with open(os.path.join(os.path.dirname(__file__), 'settings.ini')) as f:
			with open(os.path.join(os.path.expanduser('~'), '.ocrmypdfgui', 'settings.ini')) as f:

				self.ocrmypdfsettings = json.load(f)

			#self.ocrmypdfapioptions_info = self.dict_to_string(self.ocrmypdfsettings)
			print("Settings Loaded")

		else:
			print("Settings not found")
			pass

	def save_settings(self):
		print("savefunction")
		print(self.ocrmypdfsettings)

		try:
#			json.dump(settings, open(os.path.join(os.path.dirname(__file__), 'settings.ini'), "w"))
			Path(os.path.join(os.path.expanduser('~'), '.ocrmypdfgui')).mkdir(parents=True, exist_ok=True)
			json.dump(self.ocrmypdfsettings, open(os.path.join(os.path.expanduser('~'), '.ocrmypdfgui', 'settings.ini'), "w"))

			print("Saved")
		except:
			print("Error Saving to file.")
			#self.on_error_clicked("Error Saving.", "Settings could not be saved to disk.")
		self.load_settings()

	def on_error_clicked(self, message, secondary_text):
		print("error")
		dialog = Gtk.MessageDialog(
			transient_for=self,
			flags=0,
			message_type=Gtk.MessageType.ERROR,
			buttons=Gtk.ButtonsType.CANCEL,
			text=message,
		)
		dialog.format_secondary_text(
			secondary_text
		)
		dialog.run()
		print("ERROR dialog closed")

		dialog.destroy()

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
		#self.start_ocr_button.hide()
		#self.stop_ocr_button.show()
		self.ocr = start_job(self.dir_path, self.increment_progress_bar_batch, self.print_to_textview, self.ocrmypdfsettings)

	def on_click_stopocr(self, button):
		print("stop ocr")
		#self.start_ocr_button.show()
		#self.stop_ocr_button.hide()
		#self.ocr.join()

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

class SettingsWindow(Gtk.Window):
	def __init__(self, main):#ocrmypdfsettings, save_settings):
		#Init Logic
		#self.ocrmypdfsettings = ocrmypdfsettings
		#self.save_settings = save_settings
		self.ocrmypdflanguages = get_languages()
		self.main = main
		#Build Window
		Gtk.Window.__init__(self, title="Settings")
		self.notebook = Gtk.Notebook()
		self.add(self.notebook)
		print(self.main.ocrmypdfsettings)

		#Page 1 - Options
		self.page1 = Gtk.Box()
		self.page1.set_border_width(10)
		grid_page1 = Gtk.Grid()

		#Rotate Pages
		label1_page1 = Gtk.Label(label="Rotate Pages")
		grid_page1.attach(label1_page1, 1, 1, 1, 1)
		self.switch1_page1 = Gtk.Switch()
		if(self.main.ocrmypdfsettings["rotate_pages"] == True):
			self.switch1_page1.set_active(True)
		else:
			self.switch1_page1.set_active(False)
		self.switch1_page1.connect("notify::active", self.save_state)
		grid_page1.attach(self.switch1_page1, 2, 1, 1, 1)

		#Remove Background
		label2_page1 = Gtk.Label(label="Remove Background")
		grid_page1.attach(label2_page1, 1, 2, 1, 1)
		self.switch2_page1 = Gtk.Switch()
		if(self.main.ocrmypdfsettings["remove_background"] == True):
			self.switch2_page1.set_active(True)
		else:
			self.switch2_page1.set_active(False)
		self.switch2_page1.connect("notify::active", self.save_state)
		grid_page1.attach(self.switch2_page1, 2, 2, 1, 1)

		#Deskew
		label3_page1 = Gtk.Label(label="Deskew")
		grid_page1.attach(label3_page1, 1, 3, 1, 1)
		self.switch3_page1 = Gtk.Switch()
		if(self.main.ocrmypdfsettings["deskew"] == True):
			self.switch3_page1.set_active(True)
		else:
			self.switch3_page1.set_active(False)
		self.switch3_page1.connect("notify::active", self.save_state)
		grid_page1.attach(self.switch3_page1, 2, 3, 1, 1)

		#Clean
		label4_page1 = Gtk.Label(label="Clean")
		grid_page1.attach(label4_page1, 1, 4, 1, 1)
		self.switch4_page1 = Gtk.Switch()
		if(self.main.ocrmypdfsettings["clean"] == True):
			self.switch4_page1.set_active(True)
		else:
			self.switch4_page1.set_active(False)
		self.switch4_page1.connect("notify::active", self.save_state)
		grid_page1.attach(self.switch4_page1, 2, 4, 1, 1)

		#Force OCR
		label5_page1 = Gtk.Label(label="Force OCR")
		grid_page1.attach(label5_page1, 1, 5, 1, 1)
		self.switch5_page1 = Gtk.Switch()
		if(self.main.ocrmypdfsettings["force_ocr"] == True):
			self.switch5_page1.set_active(True)
		else:
			self.switch5_page1.set_active(False)
		self.switch5_page1.connect("notify::active", self.save_state)
		grid_page1.attach(self.switch5_page1, 2, 5, 1, 1)

		#Skip Text
		label6_page1 = Gtk.Label(label="Skip Text")
		grid_page1.attach(label6_page1, 1, 6, 1, 1)
		self.switch6_page1 = Gtk.Switch()
		if(self.main.ocrmypdfsettings["skip_text"] == True):
			self.switch6_page1.set_active(True)
		else:
			self.switch6_page1.set_active(False)
		self.switch6_page1.connect("notify::active", self.save_state)
		grid_page1.attach(self.switch6_page1, 2, 6, 1, 1)


		self.page1.add(grid_page1)


		self.notebook.append_page(self.page1, Gtk.Label(label="Options"))#Add and Define Label of Page

		#Page 2 - Languages
		self.page2 = Gtk.Box()
		self.page2.set_border_width(10)
		grid_page2 = Gtk.Grid()

		#Button English
		self.button_eng = Gtk.ToggleButton(label="English")
		grid_page2.attach(self.button_eng, 1, 1, 1, 1)
		if("eng" in self.main.ocrmypdfsettings["language"]):
			self.button_eng.set_active(True)
		else:
			self.button_eng.set_active(False)
		self.button_eng.connect("notify::active", self.save_state)

		#Button German
		self.button_deu = Gtk.ToggleButton(label="German")
		grid_page2.attach(self.button_deu, 1, 2, 1, 1)
		if("deu" in self.main.ocrmypdfsettings["language"]):
			self.button_deu.set_active(True)
		else:
			self.button_deu.set_active(False)
		self.button_deu.connect("notify::active", self.save_state)

		print(self.ocrmypdflanguages)


		self.page2.add(grid_page2)
		self.notebook.append_page(self.page2, Gtk.Label(label="Languages"))#Add and Define Label of Page


	def save_state(self, switch, gparam):
		#save state of widgets to settings
		print("save state")
		#Switches
		self.main.ocrmypdfsettings['rotate_pages'] = self.switch1_page1.get_active()
		self.main.ocrmypdfsettings['remove_background'] = self.switch2_page1.get_active()
		self.main.ocrmypdfsettings['deskew'] = self.switch3_page1.get_active()
		self.main.ocrmypdfsettings['clean'] = self.switch4_page1.get_active()
		self.main.ocrmypdfsettings['force_ocr'] = self.switch5_page1.get_active()
		self.main.ocrmypdfsettings['skip_text'] = self.switch6_page1.get_active()

		#languages
		languages = []
		if(self.button_eng.get_active()):
			languages.append("eng")
		if(self.button_deu.get_active()):
			languages.append("deu")
		self.main.ocrmypdfsettings['language'] = languages

		print(self.main.ocrmypdfsettings)

		self.main.save_settings()

win = MainWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
win.stop_ocr_button.hide()
Gtk.main()
