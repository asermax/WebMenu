#WebMenu v.1.0
#Andrea Franco 19/08/2012
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import webbrowser, os
import urllib2

from gi.repository import Gio
from gi.repository import GObject
from gi.repository import PeasGtk
from gi.repository import Gtk

DCONF_DIR = 'org.gnome.rhythmbox.plugins.webmenu'
CURRENT_VERSION = '2.0'
services = {}
services_order = []
other_settings=[]

class WMConfig(object):
##########
#The "__init__" function is called by the "do_activate" function in WebMenu.py when the program is launced. It saves the global variables for WebMenu_config.py
##########
    def __init__(self):
	global services, services_order, other_settings
        self.settings = Gio.Settings(DCONF_DIR)
	services = self.settings['services'] #'services' is a global variable with all the settings in it
	services_order=self.settings['services-order']
	other_settings=self.settings['other-settings']

    def get_settings(self):
        return self.settings

##########
#The "check_services_order" function is called by the "apply_settings" function in WebMenu.py. It eliminates settings errors. 
##########
    def check_services_order(self):
	global services_order
	changed=False #The services order is rewritten only if it is changed by this function
	for service, data in services.items():
		if service not in services_order: 
			services_order.append(service) #If a service is missing from the "service-order" key, it is added at the end
			changed=True
	for service in services_order:
		if service not in services: 
			services_order.remove(service) #If a service is missing from the "services" key, it is also deleted from the "service-order" key
			changed=True
	if changed: self.settings['services-order']=services_order
         
class WMConfigDialog(GObject.Object, PeasGtk.Configurable):
    __gtype_name__ = 'WebMenuConfigDialog'
    object = GObject.property(type=GObject.Object)

    def __init__(self):
        GObject.Object.__init__(self)
        self.settings = Gio.Settings(DCONF_DIR)

    def do_create_configure_widget(self):
         return self.manage_window(Gtk.Widget)

##########
#The "website_toggled_from_list" function is called whenever a checkbox of a website in the manage window is toggled. 
##########     
    def website_toggled_from_list(self, checkbutton, path, treeview, what):
	global services
	(model, tree_iter) =  treeview.get_selection().get_selected()
        service = model[path][0] #Gets the service name which is in the first column of the row with the toggled checkbox
	
	service_line = list(services[service]) #A tuple is read-only, so we need to convert it into a list to modify it

	service_line[what+2] = not model[path][what+2] #The setting relative to the checkbox is updated
	model[path][what+2] = service_line[what+2] #The checkbox is updated

	services[service]= tuple(service_line) #Back to tuple

##########
#The "other_settings_toggled" function is called whenever a checkbox outside the treeview is toggled. 
##########     
    def other_settings_toggled(self, checkbutton, what):
	other_settings[what] = checkbutton.get_active()

##########
#The "update_search" function simply opens a new browser window with WebMenu downloads. 
##########     
    def update_search(self, widget, data=None):
    	webbrowser.open("https://github.com/afrancoto/WebMenu/downloads")

##########
#The "change_order" function is called when one of the two arrow buttons is clicked. 
##########    
    def change_order(self, widget, treeview, liststore, direction):
	global services, services_order
	(model, tree_iter) =  treeview.get_selection().get_selected()
        service = model.get_value(tree_iter,0) #The selected service is the one wich is moved

	moved_one_index=services_order.index(service)
	if direction is 'down': moved_two_index=moved_one_index + 1
	if direction is 'up': moved_two_index=moved_one_index - 1
	
	services_order[moved_one_index]=services_order[moved_two_index] #It swaps the variables
	services_order[moved_two_index]=service

	liststore.clear() #And updates the list
	for service in services_order: liststore.append([service, services[service][1], services[service][2], services[service][3], services[service][4]])
	treeview.set_cursor(moved_two_index)

