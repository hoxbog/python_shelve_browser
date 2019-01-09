# python_shelve_browser
Python tkinter program to quickly view contents of a shelve file

Written and tested on Python 3.5;  tested on Linux (ubuntu 16.04 LTS) and Windows 10.

Required Python Modules:
	math
	os
	functools
	time
	shelve	
	requests
	bs4
	webbrowser
	dbm
	tkinter

DESCRIPTION
	This is a small project primarily undertaken for the purpose of learning
	tkinter but solving a real need to quickly access and view the 
	contents of shelf files created by the shelve module.  The application 
	is currently meant purely to provide a quick read-only look at the 
	contents and not to offer more extensive interactions with the shelf file. 

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
    
    
