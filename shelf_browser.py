#this is a complete mess but does do the job (just about) and proves the concept
#work to do:
# 1. encapsulate tk elements in classes and revise current_shelf variable and shelf handling.  //DONE
# 2. Eliminate duplicated code by moving to functions											//DONE (mostly)
# 3. add search function for frame1 (list items) and frame2 (text output of elements)			//DONE
# 4. add "jump to" ELEMENTS in frame2  (maybe right-click context??)  //DONE
# 5. make frame2 read-only with copy-paste functions  			//DONE
# 6. add ctrl-a to select all content in frame2					//DONE
# 7. implement font family to avoid constantly setting fonts.   //DONE
# 8. implement font resizing properly. 							//DONE
# 9. implent sort for listbox 									//DONE
# 10. implement search.											//DONE
# 11. implement URL click.										//DONE
# 12. implement <html> recognition for not response input or add html tick box.		  //STILL TO DO IF USEFUL	
# 13. consider starting the 'next' of the search at the cursor rather than always 0   //STILL TO DO IF USEFUL (possibly not)
# 14. highlight search result text in list box. 				//cant be done without rebuilding listbox with text widget
# 15. improve fonts on windows-1252								//DONE
# 16. add shelf details menu type notifier using dbm.whichdb						//DONE
# 17. add functionality to save shelf in dumbdbm format for use with windows.		//DONE
# 18. print file open errors to message boxes (capture err text from err event)		//DONE
# 19. clean up order of functions and add comments
# 20. add specific check for existance of file selected.							//DONE  
#						(because windows does not register cancel as an error)  
# 21. create popup menu class to avoid repeating the code in results and shelf manager  //DONE
# change __default font in FindEntry to be a public properts so it can be changed.
# 22. improve tk_selectall and tk_copy to handle both evt and widget passed.		//DONE
# 23. add paste functionality for Entry and create popup menu to copy/paste/cut?? to FindEntry  //DONE


'''
NAME
	shelf_browser - a small GUI to view read-only contents of shelve files


DESCRIPTION
	This is a small project primarily undertaken for the purpose of learning
	tkinter but solving a genuine need to quickly access and view the 
	contents of shelf files created by the shelve module.  The application 
	is meant purely to provide a quick read-only look at the contents and not
	to provide more extensive interactions with the shelf file. 

	The classes contained within are meant to be used together to form the 
	whole application but where possible I have built them so they are 
	independent enough to use as components in future projects.

	Application Functionality:
		- Browse to and open shelf file (File --> Open...)
		- Quick reference to name of currently opened shelf file
		- View details of open shelf file (File --> File Info...)
		- create copy of current shelf in dbm.dumb format for portability
			(File--> File Info --> "Convert to portable format")
		- Scrollable list of shelf keys provided in left hand pane (listbox)
		- Keys are sorted alphabetically prior to being displayed
		- Listbox displays key entries in alternating bg colour
		- R-click or ctrl-c to copy key text to clipboard
		- Filter shelf keys based on search criteria typed into search entry 
		- Disable filter (show all key, ignoring what is in the search entry)
		- View summary information about shelf keys in info bar at bottom of list
		    - how many shelf keys in file
		    - how many are being displayed (ie. not filtered)
		    - which position key is currently selected
		- Left-click listbox item to display details of value stored for the 
			key in right hand pane
		- Press delete to delete key/value entry from shelf (one at a time)
		- Pbject type and preview of value displayed in summary pane (top right)
		- Detailed string version of value displayed in scrolling text box 
			which is read-only (right pane).
		- If value is a list or tuple, the text box is broken down into sections
			with further details of the sub item object type and content.
			(one level only for now and no tree view yet.)
		- Right-click to jump between different sections if list or tuple output
			has been handled
		- Highlight search value matches for strings entered in search entry
		- Display x/x search results statistics on floating pane.
		- Close floating search stats pane by clicking red x
		- Iterate through matched search results either forward or backwards
		- Press enter on search entry box to iterate forwards through matches
		- 'Current' search match is highlighted a different colour
		- Some intitive interactions enabled on scrolled text 
			(ctrl-a, click drag to highlight, left-click to deselect)
		- R-click to copy highlighted text from scrolled text
		- Font size interaction, (indepentent for left and right frames
				in order to be able to achieve different text sizes:
			ctrl-+ 		increase font size by 1.
			ctrl--		decrease font size by 1.
			ctrl-0		reset font size to 8
		- Set font size via menu (applies to ALL fonts in application)
			(Edit --> Font)  
		- Cut, Copy, Paste r-click context menu for search entry widget
		- Exit application (File --> Exit)


Included Classes:
	
	DefaultContextMenu(tk.Menu)
		Provide a default r-click style context menu for cut, copy paste

	ShelfBrowser()
		Manage master tkinter frame and application layout

	FindEntry()
		Provide Entry box for text searches. For reference by other classes

	ShelfManager()
		Manage shelve file interaction and present shelve.keys() in listbox

	ResultsPane()
		Present shelf value content in text format in tkinter Text()  


Useful Functions:

	set_fonts()
		Change font size for a tk.Font() object
		
	font_events()
		Increases or decreases size of fonts on ctrl-+, ctrl--, ctrl-0

	goto_url()
		Open URL passed by calling program

	url_cursor()
		Change cursor type to hand2 for rolling over urls

	print_key()
		print the key generating the event to stdout

	set_widget_focus()
		Set current focus on widget generating the event

	tktext_cancel_sel()
		Cleanly removes highlighted selection for tk.Text() widgets

	tkcopy()
		Copy highlighted text to clipboard

	tkcut()
		Copy highlighted text to clipboard

	tkpaste()
		Paste clipboard text to widget

	tk_selectall()
		Handle ctrl-a event to select all

'''

import math
import os
import stat #for interpreting os.stat results
from functools import partial
from time import asctime, localtime, strftime

import shelve
import requests
from bs4 import BeautifulSoup
import webbrowser
from dbm import whichdb, dumb

import tkinter as tk
import tkinter.font as tkfnt
from tkinter import filedialog
from tkinter import messagebox
from tkinter import scrolledtext
from tkinter import ttk

# Helper functions and event handlers not widget or class specific.
def set_fonts(fnt, f_size):
	'''Change font size for a tk.Font() object'''
	fnt.configure(size=f_size)
	return 'break'

def font_events(evt, fnt_grp,*, f_size=None):
	'''
	Increases or decreases size of fonts on ctrl-+, ctrl--, ctrl-0

	Expects a list object with any number of sub lists of the makeup
	[<font object>, <size offset>].  The former is a tk.Font() object that 
	will be altered, the latter is a size offset relative to the f_size
	parameter which must be passed if ctrl-0 is received.  

	Note that f_size MUST be passed in the case of a Ctrl-0 event.

	Parameters:

		fnt_grp : List
			entries must be sublists of format [<font object>, <size offset>]
			list of tk.Font() objects to update with size

		f_size : int
			in the case of Ctrl-0, size of font to adjust to

	''' 
	for f in fnt_grp:
		if evt.keysym in ['plus', 'equal']:
			f[0].configure(size=f[0].cget('size')+1)
		elif evt.keysym == 'minus':
			f[0].configure(size=f[0].cget('size')-1)
		elif evt.keysym == '0':
			f[0].configure(size=f_size+f[1]) # no error catch in case f_size missed. we want the error.
	return 'break'