##########
#The "new_service_add" function is called from the "new_service_window". 
##########  
    def new_service_add(self, widget, name, album, artist, treeview, liststore):
	global services, services_order
        service=name.get_text() #Gets the data from the textboxes
	album_URL=album.get_text()
	artist_URL=artist.get_text()

	if (album_URL[:7] != "http://") and (album_URL[:8] != "https://") and (album_URL != ""): album_URL="http://"+album_URL #Adds the http:// if it's not in the URL
	if (artist_URL[:7] != "http://") and (artist_URL[:8] != "https://") and (artist_URL != ""): artist_URL="http://"+artist_URL
	
	if (service is not '') and not((album_URL is '') and (artist_URL is '')): #If the name is empty or both the URLs are empty, nothing is done
        	services[service] = ('', album_URL, artist_URL , True, True) #Writes the new service in the global variables
		services_order.append(service)

	liststore.clear() #And updates the list
	for service in services_order: liststore.append([service, services[service][1], services[service][2], services[service][3], services[service][4]])
	treeview.set_cursor(len(services_order)-1)
        self.window.destroy()

##########
#The "delete_service" function is called by the "delete_service" button. 
##########  
    def delete_service(self, widget, treeview, liststore):
	global services, services_order
	(model, tree_iter) =  treeview.get_selection().get_selected()
        service = model.get_value(tree_iter,0) #The selected service is the one wich is deleted

	question = _("Are you sure you want to delete '"+service+"' from WebMenu?") #A confirmation is required
    	dialog = Gtk.MessageDialog(self.window, 0, Gtk.MessageType.QUESTION, Gtk.ButtonsType.YES_NO, question) 
    	response = dialog.run()
	dialog.destroy()

	if response == Gtk.ResponseType.YES:
	    del services[service]
	    services_order.remove(service)  #Deletes the service from the global variables
	    
	    liststore.clear() #And updates the list
	    for service in services_order: liststore.append([service, services[service][1], services[service][2], services[service][3], services[service][4]])

##########
#The "reset_to_default" function is called by the "reset_to_default" button. 
##########  
    def reset_to_default(self, widget, liststore):
	#TODO: Update the other-settings checkboxes when settings are resetted 
	global services, services_order, other_settings

	question = _("Are you sure you want to restore the default services and options?\n All your changes will be lost.")  #A confirmation is required
    	dialog = Gtk.MessageDialog(self.window, 0, Gtk.MessageType.QUESTION, Gtk.ButtonsType.YES_NO, question) 
    	response = dialog.run()
	dialog.destroy()

	if response == Gtk.ResponseType.YES:
		self.settings.reset('services') #Settings are resetted, that's the only function that doesn't need "apply_settings"
		self.settings.reset('services-order')
		self.settings.reset('other-settings')
		services = self.settings['services'] #Global variables are updated
		services_order=self.settings['services-order']
		other_settings=self.settings['other-settings']
	
		liststore.clear() #And the list is updated
        	for service in services_order: liststore.append([service, services[service][1], services[service][2], services[service][3], services[service][4]])

##########
#The "row_changed" function adds a tooltip for each row with the URLs. 
##########  
    def row_changed(self, treeview, label_album_URL, label_artist_URL):
	(path, column)=treeview.get_cursor()
	(model, tree_iter) =  treeview.get_selection().get_selected()
        service = model[path][0] #Gets the service name which is in the first column of the row with the toggled checkbox

	label_album_URL.set_text(services[service][1])
	label_artist_URL.set_text(services[service][2])
	label_artist_URL.set_use_markup(True)

