#!/usr/bin/env python3
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio


class HeaderBarWindow(Gtk.Window):
    def __init__(self):
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
       	button = Gtk.Button.new_from_icon_name("open-menu-symbolic", Gtk.IconSize.MENU)
        button.connect("clicked", self.on_click_menu)       	
       	box.add(button)
        hb.pack_end(box)

	#Add Output Area
        self.box = Gtk.Box()
        self.add(self.box)
        self.textview = Gtk.TextView()
        self.box.pack_start(self.textview, True, True, 0)
        self.textbuffer = self.textview.get_buffer()


    def on_click_selectpdf(self, button):
        #What to do on click
        text = '"Click me1" button was clicked'
        self.print_to_textview(text)
        
    def on_click_selectfolder(self, button):
        #What to do on click
        text = '"Click me2" button was clicked'        
        self.print_to_textview(text)
               
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