def goto_url(evt, url):
	'''Open URL passed by calling program'''
	webbrowser.open(url)
	return 'break'

def url_cursor(evt):
	'''Change cursor type to hand2 for rolling over urls'''
	if evt.type == '7':	#7 = '<Enter>' event
		evt.widget.config(cursor='hand2')
	else:				#assume this will always be event type #8 '<Leave>'
		evt.widget.config(cursor='')
	return 'break'

def print_key(evt):
	'''print the key generating the event to stdout'''
	print(evt.keysym)
	return 'break'

def set_widget_focus(evt):
	'''Set current focus on widget generating the event'''
	evt.widget.focus_set()
	return 'break'

def tktext_cancel_sel(evt):
	'''Cleanly removes highlighted selection for tk.Text() widgets'''
	if not isinstance(evt.widget, tk.Text):
		return 'break'
	evt.widget.tag_remove(tk.SEL, 1.0, tk.END)
	evt.widget.mark_unset('tk::anchor1')
	evt.widget.mark_set(tk.INSERT, tk.CURRENT)

def tkcopy(evt=None, widget=None):
	'''Copy highlighted text to clipboard'''
	widget = widget or evt.widget   # or acts as coalesce here
	if isinstance(widget, (tk.Text, tk.Entry)):
		try:
			widget.clipboard_clear()
			widget.clipboard_append(widget.selection_get())			
		except:
			pass
	elif isinstance(widget, tk.Listbox):
		try:
			widget.clipboard_clear()
			widget.clipboard_append(widget.get(widget.curselection()[0]))
		except:
			widget.clipboard_append('')
	return 'break'

def tkcut(evt=None, widget=None):
	'''Copy highlighted text to clipboard'''
	widget = widget or evt.widget   # or acts as coalesce here
	if isinstance(widget, (tk.Text, tk.Entry)):
		try:
			widget.clipboard_clear()
			widget.clipboard_append(widget.selection_get())
			widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
		except Exception as err:
			pass
	return 'break'

def tkpaste(evt=None, widget=None):
	'''Paste clipboard text to widget'''
	widget = widget or evt.widget   # or acts as coalesce here
	if isinstance(widget, (tk.Text, tk.Entry)):
		widget.focus()
		widget.insert(tk.INSERT, widget.clipboard_get())
		try:  # try to delete any current selection
			widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
		except Exception as err:
			pass
	return 'break'

def tk_selectall(evt=None, widget=None):
	'''Handle ctrl-a event to select all'''
	widget = widget or evt.widget  	#or acts as coalesce here
	if isinstance(widget, tk.Text):
		widget.tag_add('sel', '1.0', 'end')
		widget.mark_set(tk.INSERT, 1.0)
	elif isinstance(widget, tk.Entry):
		widget.select_range(0, 'end')

	return 'break'


class DefaultContextMenu(tk.Menu):
	'''
	Provide a default r-click context menu with copy/paste capability.

	Inherits from tk.Menu() object.

	Attributes:

		master : tkinter widget
			widget over which the context menu will appear

		__default_commands : dict
			dictionary of default commands to be included in the menu
			and their current status (True=show, False=hide). Set with
			self.setup().

	Methods:

		popup (self, evt)
			triggered by an event call from the master widget.  posts
			the menu at the coordinates of the mouse.

		popupFocusOut(self, evt):
			hide the menu when the user clicks away

		setup(self, **kwargs)
			updates the show/hide status of the default menu items and
			populates the menu with default options.  Call with
			dfcopy/dfpaste/dfcancel = True/False.

		reset(self)
			calls setup().  this is simply to provide a more readable call
			for the setup function when resetting the menu during a 
			program.

	'''
	def __init__(self, master, cnf={}, **kw):
		'''See tkinter.Menu() docs'''
		tk.Menu.__init__(self, master, cnf, **kw)
		self.master = master
		self.__default_commands = {'dfcopy':True, 'dfcut': True, 'dfpaste':True, 'dfcancel':True}
		self.tearoff = 0
		self.bind("<FocusOut>", self.popupFocusOut)
		self.setup()

	def popup(self, evt):
		'''Posts the menu at the coordinates of the mouse'''
		try:
			self.post(evt.x_root, evt.y_root)
			self.focus()	#need to set focus in order for <FocusOut> to work.
		finally:
			self.grab_release()
		return 'break'

	def popupFocusOut(self, evt):
		'''Hides menu when user clicks away'''
		self.unpost()
		return 'break'

	def setup(self, **kwargs):
		'''
		Update default menu items to show and redraw menu.

		Parameters:

			**kwargs
				valid values:   dfcopy=True/False		Copy
								dfpaste=True/False		Paste
								dfcancel=True/False		Cancel
		
		'''
		for c in self.__default_commands.keys():
			u = kwargs.get(c)
			if type(u) == bool:
				self.__default_commands[c] = u

		self.delete(0, tk.END)		
		if self.__default_commands.get('dfcopy'):
			self.add_command(label='Copy', command=partial(tkcopy, evt=None, widget=self.master))
		if self.__default_commands.get('dfcut'):
			self.add_command(label='Cut', command=partial(tkcut, evt=None, widget=self.master))
		if self.__default_commands.get('dfpaste'):
			self.add_command(label='Paste', command=partial(tkpaste, evt=None, widget=self.master))
		if self.__default_commands.get('dfcancel'):
			self.add_command(label='Cancel')

	def reset(self):
		'''Call self.setup()'''
		self.setup()
		