##########
#The "manage_window" function draws the main settings window. 
##########  
    def manage_window(self, widget, data=None):
	self.window = Gtk.Window()

	liststore = Gtk.ListStore(str, str, str, bool, bool)
	for service in services_order: liststore.append([service, services[service][1], services[service][2], services[service][3], services[service][4]])
	
	vbox=Gtk.VBox()
	treeview = Gtk.TreeView(liststore)
	treeview.set_cursor(0)

	rendererText = Gtk.CellRendererText()
        column_0 = Gtk.TreeViewColumn("Service", rendererText, text=0)
	column_0.set_resizable(True)
	column_0.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        column_0.set_fixed_width(200)
        treeview.append_column(column_0)

	rendererAlbumCheck = Gtk.CellRendererToggle()
	rendererAlbumCheck.set_property('activatable', True)
	rendererAlbumCheck.connect("toggled", self.website_toggled_from_list, treeview, 1)
	column_1 = Gtk.TreeViewColumn("Album", rendererAlbumCheck, active=3)
	column_1.set_resizable(True)
      	column_1.set_fixed_width(150)
        treeview.append_column(column_1)

	rendererArtistCheck = Gtk.CellRendererToggle()
	rendererArtistCheck.set_property('activatable', True)
	rendererArtistCheck.connect("toggled", self.website_toggled_from_list, treeview, 2)
	column_2 = Gtk.TreeViewColumn("Artist", rendererArtistCheck, active=4)
	column_2.set_resizable(True)
        column_2.set_fixed_width(150)
        treeview.append_column(column_2)	

	scroll = Gtk.ScrolledWindow()
    	scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    	scroll.add(treeview)
	scroll.set_min_content_width(300)
	scroll.set_min_content_height(300)
	vbox.pack_start(scroll, True, True, 5)

	frame=Gtk.Frame(label="URLs:")
	
	hbox_line1=Gtk.HBox()
	label_album=Gtk.Label("<b>Album:</b> ", use_markup=True)
	label_album.set_alignment(0,0)
	hbox_line1.pack_start(label_album, False, True, 0)    
	label_album_URL=Gtk.Label(services[liststore[0][0]][1])
	label_album_URL.set_justify(Gtk.Justification.LEFT)
	label_album_URL.set_alignment(0,0)
	hbox_line1.pack_start(label_album_URL, False, True, 0)  

	hbox_line2=Gtk.HBox()
	label_artist=Gtk.Label("<b>Artist:</b> ", use_markup=True)
	label_artist.set_alignment(0,0)
	hbox_line2.pack_start(label_artist, False, True, 0)    
	label_artist_URL=Gtk.Label(services[liststore[0][0]][2])
	label_artist_URL.set_justify(Gtk.Justification.LEFT)
	label_artist_URL.set_alignment(0,0)
	hbox_line2.pack_start(label_artist_URL, False, True, 0)   

	vbox_in_frame=Gtk.VBox()
	vbox_in_frame.pack_start(hbox_line1, False, True, 0)
	vbox_in_frame.pack_start(hbox_line2, False, True, 0)

	scroll_urls = Gtk.ScrolledWindow()
    	scroll_urls .set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    	scroll_urls.add_with_viewport(vbox_in_frame)
	scroll_urls.set_min_content_width(90)
	#scroll_urls.set_min_content_height(60)
	frame.add(scroll_urls)
	hbox_out_frame=Gtk.HBox()
	hbox_out_frame.pack_start(frame, True, True, 5)    
	vbox.pack_start(hbox_out_frame, False, True, 5)    

	other_settings_hbox=Gtk.HBox()

	all_album_check = Gtk.CheckButton("Album/All") #The 'All'-album checkbox
        all_album_check.set_active(other_settings[1])
	all_album_check.connect("toggled", self.other_settings_toggled, 1) #The last argument, 1, stands for "Album"   
	other_settings_hbox.pack_start(all_album_check, False, False, 0)

	all_artist_check = Gtk.CheckButton("Artist/All") #The 'All'-artist checkbox
        all_artist_check.set_active(other_settings[2])
	all_artist_check.connect("toggled", self.other_settings_toggled, 2) #The last argument, 1, stands for "Album"   
	other_settings_hbox.pack_start(all_artist_check, False, False, 10)

	options_check = Gtk.CheckButton("Web/Options") #The 'Options' checkbox
        options_check.set_active(other_settings[0])
	options_check.connect("toggled", self.other_settings_toggled, 0) #The last argument, 2, stands for the "Options" item
	other_settings_hbox.pack_start(options_check, False, False, 10)

	vbox.pack_start(other_settings_hbox, False, True, 5)

	hbox1=Gtk.HBox()
        button_up = Gtk.Button(u'\u2191')
        button_up.connect("clicked", self.change_order, treeview, liststore, 'up')
        hbox1.pack_start(button_up, False, True, 0)
            
        button_down = Gtk.Button(u'\u2193')
        button_down.connect("clicked", self.change_order, treeview, liststore, 'down')
        hbox1.pack_start(button_down, False, True, 0)

	new_button = Gtk.Button("Add Service")
	new_button.connect("clicked", self.new_service_window, treeview, liststore)
	hbox1.pack_start(new_button, False, True, 0)

        delete_button = Gtk.Button('Delete Service')
        delete_button.connect("clicked", self.delete_service, treeview, liststore)
        hbox1.pack_start(delete_button, False, True, 0)

        reset_button = Gtk.Button('Reset to default')
        reset_button.connect("clicked", self.reset_to_default, liststore)
        hbox1.pack_end(reset_button, False, False, 0)
	vbox.pack_start(hbox1, False, True, 5)

	hbox2=Gtk.HBox()
	done_button = Gtk.Button(stock=Gtk.STOCK_APPLY)
	hbox2.pack_end(done_button, False, False, 0)
	done_button.connect_object("clicked", self.apply_settings, self.window)

	update_button = Gtk.Button("Updates? (v."+CURRENT_VERSION+")")
	update_button.connect("clicked", self.update_search)
        hbox2.pack_start(update_button, False, False, 0)

	vbox.pack_start(hbox2, False, True, 5)

	treeview.connect('cursor-changed', self.row_changed, label_album_URL, label_artist_URL)
	self.window.add(vbox)
	self.window.show_all()
	return

