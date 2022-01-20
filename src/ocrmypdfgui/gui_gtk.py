#!/usr/bin/env python3
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio


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
		self.box = Gtk.Box()
		self.add(self.box)
		self.textview = Gtk.TextView()
		self.box.pack_start(self.textview, True, True, 0)
		self.textbuffer = self.textview.get_buffer()

	#Init Logic


	def about_application(self, button):
		#about page
		dialog = Gtk.AboutDialog ()
		#"program-name", "OCRmyPDFGui",
		#"title", "About OCRmyPDFGui",
		#"authors", "Alexander Langanke",
		#"version", "1.0",
		#"website", "https://github.com/alexanderlanganke/ocrmypdfgui"
		#)
		authors = ["Alexander Langanke"]
		dialog.set_authors(authors)
		dialog.set_program_name("OCRmyPDFGui")
		dialog.set_website("https://github.com/alexanderlanganke/ocrmypdfgui")
		dialog.set_comments("I use James R. Barlow's OCRmyPDF heavily in my paperless Office and have created this Python Project as a GUI wrapper to run batch jobs on my filesystem. This is strictly a Hobby Project and is not 'official'. Feel free to use it if you like.")
		response = dialog.run()

	def settings(self, button):
		#Settings page
		print("test")

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
			self.print_to_textview(text)
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
			self.print_to_textview(text)
		elif response == Gtk.ResponseType.CANCEL:
			print("Cancel clicked")
		dialog.destroy()

	def on_click_startocr(self, button):
		#What to do on click
		text = '"Click me3" button was clicked'
		self.print_to_textview(text)

	def on_click_menu(self, button):
		#What to do on click
		text = '"Click me4" button was clicked'
		self.print_to_textview(text)

	def print_to_textview(self, text):
		#print text to textview
		buffer = self.textview.get_buffer()
		startIter, endIter = buffer.get_bounds()
		old_text = buffer.get_text(startIter, endIter, False)
		output = old_text + text
		self.textbuffer.set_text(output)

	def clear_textview(self):
	   #empty textview buffer
	   self.textbuffer.set_text("")

win = HeaderBarWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