class ShelfBrowser():
	''' 
	Master class to manage window layout, fonts and menu bar.

	ShelfBrowser initiates and sets overall app layout, initiates 
	other classes which contain program functionality and controls 
	basic menu functions.  This class also sets the default font 
	from which overall application look feel is derived by other
	classes.

	Call this from __main__ with a Tk() object as arguement.
	Eg. 
	  >>> import tkinter as tk
	  >>> root = tk.Tk()
	  >>> ShelfBrowser(root)
	  >>> root.mainloop()

	Parameters:  
		see __init__ doc string.

	Attributes:

		root : tk.Tk()
			primary window object under which all further frames will be
			  created

		main_font : tk.Font()
			the default font to be used throughout the application

	Methods:

		__open_shelf()
			Called from the File menu.
			Opens a file-selection dialog and passes a selected
			  file path to the ShelfManager instance.

		__fontsize(f_size):
			Called as command arguement from fontsize menu with the
			 selected font size as a parameter.  Subsequently calls
			 font resize methods of other classes as needed.

		__file_info():
			Called as command arguement from File menu.  
			Creates a custom transient dialog window in which to display
			  details about the currently open file.  File details are 
			  requested by calling ShelfManager.get_shelf_details('p')

			Also creates a command button to activate
			  ShelfManager.convert_to_dumb()

			Note: The construction of this dialog should perhaps have been 
			  managed entirely by the ShelfManager class but I decided to 
			  leave menu creation in the hands of this class and push the 
			  heavy lifting of determining the file detils to ShelfManager.
			  I'm still wondering whether to change it.   

	'''
	def __init__(self, parent):
		'''
		Create window layout, font, menu and call appication classes.
			
		Parameters:

			parent : tk.Tk()
				root tkinter window in which to build application.

		'''
	 	#define main font/s
		self.__fonts = []
		self.main_font = tkfnt.Font(size=8)
		self.__fonts.append(self.main_font)

		#create root window
		self.root = parent
		self.root.title('Shelf Browser Utility - 1.0')
		self.root.geometry('1300x800') 
		self.root.rowconfigure(1, weight=1)
		self.root.columnconfigure(0, weight=1)

		#add paned window to hold 2 main application frames 
		self.pwin = tk.PanedWindow(self.root)
		self.pwin.grid(column=0, row=1, sticky=(tk.N,tk.S,tk.E,tk.W))

		#add frames window to act as root for application classes
		#frame0 - search box (FindEntry() class)
		self.frame0 = tk.Frame(self.root)
		self.frame0.grid(column=0, row=0, sticky=(tk.N,tk.S,tk.E,tk.W))
		self.frame0.rowconfigure(0, weight=1)
		self.frame0.columnconfigure(0, weight=1)
		#frame1 - paned window left frame list box (ShelfManager() class)
		self.frame1 = tk.Frame(self.pwin)
		self.frame1.rowconfigure(1, weight=1)
		self.frame1.columnconfigure(0, weight=1)
		self.pwin.add(self.frame1, width=650)
		#frame2 - paned window right frame text box (ResultsPane() class)
		self.frame2 = tk.Frame(self.pwin)
		self.frame2.rowconfigure(1, weight=1)
		self.frame2.columnconfigure(0, weight=1)
		self.pwin.add(self.frame2)

		#construct menus
		#master menu
		self.men1 = tk.Menu(self.pwin, font=self.main_font, tearoff=0)
		#File Menu
		self.file_menu = tk.Menu(self.men1, font=self.main_font, tearoff=0)
		self.file_menu.add_command(label='Open...', command=self.__open_shelf)
		self.file_menu.add_command(label='File info...', command=self.__file_info)
		self.file_menu.add_separator()
		self.file_menu.add_command(label='Exit', command=self.root.destroy)
		self.men1.add_cascade(label='File', menu=self.file_menu)
	 	#Edit menu
		self.edit_menu = tk.Menu(self.men1, font=self.main_font, tearoff=0)
		self.fonts_menu = tk.Menu(self.edit_menu, font=self.main_font, tearoff=0)
		for f in [4,6,8,10,12,14,16,18,20]:	
			self.fonts_menu.add_command(label=f, command=partial(self.__fontsize, f_size=f))
		self.edit_menu.add_cascade(label='Font', menu=self.fonts_menu)
		self.men1.add_cascade(label='Edit', menu=self.edit_menu)	
		#add completed menu to root window
		self.root.config(menu=self.men1)

		#add search box (frame0)
		self.findentry = FindEntry(self.frame0, self.main_font)

		#add results pane (frame2)
		self.resultspane = ResultsPane(self.frame2, self.main_font, self.findentry)

		#add list box (frame1)
		self.shelfmanager = ShelfManager(self.frame1, self.main_font, self.resultspane, self.findentry)

	def __open_shelf(self):
		'''
		Ask user to select a file and pass path to ShelfManager class

		'''
		try:
			path_ = ''
			path_ = filedialog.askopenfilename()
			if not os.path.isfile(path_):
				raise Exception('os.path.isfile() returns False')
			self.shelfmanager.populate(path_)
		except Exception as err:
			errmsg = 'Error selecting file.\n\nException of type {0} occurred.\n{1!r}'.format(type(err).__name__, err.args)
			messagebox.showwarning('File selection error...', errmsg)
			return 'break'

	def __fontsize(self, f_size):
		'''
		Alter font size for all applicable fonts within current self.fonts

		This method resizes fonts within the current instance based on
		the input parameter and then calls the font resize method of any
		additional objects which manage their own fonts if required.

		Parameters:

			f_size : Int
			   integer determining new font size to apply

		'''
		for f in self.__fonts:
			f.configure(size=f_size)
		self.resultspane.resize_fonts(f_size)

	def __file_info(self):
		'''
		Create custom dialog window and fill it with output from ShelfManager. 

		Creates a custom dialog window using tk.Toplevel() and populates 
		it with details of the currently open file being managed by a 
		ShelfManager object. The intention of this method is to provide
		the layout/presentation window while ShelfManager takes care of
		interrogating the file.

		The ShelfManager.get_shelf_details() method is called to retreive
		the relevant file information.  Passing the 'p' value as
		parameter requests a printable list rather than raw attribute
		data.

		'''
		self.info_dialog = tk.Toplevel()
		self.info_dialog.title('File info...')
		self.info_dialog.transient(self.root)
		shelf_detail = self.shelfmanager.get_shelf_details('p')
		txt1 = ''
		txt2 = ''
		for i in shelf_detail:
			txt1 += '{}:\r\n'.format(i[0])
			txt2 += '\t{}\r\n'.format(i[1])
		self.info_dialog_lbl1 = tk.Label(self.info_dialog, text=txt1, justify=tk.LEFT, font=self.main_font)  
		self.info_dialog_lbl1.grid(row=0, column=0, ipadx=20, ipady=20)
		self.info_dialog_lbl2 = tk.Label(self.info_dialog, text=txt2, justify=tk.LEFT, font=self.main_font)  
		self.info_dialog_lbl2.grid(row=0, column=1, ipadx=20, ipady=20)
		self.info_dialog_close = tk.Button(self.info_dialog, 
										  	   text='Close', 
										       font=self.main_font,
										       command=self.info_dialog.destroy)
		self.info_dialog_close.grid(row=10, column=0, columnspan=2, padx=10, pady=10)
		self.info_dialog_convert = tk.Button(self.info_dialog, 
										  	   text='Convert to portable format (dbm.dumb)', 
										       font=self.main_font,
										       bg='red',
										       command=self.shelfmanager.convert_to_dumb)
		self.info_dialog_convert.grid(row=11, column=0, columnspan=2, padx=20, pady=20)


