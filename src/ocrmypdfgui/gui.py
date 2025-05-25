#!/usr/bin/env python3

from ocrmypdfgui.ocr import start_job, stop_event
from ocrmypdfgui.ocr import get_api_options
from ocrmypdfgui.plugin_progressbar import ocrmypdf_progressbar_singlefile
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
		button = Gtk.Button.new_with_label("Select File")
		button.connect("clicked", self.on_click_select_file)
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
		self.ocrmypdfsettings = {}
		self.load_settings()
		self.start_ocr_button.set_sensitive(True)
		self.stop_ocr_button.set_sensitive(False)

		ocrmypdf_progressbar_singlefile.set_callback(self.update_single_file_progress_display)

	def update_single_file_progress_display(self, description, progress_fraction):
		if description: # Description might be None initially from plugin
			self.label_currentfile.set_text(str(description))
		self.progressbar.set_fraction(float(progress_fraction))

	def increment_progress_bar_batch(self, step):
		# This progressbar is for the overall batch progress,
		# not for the single file progress which is now handled by update_single_file_progress_display
		self.progressbar.set_fraction(step)


	def ocr_job_finished_or_stopped(self):
		self.start_ocr_button.set_sensitive(True)
		self.stop_ocr_button.set_sensitive(False)

	def about_application(self, button):
		#about page
		dialog = Gtk.AboutDialog()
		authors = ["Alexander Langanke"]
		dialog.set_authors(authors)
		dialog.set_program_name("OCRmyPDFGui")
		dialog.set_website("https://github.com/alexanderlanganke/ocrmypdfgui")
		dialog.set_comments("I use James R. Barlow's OCRmyPDF heavily in my paperless Office and have created this Python Project as a GUI wrapper to run batch jobs on my filesystem. This is strictly a Hobby Project and is not 'official'. Feel free to use it if you like.")

		snap_dir = os.getenv("SNAP")
		if snap_dir:
			icon_path = os.path.join(snap_dir, "gui/ocrmypdfgui.png")
		else:
			# Fallback for running outside snap (e.g., development)
			# Assumes the script is in src/ocrmypdfgui, so gui/ is ../../gui/
			icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "gui", "ocrmypdfgui.png")

		if os.path.exists(icon_path):
			try:
				logo = GdkPixbuf.Pixbuf.new_from_file(icon_path)
				dialog.set_logo(logo)
			except GLib.Error as e: # More specific exception for GdkPixbuf loading errors
				print(f"Warning: Could not load icon at {icon_path}: {e}")
		else:
			print(f"Warning: Icon not found at {icon_path}")
		
		response = dialog.run()

	def settings(self, button):
		#Settings page
		settings_window = SettingsWindow(self)#self.ocrmypdfsettings, self.save_settings)
		settings_window.show_all()

	def load_settings(self):
		default_settings = {
			"use_threads": False, "rotate_pages": False, "remove_background": False,
			"deskew": False, "clean": False, "clean_final": False,
			"remove_vectors": False, "threshold": False, "force_ocr": False,
			"skip_text": False, "redo_ocr": False, "jbig2_lossy": False,
			"keep_temporary_files": False, "progress_bar": False,
			"title": "", "author": "", "subject": "", "language": [],
			"output_mode": "pdf", "new_archive_on_sidecar": True
		}
		settings_file_path = os.path.join(os.path.expanduser('~'), '.ocrmypdfgui', 'settings.ini')

		if os.path.exists(settings_file_path):
			print("Settings found")
			try:
				with open(settings_file_path, 'r') as f:
					loaded_settings = json.load(f)
				print("Settings Loaded")
				# Merge loaded settings with defaults. Loaded settings take precedence.
				self.ocrmypdfsettings = {**default_settings, **loaded_settings}
			except (json.JSONDecodeError, IOError, OSError) as e:
				print(f"Error loading settings file: {e}. Using default settings.")
				self.ocrmypdfsettings = default_settings
		else:
			print("Settings not found")
			self.ocrmypdfsettings = default_settings

		# Ensure 'language' is always a list
		if not isinstance(self.ocrmypdfsettings.get("language"), list):
			self.ocrmypdfsettings["language"] = []

	def save_settings(self):
		settings_dir = os.path.join(os.path.expanduser('~'), '.ocrmypdfgui')
		settings_path = os.path.join(settings_dir, 'settings.ini')
		try:
			Path(settings_dir).mkdir(parents=True, exist_ok=True)
			with open(settings_path, "w") as f:
				json.dump(self.ocrmypdfsettings, f, indent=4) # Added indent for readability
			print("Saved settings to:", settings_path)
			# self.load_settings() # Removed as per instruction - self.ocrmypdfsettings is already up-to-date.

		except (IOError, OSError) as e:
			print(f"Error Saving to file: {e}") 
			self.on_error_clicked("Error Saving Settings",
								  f"Could not save settings to disk. Please check permissions or disk space.\nDetails: {e}")
		except json.JSONDecodeError as e: # Though dump is less likely to cause this than load
			print(f"Error encoding settings to JSON: {e}")
			self.on_error_clicked("Error Saving Settings",
								  f"Could not encode settings data.\nDetails: {e}")
		except Exception as e: 
			print(f"An unexpected error occurred while saving settings: {e}")
			self.on_error_clicked("Error Saving Settings",
								  f"An unexpected error occurred.\nDetails: {e}")
		# self.load_settings() # Removed from here, was unconditional previously

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

	def on_click_select_file(self, button):
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

		filter_all_supported = Gtk.FileFilter()
		filter_all_supported.set_name("All supported files")
		filter_all_supported.add_mime_type("application/pdf")
		filter_all_supported.add_pattern("*.pdf")
		filter_all_supported.add_pattern("*.cbz")
		filter_all_supported.add_pattern("*.cbr")
		dialog.add_filter(filter_all_supported)

		filter_pdf = Gtk.FileFilter()
		filter_pdf.set_name("PDF files")
		filter_pdf.add_mime_type("application/pdf")
		filter_pdf.add_pattern("*.pdf")
		dialog.add_filter(filter_pdf)

		filter_comic = Gtk.FileFilter()
		filter_comic.set_name("Comic Book Archive files")
		filter_comic.add_pattern("*.cbz")
		filter_comic.add_pattern("*.cbr")
		dialog.add_filter(filter_comic)

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
		self.start_ocr_button.set_sensitive(False)
		self.stop_ocr_button.set_sensitive(True)
		self.ocr = start_job(self.dir_path, self.increment_progress_bar_batch, self.print_to_textview, self.ocrmypdfsettings, self.ocr_job_finished_or_stopped)

	def on_click_stopocr(self, button):
		print("stop ocr")
		stop_event.set()
		self.start_ocr_button.set_sensitive(True)
		self.stop_ocr_button.set_sensitive(False)
		#self.ocr.join() # Do not join, it blocks the GUI

	def on_click_menu(self, button):
		#What to do on click
		text = '"Click me4" button was clicked'
		self.print_to_textview(text)

	def print_to_textview(self, text, type):
		end_iter = self.textbuffer.get_end_iter()

		if (type == "success"):
			self.textbuffer.insert_markup(end_iter, "<span color='green'>"+text+"</span>", -1)
		elif (type == "error"):
			self.textbuffer.insert_markup(end_iter, "<span color='red'>"+text+"</span>", -1)
		elif (type == "skip"):
			self.textbuffer.insert_markup(end_iter, "<span color='blue'>"+text+"</span>", -1)
		elif (type == "default"):
			self.textbuffer.insert_markup(end_iter, "<span color='black'>"+text+"</span>", -1)

		else:
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
		self.set_border_width(10)
		self.set_default_size(900, 550)
		self.notebook = Gtk.Notebook()
		self.add(self.notebook)

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
		self.switch1_page1.connect("notify::active", self.save_state, label1_page1)
		grid_page1.attach(self.switch1_page1, 2, 1, 1, 1)

		#Remove Background
		label2_page1 = Gtk.Label(label="Remove Background")
		grid_page1.attach(label2_page1, 1, 2, 1, 1)
		self.switch2_page1 = Gtk.Switch()
		if(self.main.ocrmypdfsettings["remove_background"] == True):
			self.switch2_page1.set_active(True)
		else:
			self.switch2_page1.set_active(False)
		self.switch2_page1.connect("notify::active", self.save_state, label2_page1)
		grid_page1.attach(self.switch2_page1, 2, 2, 1, 1)

		#Deskew
		label3_page1 = Gtk.Label(label="Deskew")
		grid_page1.attach(label3_page1, 1, 3, 1, 1)
		self.switch3_page1 = Gtk.Switch()
		if(self.main.ocrmypdfsettings["deskew"] == True):
			self.switch3_page1.set_active(True)
		else:
			self.switch3_page1.set_active(False)
		self.switch3_page1.connect("notify::active", self.save_state, label3_page1)
		grid_page1.attach(self.switch3_page1, 2, 3, 1, 1)

		#Clean
		label4_page1 = Gtk.Label(label="Clean")
		grid_page1.attach(label4_page1, 1, 4, 1, 1)
		self.switch4_page1 = Gtk.Switch()
		if(self.main.ocrmypdfsettings["clean"] == True):
			self.switch4_page1.set_active(True)
		else:
			self.switch4_page1.set_active(False)
		self.switch4_page1.connect("notify::active", self.save_state, label4_page1)
		grid_page1.attach(self.switch4_page1, 2, 4, 1, 1)

		#Force OCR
		label5_page1 = Gtk.Label(label="Force OCR")
		grid_page1.attach(label5_page1, 1, 5, 1, 1)
		self.switch5_page1 = Gtk.Switch()
		if(self.main.ocrmypdfsettings["force_ocr"] == True):
			self.switch5_page1.set_active(True)
		else:
			self.switch5_page1.set_active(False)
		self.switch5_page1.connect("notify::active", self.save_state, label5_page1)
		grid_page1.attach(self.switch5_page1, 2, 5, 1, 1)

		#Skip Text
		label6_page1 = Gtk.Label(label="Skip Text")
		grid_page1.attach(label6_page1, 1, 6, 1, 1)
		self.switch6_page1 = Gtk.Switch()
		if(self.main.ocrmypdfsettings["skip_text"] == True):
			self.switch6_page1.set_active(True)
		else:
			self.switch6_page1.set_active(False)
		self.switch6_page1.connect("notify::active", self.save_state, label6_page1)
		grid_page1.attach(self.switch6_page1, 2, 6, 1, 1)

		# Separator for Output Options
		separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL, margin_top=10, margin_bottom=10)
		grid_page1.attach(separator, 1, 7, 2, 1) # Spanning 2 columns

		# Output Mode Label
		label_output_mode = Gtk.Label(label="Output Mode:")
		label_output_mode.set_halign(Gtk.Align.START)
		grid_page1.attach(label_output_mode, 1, 8, 1, 1)

		# Output Mode Radio Buttons Box
		radio_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
		self.radio_pdf = Gtk.RadioButton.new_with_label(None, "Create Searchable PDF")
		self.radio_pdf.connect("toggled", self.save_state_output_mode)
		radio_box.add(self.radio_pdf)

		self.radio_sidecar = Gtk.RadioButton.new_with_label_from_widget(self.radio_pdf, "Add Sidecar TXT to Archive (Converts CBR to CBZ)")
		self.radio_sidecar.connect("toggled", self.save_state_output_mode)
		radio_box.add(self.radio_sidecar)
		
		grid_page1.attach(radio_box, 2, 8, 1, 1)

		# New Archive Checkbox
		self.check_new_archive = Gtk.CheckButton(label="Create new archive for sidecar (uncheck to modify original)")
		self.check_new_archive.connect("toggled", self.save_state_new_archive_checkbox)
		grid_page1.attach(self.check_new_archive, 2, 9, 1, 1) # Placed below radio buttons

		# Set initial states for output mode and checkbox
		if self.main.ocrmypdfsettings.get("output_mode", "pdf") == "sidecar_txt":
			self.radio_sidecar.set_active(True)
			self.check_new_archive.set_sensitive(True)
		else:
			self.radio_pdf.set_active(True)
			self.check_new_archive.set_sensitive(False)
		
		self.check_new_archive.set_active(self.main.ocrmypdfsettings.get("new_archive_on_sidecar", True))


		self.page1.add(grid_page1)


		self.notebook.append_page(self.page1, Gtk.Label(label="Options"))#Add and Define Label of Page

		#Page 2 - Languages
		self.page2 = Gtk.Box()
		self.page2.set_border_width(10)
		self.scrolledwindow = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
		self.page2.add(self.scrolledwindow)
		grid_page2 = Gtk.Grid()

		#Write Code to create a dynamic grid which will adapt to the number of installed languages
		#iterate through all languages and create new row every x items
		#create a dict to hold buttons with the label representing the language "deu", "eng" etc.
		#adapt save_state() to read these dynamic buttons into languages[]
		row = 0
		column = 0
		x=0
		i=0
		if (len(self.ocrmypdflanguages)<10):
			x = len(self.ocrmypdflanguages)
		else:
			x = 10
		while (i < len(self.ocrmypdflanguages)):
			while (column < x):
				if(i==len(self.ocrmypdflanguages)):
					break
				else:
					self.button = Gtk.ToggleButton(label=self.ocrmypdflanguages[i])
					grid_page2.attach(self.button, column, row, 1, 1)
					if(self.ocrmypdflanguages[i] in self.main.ocrmypdfsettings["language"]):
						self.button.set_active(True)
						self.button.connect("notify::active", self.save_state, self.ocrmypdflanguages[i])
					else:
						self.button.set_active(False)
						self.button.connect("notify::active", self.save_state, self.ocrmypdflanguages[i])
				column+=1
				i+=1
			row+=1
			column = 0

		self.scrolledwindow.add(grid_page2)
		self.notebook.append_page(self.page2, Gtk.Label(label="Languages"))#Add and Define Label of Page


	def save_state(self, widget, gparam, name):
		#save state of widgets to settings
		#run different code depending on what type of widget activates this function
		#Switches
		if(isinstance(widget, Gtk.Switch)):
			self.main.ocrmypdfsettings['rotate_pages'] = self.switch1_page1.get_active()
			self.main.ocrmypdfsettings['remove_background'] = self.switch2_page1.get_active()
			self.main.ocrmypdfsettings['deskew'] = self.switch3_page1.get_active()
			self.main.ocrmypdfsettings['clean'] = self.switch4_page1.get_active()
			self.main.ocrmypdfsettings['force_ocr'] = self.switch5_page1.get_active()
			self.main.ocrmypdfsettings['skip_text'] = self.switch6_page1.get_active()
		#languages
		elif(isinstance(widget, Gtk.ToggleButton)):
			languages = self.main.ocrmypdfsettings['language']
			if(widget.get_active() == True):
				languages.append(name)
			elif(widget.get_active() == False):
				languages.remove(name)
			self.main.ocrmypdfsettings['language'] = languages
		else:
			print("Error calling save_state function")

		self.main.save_settings()

	def save_state_output_mode(self, widget):
		if widget.get_active(): # Process only the active radio button
			if self.radio_pdf.get_active():
				self.main.ocrmypdfsettings["output_mode"] = "pdf"
				self.check_new_archive.set_sensitive(False)
				print("Set output_mode to pdf")
			elif self.radio_sidecar.get_active():
				self.main.ocrmypdfsettings["output_mode"] = "sidecar_txt"
				self.check_new_archive.set_sensitive(True)
				print("Set output_mode to sidecar_txt")
			self.main.save_settings()

	def save_state_new_archive_checkbox(self, widget):
		self.main.ocrmypdfsettings["new_archive_on_sidecar"] = widget.get_active()
		print(f"Set new_archive_on_sidecar to {widget.get_active()}")
		self.main.save_settings()


def run():
	win = MainWindow()
	win.connect("destroy", Gtk.main_quit)
	win.show_all()
	Gtk.main()