##########
#The "new_service_window" function draws the window to add a new service. 
##########  
    def new_service_window(self, widget, treeview, liststore):
	self.window = Gtk.Window()

	vbox=Gtk.VBox(False, 0)
	vbox.set_margin_left(15)
	vbox.set_margin_right(15)
	main_label = Gtk.Label("<b>Add a new service:</b>", use_markup=True) #Main label 
	vbox.pack_start(main_label, False, False, 10)
	description_label = Gtk.Label("Make a search on the website you want to add, copy here the URL and replace your query\n"
				      "with the keywords: <b>[ALBUM]</b> and/or <b>[ARTIST]</b>\n"
				      "<i>(If you want the service to show up in only one menu, simply leave the other URL empty.)</i>", use_markup=True) #Description label  
	vbox.pack_start(description_label, False, False, 10)	

	hbox=Gtk.HBox(False, 5)
	
	vbox_labels=Gtk.VBox(False, 7)
 	name_label = Gtk.Label("<b>Service Name:</b>", use_markup=True)
	vbox_labels.pack_start(name_label, True, True, 0)

 	album_url_label = Gtk.Label("<b>Album URL:</b>", use_markup=True)
	vbox_labels.pack_start(album_url_label, True, True, 0)

 	artist_url_label = Gtk.Label("<b>Artist URL</b>", use_markup=True)
	vbox_labels.pack_start(artist_url_label, True, True, 0)
	hbox.pack_start(vbox_labels, False, False, 0)	

	vbox_entries=Gtk.VBox(False, 7)
 	name_entry = Gtk.Entry()
	name_entry.set_width_chars(52)
	name_entry.set_max_length(30)
	name_entry.set_text('')
	vbox_entries.pack_start(name_entry, True, True, 0)

 	album_url_entry = Gtk.Entry()
	album_url_entry.set_max_length(300)
	album_url_entry.set_text('')
	vbox_entries.pack_start(album_url_entry, True, True, 0)

 	artist_url_entry = Gtk.Entry()
	artist_url_entry.set_max_length(300)
	artist_url_entry.set_text('')
	vbox_entries.pack_start(artist_url_entry, True, True, 0)
	hbox.pack_start(vbox_entries, False, False, 0)	
	vbox.pack_start(hbox, False, False, 10)

	bbox = Gtk.HButtonBox()
	bbox.set_border_width(5)
	bbox.set_layout(Gtk.ButtonBoxStyle.END)
	bbox.set_spacing(10)
	create_button = Gtk.Button(stock=Gtk.STOCK_OK)
	create_button.connect("clicked", self.new_service_add, name_entry, 
	                                                       album_url_entry, 
	                                                       artist_url_entry,
							       treeview, liststore)
	bbox.add(create_button)

	cancel_button = Gtk.Button(stock=Gtk.STOCK_CANCEL)
	bbox.add(cancel_button)
	cancel_button.connect_object("clicked", Gtk.Widget.destroy, self.window)

	#button = Gtk.Button(stock=Gtk.STOCK_HELP) #Future development
	#bbox.add(button)
	vbox.pack_start(bbox, False, False, 0)
        self.window.add(vbox)
	self.window.show_all()
	return

##########
#The "apply_settings" function is called by the "apply" button in the manage window, it's the only function that writes in dconf ("reset_to_default" excluded)  
########## 
    def apply_settings(self, widget, data=None):
	self.settings['services']=services
	self.settings['services-order']=services_order
	self.settings['other-settings']=other_settings
	self.window.destroy()