class FindEntry():
	'''
	Search box object intended for re-use by multiple other objects.

	FindEntry() provides a tk.Entry widget for the user to type
	a search string into.  It is intended to offer a single point
	of entry to the user and therefore to be interrogated by
	multiple parts of the application as part of their independent
	search / filter methods.

	Parameters:  
		see __init__ doc string.

	Attributes:

		root : tkinter window object (multiple)
			a frame or window in which to place the Entry widget

		active : tk.BooleanVar()
			1 = instance is being used by the user to search
			0 = instance is inactive (not in use)

		search_string : tk.StringVar()
			string value representing current value of Entry 
			widget.  When active=1, this is the value of
			the user's text search inquiry.  When active=0
			this is the default text on the widget.

		main_font : tk.Font()
			default font used by the widget, defined by from 
			calling entity

	Methods:

		__usage_indicator(self, args*)
			triggered by <FocusIn> and <FocusOut> events.
			sets the active attribute on or off depending on 
			  whether a search value is entered. 
			sets the value of the Entry widget to default 
			  when not in use.
			removes the default text from Entry widget 
			  when moving from inactive to active state

		__ctrl_backspce(self, evt)
			deletes all text from the widget on Control-Backspace 

	'''
	def __init__(self, parent, fnt=None):
		'''
		Initiate search box objects, define layout and set event bindings.

		Parameters:

			parent : tk.Tk()
				frame or Tk() window in which to place Entry widget

			fnt : tk.Font()
				a default font for use or derivation throughout.
				if fnt=None, a default font of size 8 will be defined.

		'''
		self.root = parent
		self.active = tk.BooleanVar()
		self.search_string = tk.StringVar()
		self.__default_text = '<search here>'

		self.active.set(0)

		#setup fonts
		self.__fonts = []
		if fnt == None:
			self.main_font = tkfnt.Font(size=8)
		else:
			self.main_font = fnt

		#setup entry box
		self.search_string.set(self.__default_text)
		self.find_entry = tk.Entry(self.root, font=self.main_font, textvariable=self.search_string, border=2, fg='grey')
		self.find_entry.grid(column=0, row=0, sticky=(tk.N,tk.S,tk.E,tk.W))
		
		#setup event bindings
		self.find_entry.bind('<FocusIn>', self.__usage_indicator)
		self.find_entry.bind('<FocusOut>', self.__usage_indicator)
		self.find_entry.bind('<Control-a>', tk_selectall)
		self.find_entry.bind('<Control-BackSpace>', self.__ctrl_backspce)

		#popup menu
		self.context_menu = DefaultContextMenu(self.find_entry, tearoff=0, font=self.main_font)
		self.find_entry.bind('<Button-3>', self.context_menu.popup)

	def __usage_indicator(self, *args):
		'''		Set self.active indicator.  See class doc string for details.'''
		if len(self.find_entry.get()) == 0:
			self.active.set(0)
			self.search_string.set(self.__default_text)
		elif self.active.get() == 0:
			self.search_string.set('')
			self.active.set(1)
		return 'break'

	#event handlers
	def __ctrl_backspce(self, evt):
		'''		Event handler. Delete contents of search box when triggered.'''
		evt.widget.delete(0, tk.END)
		return 'break'


class ShelfManager():
	'''
	Open shelf file, display keys and handle user interactions.

	This class creates a tk.Listbox object and populates it with the keys 
	present in a shelve.Shelf().  It's primary purpose is to manage 
	opening of the shelf file, displaying the key entries within and 
	passing values to a separate display handler.  At the time of writing
	the display handler is intended to be a ResultsPane() object but 
	this ShelfManager could easily be used with a different object with 
	very minor corrections to the sendto_target() method.

	The class also offers functionality to delete an entry from a shelf
	file and to return file system info about the opened file. 

	

	Attributes:
		root : tk.Tk() or other tkinter frame object
			a frame or window in which to place the Entry widget

		current_shelf : str
			path of current shelf file.  
			This is separate to __selected_shelf_file because some
			  formats of shelf (eg. dbm.dumb) are not called by filename
			  but rather by a general shelf name.  
			  (eg shelve.open('/test' may refer to /test.bak, /test.dat etc)

		main_font : tk.Font()
			default font used by the widget, defined by from 
			  calling entity

		shelfkeys : List
			full list of keys extracted from the 'current' (most recently
			  opened) shelf file.

		search_check_val : tk.IntVar()
			current value of the 'disable filter' checkbox    0=off; 1=on.
			a trace is setup on this value to react to any changes.

		target_pane : ResultsPane() or other text display handler
			optional default display handler to which to send values.
			used by send_to_target

		target_find : FindEntry()
			instance of FindEntry() passed as a parameter when instantiating.
			this object will be tracked for search/filter functionality. 

		__selected_shelf_file : str
			path of the specific file selected by the user.  This may differ
			to the value of current_shelf.  (See current_shelf doc above.)

	Methods:

		populate(self, filepath)
			open shelf file passed as parameter and populate listbox with 
			  keys. Also populates self.current_shelf and 
			  self.__selected_shelf_file

		reset_list(self, populate=False)
			delete all current entries from key listbox.  
			if populate=True is passed, will repopulate lisbox with all 
			  keys from self.shelfkeys variable.

		colour_items(self)
			add alternate colouring for lines in listbox.
			in a future enhancement this could be updated to make the
			  colours configurable by the user.

		set_infobar(self, *args)
			add details to the information bar which is placed at the 
			  bottom of the frame.  This is called whenever the listbox
			  changes (<<ListboxSelect>>) or by other functions which
			  alter the state of the listbox.
			
			Info displayed:
			  Total number of items in self.shelfkeys
			  Total number of items currently in listbox (in case of filter)
			  Current index number selected in 

		filter_list(self, *args)
			filters the main listbox based on changes to the search criteria
			  entered into the FindEntry() object defined in the target_find()
			  parameter.  If the searchbox is not active or if the 
			  'disable filter' checkbox is checked, the function will 
			  populate the listbox with the full contents of self.shelfkeys.

			this function could be updated in the future to take filter input
			  from other sources than the target_find object.

		selected_key(self)
			return index of currently selected item.  included simply to make
			  the code more readable.

		sendto_target(self, target=None)
			retreives the shelf value for the associated input key and calls
			  a display handler, passing the value content as a parameter.
			  Called either by a <<ListboxSelect>> event or by 
			  <Double-Button-1> event.
			
			by default, the function will call the .populate() method of
			  the object passed as target_pane but if target_pane=None 
			  the function will create a tk.Toplevel() window and create
			  new ResultsPane() and FindEntry() instances to populate it
			  before passing the value content to this new object.    

		get_shelf_details(self, mode='p')	-> List  or -> Dict
			returns relevant file details of the currently opened
			shelf file using os.stat and dbm.whichdb.  

			mode='p' will return a formatted list of values ready for display
			mode='d' will return a dictionary containing raw values

			details returned are:
			  - file name
			  - directory name
			  - full path
			  - dbm schema (dbm.dumb, dbm.gnu etc)
			  - file size
			  - created
			  - last modified
			  - last accessed

		convert_to_dumb(self)
			if the current shelf file is not already dbm.dumb format, this
			  method creates a copy in dbm.dumb format.  The purpose of this
			  is to enable the user to create a cross-platform compatible
			  version of the shelf if needed.

	Event Handler Methods:
		
		item_delete(self, evt)		Trigger : <<Delete>>
			when delete key is pressed, removes the key/value from current_shelf
			corresponding to the currently selected key in listbox.

		item_select(self, evt)		Trigger : <<ListboxSelect>>
			calls the sendto_target() function with target_pane specified.

		expand_result(self, evt)	Trigger : <Return>
			calls the sendto_target() function with no target_pane specified
			  forcing the application to create a separate popup window to 
			  pass the value to.  


		search_check_change(self, *args) 	Trigger : self.search_check_val.trace()
			trigger filtering of the listbox in case "disable filter"
			checkbox is turned on.

	'''
	def __init__(self, parent, fnt=None, target_pane=None, target_find=None):
		'''
		Initiate ShelfManager() objects, define layout and set event bindings.

		Parameters:

			parent : tk.Tk()
				frame or Tk() window in which to place listbox and other widgets

			fnt : tk.Font()
				a default font for use or derivation throughout.
				if fnt=None, a default font of size 8 will be defined.

			target_pane : ResultsPane() or other display handler
				object to call when passing shelve values for display.
				assume ResultsPane() object here but any other object with a 
				  .populate method is acceptable.

			target_find : FindEntry()
				FindEntry() object which will be accessed for filter criteria.

		'''
		self.root = parent
		self.current_shelf = '<no shelf to display>'
		self.__selected_shelf_file = ''
		self.target_pane = target_pane
		self.shelfkeys = []
		self.search_check_val = tk.IntVar()
		self.search_check_val.trace('w', self.search_check_change)

		#setup fonts
		self.fonts = []
		if fnt == None:
			self.main_font = tkfnt.Font(size=8)
		else:
			self.main_font = fnt

		#if search entry is defined, setup trigger to capture change events
		if target_find:
			self.target_find = target_find
			self.search_string = self.target_find.search_string
			self.search_string.trace('w', self.filter_list)

		#create label showing current file
		self.file_label = tk.Label(self.root, text=self.current_shelf, fg='white', bg='grey', anchor='w', font=('Ariel', 6, 'bold'))
		self.file_label.grid(column=0, row=0, sticky=(tk.N,tk.S,tk.E,tk.W))
		#create search check box
		self.search_check = tk.Checkbutton(self.root, text='disable search', variable=self.search_check_val, onvalue=1, offvalue=0, fg='#D3D3D3', bg='grey', highlightthickness=0, justify='center', font=('Ariel', 6))
		self.search_check.grid(column=0, row=0, sticky=tk.E)
		#create main list box
		self.keylist = tk.Listbox(self.root, font=self.main_font, exportselection=False)
		self.keylist.grid(column=0, row=1, sticky=(tk.N,tk.S,tk.E,tk.W))
		self.keylist.activate(0)
		self.keylist.bind('<<ListboxSelect>>', self.set_infobar)
		self.keylist.bind('<<ListboxSelect>>', self.item_select, add='+')
		self.keylist.bind('<Double-Button-1>', self.expand_result)
		self.keylist.bind('<Return>', self.expand_result)
		self.keylist.bind('<Delete>', self.item_delete)
		self.keylist.bind('<Control-plus>', partial(font_events, fnt_grp=[(self.main_font,0)] ))
		self.keylist.bind('<Control-equal>', partial(font_events, fnt_grp=[(self.main_font, 0)] ))
		self.keylist.bind('<Control-minus>', partial(font_events, fnt_grp=[(self.main_font, 0)] ))
		self.keylist.bind('<Control-0>', partial(font_events, fnt_grp=[(self.main_font, 0)], f_size=self.main_font.cget('size') ))
		self.keylist.bind('<Control-c>', partial(tkcopy, widget=self.keylist))
		#create vertical scroll bar
		self.v_scrl1 = tk.Scrollbar(self.root, orient='vertical')
		self.v_scrl1.config(command=self.keylist.yview)
		self.v_scrl1.grid(column=1, row=1, rowspan=2, sticky=(tk.N,tk.S,tk.E,tk.W))
		#create horizontal scroll bar
		self.h_scrl1 = tk.Scrollbar(self.root, orient='horizontal')
		self.h_scrl1.config(command=self.keylist.xview)
		self.h_scrl1.grid(column=0, row=2, sticky=(tk.N,tk.S,tk.E,tk.W))
		#attach scrollbars
		self.keylist.config(yscrollcommand=self.v_scrl1.set)
		self.keylist.config(xscrollcommand=self.h_scrl1.set)

		#create info bar
		self.infobar = tk.Label(self.root, font=self.main_font, text='Showing 0 of 0 records\trecord 0 selected', anchor='w', bd=2, relief='sunken')
		self.infobar.grid(column=0, row=3, columnspan=2, sticky=(tk.N, tk.S, tk.E, tk.W))
		self.set_infobar()

		#popup menu
		self.context_menu = DefaultContextMenu(self.keylist, tearoff=0, font=self.main_font)
		self.context_menu.setup(dfpaste=False, dfcancel=False, dfcut=False)
		self.keylist.bind('<Button-3>', self.context_menu.popup)
				
	def populate(self, filepath):
		'''
		Open shelf file specified in filepath and populate listbox with
		  keys found within.  Also populate self.shelfkeys and
		  self.__selected_shelf_file.

		  If the path is not to a valid shelf, an error will be returned.

		  Parameters:

		  	filepath : str
		  		string containing path to a validshelf file.  

		'''

		self.shelfkeys = []
		self.__selected_shelf_file = filepath
		if whichdb(os.path.splitext(filepath)[0]) != None or '':
			self.current_shelf = os.path.splitext(filepath)[0]  #make compatible with dumbdbm
		else:
			self.current_shelf = filepath

		try:
			with shelve.open(self.current_shelf) as s:
				self.shelfkeys = [i for i in s]
			self.shelfkeys.sort()
			self.file_label.configure(text='Displaying shelf:        ' + self.current_shelf)
			self.reset_list(populate=True)
		except Exception as err:
			errmsg = 'Error opening file, please select a valid shelf file.\n\nException of type {0} occurred.\n{1!r}'.format(type(err).__name__, err.args)
			messagebox.showwarning('File open error...', errmsg)
			return 'break'

		self.filter_list()

	def reset_list(self, populate=False):
		'''
		Clear listbox and populate if parameter is set to True

		Parameters:

			populate : Bool
				=False	only clear the list 		(default)
				=True 	populate list with full contents of self.shelfkeys
		'''
		self.keylist.delete(0, tk.END)
		if populate == True:
			self.keylist.insert(tk.END, *self.shelfkeys)
			self.colour_items()
		self.set_infobar()
		return

	def colour_items(self):
		'''Colour items in listbox in alternate colours'''
		l = range(0, self.keylist.size())
		for i in l[0::2]:
			self.keylist.itemconfig(i, bg='white')
		for i in l[1::2]:
			self.keylist.itemconfig(i, bg='#EBF4FA') #light blue

	def set_infobar(self, *args):
		'''Populate information bar with details about list items. See class doc.'''
		if len(self.keylist.curselection()) == 0:
			curselect = '0'
		else:
			curselect = self.keylist.curselection()[0] + 1

		txt = 'Showing {0} of {1} records.\tRecord {2} selected.'.format(
				self.keylist.size(),
				len(self.shelfkeys),
				curselect
				)
		self.infobar.config(text=txt)

	def filter_list(self, *args):
		'''Apply search filter to listbox.  Can be triggered by event''' 
		search_text = self.search_string.get()
		self.reset_list()

		if len(search_text) == 0 or self.target_find.active.get() == 0 or self.search_check_val.get() == 1:
 			self.reset_list(populate=True)	#insert all		
		else:
			for i in self.shelfkeys:
				if search_text in i:
					self.keylist.insert(tk.END, i)
		self.colour_items()
		self.set_infobar()
		return 'break'

	def selected_key(self):
		'''Return index of currently selected listbox item.'''
		item_index = self.keylist.curselection()[0]
		shelf_key = self.keylist.get(item_index)
		return shelf_key

	def sendto_target(self, target=None):
		'''
		Retreive value from the the current shelf file according to the 
		currently selected key in listbox.  Call target display handler
		with .populate command, passing the retreived value.

		If no target display handler is passed as a parameter, construct
		tk.Toplevel() window and create a ResultsPane() and FindEntry()
		objects to pass the value to.

		Parameters:
			target : ResultsPane() or other display handler

		'''
		if target == None:
			tl = tk.Toplevel()
			tl.title(self.selected_key())
			tl.wm_geometry("800x600")
			tl.rowconfigure(1, weight=1)
			tl.columnconfigure(0, weight=1)
			frame1 = tk.Frame(tl)
			frame1.grid(row=0, column=0, sticky=(tk.N,tk.S,tk.E,tk.W))
			frame1.rowconfigure(0, weight=1)
			frame1.columnconfigure(0, weight=1)			
			frame2 = tk.Frame(tl)
			frame2.rowconfigure(1, weight=1)			
			frame2.columnconfigure(0, weight=1)			
			frame2.grid(row=1, column=0, sticky=(tk.N,tk.S,tk.E,tk.W))
			searchbox = FindEntry(frame1, self.main_font)
			target = ResultsPane(frame2, self.main_font, searchbox)
		
		with shelve.open(self.current_shelf) as s:
			target.populate(s[self.selected_key()])

	def get_shelf_details(self, mode='p'):
		'''
		Retreive details about the currently selected shelf and return
		as either a List or Dict object.

		See class doc for more details.

		Parameters:

			mode : str(1)		(default)
				='p'	return list of formatted values
				='d'	return dict of raw values

		 '''

		d = {}  #dictionary with raw data
		p = []

		try:		
			st = os.stat(self.__selected_shelf_file)
			#shelf name:
			n = 'file name'
			v = os.path.basename(self.__selected_shelf_file)
			d[n] = v
			p.append((n,v))
			#dir name
			n = 'directory name'
			v = os.path.dirname(self.__selected_shelf_file)
			d[n] = v
			p.append((n,v))
			#full path
			n = 'full path'
			v = os.path.abspath(self.__selected_shelf_file)
			d[n] = v
			p.append((n,v))
			#dbm schema
			n = 'dbm schema'
			v = whichdb(self.current_shelf)
			d[n] = v
			p.append((n,v))
			#file size
			n = 'file size'
			v = st[stat.ST_SIZE]
			d[n] = v
			p.append((n,'{:,.2f} MiB'.format(v/1024/1024)))
			#created
			n = 'created'
			v = st[stat.ST_CTIME]
			d[n] = v
			p.append((n,'{}'.format(asctime(localtime(v)))))
			#modified
			n = 'modified'
			v = st[stat.ST_MTIME]
			d[n] = v
			p.append((n,'{}'.format(asctime(localtime(v)))))
			#accessed
			n = 'accessed'
			v = st[stat.ST_ATIME]
			d[n] = v
			p.append((n,'{}'.format(asctime(localtime(v)))))
		except Exception as err:
			n = 'no file info found\n\nError type:  {0}\n{1}'.format(type(err).__name__, err.args)
			v = ''
			d[n] = v
			p.append((n,v))

		if mode == 'p':
			return p
		else:
			return d

	def convert_to_dumb(self):
		'''Generate copy of current_shelf in dbm.dumb format'''

		new_dbpath = '{0}_{1}'.format(self.current_shelf, strftime("%Y%m%d_%H%M%S"))
		msgtxt = '<empty>'

		w = whichdb(self.current_shelf) 
		if w is None or w == '':
			msgtxt = 'Current file does not appear to be a dbm file. Cancelling operation'
		elif w == 'dbm.dumb':
			msgtxt = 'Current shelf is already dbm.dumb format.  No coversion needed.'
		else:
			try:
				cs = shelve.open(self.current_shelf)
				ndb = shelve.Shelf(dumb.open(new_dbpath)) 
				for k in cs.keys():
					ndb[k] = cs[k]
				cs.close()
				ndb.close()
				msgtxt = 'New portable shelf file output as:\r\n{}'.format(new_dbpath)
			except Exception as err:
				msgtxt = 'Error while creating new shelf file. Attempt made to create:\r\n{0}'
				msgtxt += '\n\nError of type {1} occurred.\n{2}'
				msgtxt = msgtxt.format(new_dbpath, type(err).__name__, err.args)

		messagebox.showinfo('Operation summary', msgtxt)

	#event handlers
	def item_delete(self, evt):
		'''
		Delete key/value from current_shelf corresponding to the 
		currently selected key in listbox

		'''
		conf = messagebox.askokcancel(title="Delete shelf item...", 
			       message="Are you sure you want to permanently delete this shelf item?\n" + self.selected_key())
		if conf is True:
			with shelve.open(self.current_shelf) as s:
				del s[self.selected_key()]
			self.shelfkeys.remove(self.selected_key())
			self.keylist.delete(self.keylist.curselection()[0])
			self.target_pane.clear_all()
		self.colour_items()
		self.set_infobar()

	def item_select(self, evt):
		'''Triggers sendto_target() when listbox selection changes'''
		if self.keylist.size() < 1:
			pass
		else:
			self.sendto_target(target=self.target_pane)
		return 'break'

	def expand_result(self, evt):
		'''Triggers sendto_target() when listbox item is doubleclicked''' 
		if self.keylist.size() < 1:
			pass
		else:
			self.sendto_target()
		return 'break'

	def search_check_change(self, *args):
		'''Disables or Enables filtering when 'disable filter' checkbox changes'''
		if self.search_check_val.get() == 1:
			self.reset_list(populate=True)
		else:
			self.filter_list()


class ResultsPane():
	'''
	Create flexible display pane for values to be passed to .populate method

	This class creates a read only ScrolledText object in which to 
	display a text version of any input values that are passed to the
	.populate method.  It contains functionlity to handle specific content 
	in an intelligent way <TO BE IMPROVED LATER> and offers a small 
	summary pane and text search/highlighting functionality.

	At the time of writing, there is special handling for List, Tuple and 
	requests.Response objects which are passed in.

	Attributes:
		
		root : tk.Tk() or other tkinter frame object
			a frame or window in which to place the Entry widget

	Methods:

		populate(self, content_in)
			clears textboxes and populates them with content passed in
			the content_in parameter. All input is displayed in __str__ 
			format with some special handling possibly applied by the 
			format_content() method (see below) when inserted into
			the main scrolledtext box.  

			In the case of a list or tuple being passed in content_in,
			each separate element will be accessed and displayed as a 
			separate input in different sections of scrolledtext as 
			ELEMENT 1, ELEMENT 2 ..... ELEMENT X.  Each element is
			added as an entry in the popup menu to allow the user
			to easily see how many elements and jump to their chosen 
			one.

			All hyperlinks detected in the result will be underlined
			and will be clickable to open in a browser. 

		format_content(self, content)  -> str
			returns the object passed in the content parameter 
			formatted as a str. The function is intended to be
			expanded to handle some content in a more sophisticated
			way depending on the evolution of the application.

			At the time of writing, the fucntion contains special handling
			for requests.Response objects. It will retreive primarily 
			return Response.text but also adds some useful detail from 
			other parameters of the object.
				
		search_highlight(self, *args)
			searches the content of scrolledtext and adds formatted tags
			where a matching string is found. Creates a floating frame
			with x/x and next/prev buttons to iterate through and sets
			the user's view of the textbox to the first instance.

			this function should be improved in the future to accept
			search inquries from other sources (eg. a preset search 
			as a menu item as well as just the target_find  value).

		iterate_highlights(self, evt=None, direction=None, highlight_tag=None, result_tag=None)
			changes from the current search result to the next or previous
			result (eg from 1/10 to 2/10), changing the highlight colour of
			the 'current' instance and sets the users view of the scrolledtext.

		clear_all(self)
			clears the content from all objects in the ResultsPane class.

		jumpto(self, element)
			moves the users view of the scrolledtext to the index passed
			in the element parameter.

		resize_fonts(self, f_size)
			calls general set_fonts function to resize all fonts used in the
			class, accounting for offsets in size where some fonts should
			always be bigger or smaller relative to self.main_font.

		hide_search_results(self, evt)
			hides the floating frame with search result stats and next/prev
			buttons.  Currently does NOT cancel highlighting in the textbox
			but this may be desired functionality to add in the future.

	'''
	def __init__(self, parent, fnt=None, target_find=None):
		'''
		Initiate ResultsPane() objects, define layout and set event bindings.

		Parameters:

			parent : tk.Tk()
				frame or Tk() window in which to place listbox and other widgets

			fnt : tk.Font()
				a default font for use or derivation throughout.
				if fnt=None, a default font of size 8 will be defined.

			target_find : FindEntry()
				FindEntry() object which will be accessed for filter criteria.

		'''

		self.root = parent
		#self.popup_default_items = 0
		#setup fonts:
		#main font is a separate copy of the application font (want to control it independently)
		self.fonts = []
		if fnt == None:
			self.main_font = tkfnt.Font()
		else:
			self.main_font = fnt.copy()
		self.fonts.append({'font':self.main_font, 'offset':0})		#main font takes position 0 in list
		#header font is for section header on multi-object results 
		self.fnt_offset = 1  #will always be bigger than the main font by 1
		self.section_hdr_font = self.main_font.copy()
		self.section_hdr_font.configure(weight='bold', size=self.fonts[0]['font'].cget('size') + self.fnt_offset)
		self.fonts.append({'font':self.section_hdr_font, 'offset':self.fnt_offset})

		#if search entry is defined, setup trigger to capture change events 
		if target_find:
			self.target_find = target_find
			self.search_string = self.target_find.search_string
			self.search_string.trace('w', self.search_highlight)

		#configure empty header box
		self.header_box = tk.Text(self.root, font=self.main_font, height=3)
		self.header_box.grid(column=0, row=0, sticky=(tk.N,tk.S,tk.E,tk.W))
		self.header_box.insert(tk.END, 'nothing to display')
		self.header_box.configure(state='disable')
		self.header_box.bind('<Button-1>', set_widget_focus)

		#configure main results pane
		self.resultspane = scrolledtext.ScrolledText(self.root, width=20, height=10, font=self.main_font)
		self.resultspane.grid(column=0, row=1, sticky=(tk.N,tk.S,tk.E,tk.W))
		self.resultspane.configure(state='disable')
		self.resultspane.bind('<Button-1>', tktext_cancel_sel, add='+')
		self.resultspane.bind('<Button-1>', set_widget_focus, add='+')
		self.resultspane.bind('<Control-a>', tk_selectall)
		self.resultspane.bind('<Control-plus>', partial(font_events, fnt_grp=[(f['font'], f['offset']) for f in self.fonts] ))
		self.resultspane.bind('<Control-equal>', partial(font_events, fnt_grp=[(f['font'], f['offset']) for f in self.fonts] ))
		self.resultspane.bind('<Control-minus>', partial(font_events, fnt_grp=[(f['font'], f['offset']) for f in self.fonts] ))
		self.resultspane.bind('<Control-0>', partial( font_events, 
													  fnt_grp=[(f['font'], f['offset']) for f in self.fonts], 
													  f_size=self.fonts[0]['font'].cget('size'))
													)
		#self.resultspane.bind('<Key>', print_key)  #just to test function is triggering

		# configure search results box:
		# In order to place widgets centrally, surround them with empty row/columns and set the
		# empty columns to weight=1 with column/rowconfigure.  The column/row with widgets in should 
		# not have weights.
		self.search_results = tk.Frame(self.root, bg='white', borderwidth=2, relief='groove')
		self.search_results.grid(column=0, row=1, sticky=(tk.NE), padx=25, pady=10, ipadx=5, ipady=5)
		self.search_results.rowconfigure(0, weight=1)
		self.search_results.rowconfigure(2, weight=1)
		self.search_results.columnconfigure(0, weight=1)
		self.search_results.columnconfigure(6, weight=1)
		self.sr_label = tk.Label(self.search_results, text='0 / 0', font=self.main_font, bg='white', padx=10)
		self.sr_label.grid(column=1, row=1, sticky=(tk.N, tk.S, tk.E, tk.W))
		self.sr_next = tk.Button(self.search_results, text='next', font=self.main_font, bg='white', padx=10)
		self.sr_next.grid(column=4, row=1, sticky=(tk.N, tk.S, tk.E, tk.W))
		self.sr_div = tk.Frame(self.search_results, bg='white', width=5)
		self.sr_div.grid(column=3, row=1, sticky=(tk.N, tk.S, tk.E, tk.W), )
		self.sr_prev = tk.Button(self.search_results, text='prev', font=self.main_font, bg='white', padx=10)
		self.sr_prev.grid(column=2, row=1, sticky=(tk.N, tk.S, tk.E, tk.W))
		self.sr_hide = tk.Label(self.search_results, text='x', font=self.main_font, bg='white', padx=10, fg='red')
		self.sr_hide.grid(column=5, row=1, sticky=(tk.E))
		self.sr_hide.bind("<Button-1>", self.hide_search_results)
		self.search_results.grid_remove()

		#popup menu
		self.context_menu = DefaultContextMenu(self.resultspane, tearoff=0, font=self.main_font)
		self.context_menu.setup(dfpaste=False, dfcut=False)
		self.resultspane.bind('<Button-3>', self.context_menu.popup)


	def populate(self, content_in):
		'''
		Populate ResultsPane() text boxes with string representation of content_in

		Parameters:

			content_in : <any object>
				content which will be converted to str format and displayed
				in the text boxes provided by the class.

		'''
		#clear content
		self.clear_all()
		self.context_menu.add_separator()
		
		#add summary to header pane
		self.header_box.configure(state='normal')
		self.header_box.delete(1.0, tk.END)
		self.header_box.insert(tk.END, str(type(content_in)) + ':\n   ' + str(content_in))
		self.header_box.tag_add('x', 2.0, tk.END)
		self.header_box.tag_config('x', foreground='blue')
		self.header_box.configure(state='disable')

		#print details in detail pane
		self.resultspane.configure(state='normal')
		if type(content_in) in (list, tuple):
			for c, val in enumerate(content_in, 1):
				#determine current ending position of text, enter element header and set mark
				pos = self.resultspane.index("end-1c linestart")   #index always returns the next character - the next line in the case of an empty line
				element = 'ELEMENT' + str(c)
				self.resultspane.insert(tk.END, element + ':   ' + str(type(val)) + '\n')
				self.resultspane.tag_add(c, pos, self.resultspane.index('end-1c'))
				self.resultspane.tag_config(c, font=self.section_hdr_font)			
				self.resultspane.mark_set(element, pos)
				self.context_menu.add_command(label=element, command=partial(self.jumpto, element))
				#get content and print to body of text box
				val = self.format_content(val)
				self.resultspane.insert(tk.END, str(val) + '\n')
				self.resultspane.insert(tk.END, '\n'*5 + '-'*50 + '\n\n')
		else:
			self.resultspane.insert(tk.END, self.format_content(content_in))
		self.resultspane.configure(state='disabled')

		#run search highlighting in case there is a search string entered
		self.search_highlight()

		#mark hyperlinks and add callbacks for cursor and to open browser.
		c = tk.IntVar()
		start_index = '1.0'
		while start_index:
			c.set(0)
			url_regex = r'(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?'  #i still don't really understand this regex.  thanks stackoverflow
			match_index = self.resultspane.search(url_regex, start_index, stopindex=tk.END, nocase=1, count=c, regexp=True)
			if not match_index:
				break
			end_index = match_index + '+' + str(c.get()) + 'c'  #eg 2.0+12c  means "index 2.0 plus 12 characters"
			url_text = self.resultspane.get(match_index, end_index)
			self.resultspane.tag_add(url_text, match_index, end_index)
			self.resultspane.tag_config(url_text, underline=1)
			self.resultspane.tag_bind(url_text, '<Button-1>', partial(goto_url, url=url_text))
			self.resultspane.tag_bind(url_text, '<Enter>', partial(url_cursor))
			self.resultspane.tag_bind(url_text, '<Leave>', partial(url_cursor))
			start_index = end_index

	def format_content(self, content):
		'''
		Format content as str and return.  Apply some special handling.

		Parameters:

			content : <any object>
				any object that needs to be formatted as string for return
				to the calling program.

		'''  
		if type(content) == requests.models.Response:
			r = content
			#content.encoding='windows-1252' (used for testing)
			val = ''
			val += '  url:		' + r.url + '\n'
			val += '  encoding:		' + r.encoding + '\n'
			val += '  status_code:		' + str(r.status_code) + '\n'
			val += '\n\n'
			val += 'Showing prettified version of content:\n\n' + BeautifulSoup(r.text, 'lxml').prettify()
		#elif:  !other content handling goes here (eg. html, dict)
		else:
			val = str(content)
		
		return val

	def search_highlight(self, *args):
		'''Add highlights to scrolledtext for search matches''' 
		highlight_tag = 'search_highlights'
		result_tag = 'search_result'
		self.sr_label.config(text='0 / 0')

		try:
			if self.target_find.active.get() == 0:
				self.search_results.grid_remove()
				return 'break'
		except Exception:
			pass
		try:
			find_val = self.search_string.get() 
		except:
			return 'break'	#stop execution if search string does not exist.

		self.resultspane.tag_delete(highlight_tag)
		self.resultspane.tag_delete(result_tag)
		if len(find_val) == 0:
			return 

		#highlight all instances of search result
		self.resultspane.tag_config(highlight_tag, background='yellow', borderwidth=4, relief='raised')
		self.resultspane.tag_config(result_tag, background='orange', borderwidth=4, relief='raised')
		c = tk.IntVar()
		start_index = '1.0'
		while start_index:
			c.set(0)
			match_index = self.resultspane.search(find_val, start_index, stopindex=tk.END, nocase=1, count=c, regexp=False)
			if not match_index:
				break
			end_index = match_index + '+' + str(c.get()) + 'c'  #eg 2.0+12c  means "index 2.0 plus 12 characters"
			self.resultspane.tag_add(highlight_tag, match_index, end_index)
			start_index = end_index

		self.sr_next.config(text='next', command=partial(self.iterate_highlights, direction='next', highlight_tag=highlight_tag, result_tag=result_tag))
		self.sr_prev.config(text='prev', command=partial(self.iterate_highlights, direction='prev', highlight_tag=highlight_tag, result_tag=result_tag))
		if self.target_find:
			self.target_find.find_entry.bind('<Return>', partial(self.iterate_highlights, direction='next', highlight_tag=highlight_tag, result_tag=result_tag))
		self.search_results.grid()

		self.iterate_highlights(direction='next', highlight_tag=highlight_tag, result_tag=result_tag)

	def iterate_highlights(self, evt=None, direction=None, highlight_tag=None, result_tag=None):
		'''
		Iterate through existing search matches, adjusting highlight colours and position
		
		Parameters:

			direction : str
				direction ('next' or 'prev' to move highlighting to)

			highlight_tag : str
				highlighted tags to iterate through
				this was added to make this function more flexible in the future

			result_tag : str
				tag representing "current match" to colour differently

		''' 
		try:  
			#find indexes of current highlights if they exist
			start_index=self.resultspane.tag_ranges(result_tag)[0]
			end_index=self.resultspane.tag_ranges(result_tag)[1]

			#remove current tag if it exists
			self.resultspane.tag_remove(result_tag, start_index, end_index)

			#find next instance of highlight to move to (see docs on tag_ranges to understand this):
			if direction == 'prev':
				increment = -2
			else:
				increment = 2
			start_pos = self.resultspane.tag_ranges(highlight_tag).index(start_index) + increment
			new_start_index = self.resultspane.tag_ranges(highlight_tag)[start_pos]
			new_end_index = self.resultspane.tag_ranges(highlight_tag)[start_pos+1]
		except IndexError:
			#if no currently selected highlight was found, an IndexError will occur and the except will check that some search
			#results exist and either break (if not or start from the beginning)
			if len(self.resultspane.tag_ranges(highlight_tag)) == 0:
				return 'break'
			else:
				new_start_index = self.resultspane.tag_ranges(highlight_tag)[0]
				new_end_index = self.resultspane.tag_ranges(highlight_tag)[1]

		#highlight new result which is in focus
		self.resultspane.tag_add(result_tag, new_start_index, new_end_index)
		self.resultspane.see(new_start_index)

		#set results number label
		l = self.resultspane.tag_ranges(highlight_tag)[::2] #get only start positions (slice notation [::2] is start index:end index:STEP)
		self.sr_label.config(text=str(l.index(new_start_index)+1) + ' / ' + str(len(l)))

	def clear_all(self):
		'''Clear data from all objects in the ResultsPane() class'''
		self.context_menu.reset()
		self.resultspane.configure(state='normal')		
		self.resultspane.delete(1.0, tk.END)
		self.resultspane.configure(state='disabled')
		self.header_box.configure(state='normal')
		self.header_box.delete(1.0, tk.END)
		self.header_box.configure(state='disable')

		#clear tags and marks
		for t in self.resultspane.tag_names():
			self.resultspane.tag_delete(t)
		for m in self.resultspane.mark_names():
			self.resultspane.mark_unset(m)

	def jumpto(self, element):
		'''
		Move user's view of scrolledtext to index passed in element parameter

		Parameters:

			element : str
				string representing text mark name to jump to
		'''
		self.resultspane.see(element)
		return 'break'

	def resize_fonts(self, f_size):
		''' Call set_fonts function for all fonts in the class'''
		for f in self.fonts:
			set_fonts(f['font'], f_size+f['offset'])

	#event handlers
	def hide_search_results(self, evt):
		'''Hide floating search results frame'''
		self.search_results.grid_remove()
		return 'break'


if __name__ == '__main__':

	if os.name == 'nt':		#ensure acceptable font rendering in windows 10 by handing DPI
		from ctypes import windll
		try:
			windll.shcore.SetProcessDpiAwareness(1)
		except Exception:
			pass

	root = tk.Tk()
	ShelfBrowser(root)
	root.mainloop()