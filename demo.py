#!/usr/bin/env python

import npyscreen
from postgres import *
from math import ceil

################################################################
# CONNECT FORM
################################################################

class ConnectForm(npyscreen.ActionForm, npyscreen.SplitForm):

	OK_BUTTON_TEXT = "Quit"	# Reposition, rename buttons to indicate functionality
	OK_BUTTON_BR_OFFSET = (2, 8)
	CANCEL_BUTTON_TEXT = "Connect"
	CANCEL_BUTTON_BR_OFFSET = (2, 15)
	ALLOW_RESIZE = False
	
	def create(self):		
		self.dbname = self.add(npyscreen.TitleText, begin_entry_at=24, name="Database Name:", value="myapp")
		self.dbuser = self.add(npyscreen.TitleText, begin_entry_at=24, name="Database User:", value="myapp")
		self.dbpass = self.add(npyscreen.TitleText, begin_entry_at=24, name="Database Password:", value="dbpass")
		self.dbhost = self.add(npyscreen.TitleText, begin_entry_at=24, name="Database Host:", value="127.0.0.1")
		self.dbport = self.add(npyscreen.TitleText, begin_entry_at=24, name="Database Port:", value="15432")

	#Connect to the database using psycopg2 library. Reference: http://initd.org/psycopg/docs/module.html#psycopg2.connect
	
	# Want the application to tab to "connect" before it tabs to "quit". Because npyscreen ALWAYS tabs to "cancel" before "ok",
	# simply changed the function names around, so that "cancel" connects and "ok" quits.
	def on_cancel(self):
		try:
			self.parentApp.sql = PostgreSQL(self.dbname.value, self.dbuser.value, self.dbpass.value, self.dbhost.value, self.dbport.value)
			npyscreen.notify_confirm("Successfully connected to the database!","Connected", editw=1)
			self.parentApp.setNextForm('MAINMENU')
		except:
			npyscreen.notify_confirm("Error: Could not connect to database. If you are unsure, do not alter the Host or Port values.")
			self.parentApp.setNextForm('MAIN')

	def on_ok(self):
		exiting = npyscreen.notify_yes_no("Are you sure you want to quit?","Cancel?")
		if exiting:
			npyscreen.notify_confirm("Goodbye!")
			self.parentApp.setNextForm(None)
		else:
			npyscreen.notify_confirm("Please enter login information.", "Back to it!")

################################################################
# MAIN TITLE SCREEN
################################################################

class MainForm(npyscreen.FormWithMenus):

	def create(self):
		self.menu = self.new_menu(name="Main Menu", shortcut='m')
		self.menu.addItem("Structure", self.structure, "s")
		self.menu.addItem("SQL Runner", self.sql_run, "q")
		self.menu.addItem("Browse", self.browse, "b")
		self.menu.addItem("Close Menu", self.close_menu, "c")
		self.menu.addItem("Quit Application", self.exit_form, "^X")
		
		# This is ugly. I really just want something here to take up space, so it isn't a bit empty screen. ASCII art? 
		self.add(npyscreen.FixedText, value="NCurses-based database UI, Project for CS 419.")
		self.add(npyscreen.FixedText, rely = 5, value="Press ctrl-x to open the navigation window.")
		
	def on_ok(self):
		exiting = npyscreen.notify_yes_no("Are you sure you want to quit?","Quit?")
		if exiting:
			npyscreen.notify_confirm("Goodbye!")
			self.parentApp.switchForm(None)
		else:
			pass		
	
	def structure(self):
		form = 'CHOOSE'
		self.parentApp.action = 'c' # Keep track of if user wants to browse or view structure
		self.parentApp.switchForm(form)
		
	def sql_run(self):
		form = 'SQL_RUN'
		self.parentApp.switchForm(form)
		
	def browse(self):
		form = 'CHOOSE'
		self.parentApp.action = 'b'
		self.parentApp.switchForm(form)
	
	def exit_form(self):
		exiting = npyscreen.notify_yes_no("Are you sure you want to quit?","Quit?")
		if exiting:
			npyscreen.notify_confirm("Goodbye!")
			exit() #fixed the exit problem!
			#self.parentApp.switchForm(None)
		else:
			pass
			
	def close_menu(self):
		pass

################################################################
# SQL RUNNER FORM
################################################################

class SQLForm(npyscreen.SplitForm, MainForm):
	OK_BUTTON_TEXT = "Run Query"
	OK_BUTTON_BR_OFFSET = (18, 6)

	def create(self):

		# globals
		self.page = 0
		self.colnames = []
		self.results = []

		# menu items
		self.menu = self.new_menu(name="Main Menu", shortcut='m')
		self.menu.addItem("Structure", self.structure, "s")
		self.menu.addItem("SQL Runner", self.sql_run, "q")
		self.menu.addItem("Browse", self.browse, "b")
		self.menu.addItem("Close Menu", self.close_menu, "^c")
		self.menu.addItem("Quit Application", self.exit_form, "^X")
	
		# widgets
		self.SQL_command = self.add(npyscreen.MultiLineEdit, max_height=5, scroll_exit=True)
		self.results_per_page_title_text = self.add(npyscreen.TitleText, begin_entry_at=31, max_width=40, rely=7, name="# Results Per Page (Max 10):", value="10")
		self.SQL_display = self.add(npyscreen.GridColTitles, max_height=12, editable=False, rely=9)
	
		self.first_page_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[First]', relx=-43, rely=-3)
		self.first_page_btn.whenPressed = self.firstPage
	
		self.prev_page_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[Prev]', relx=-33, rely=-3)
		self.prev_page_btn.whenPressed = self.prevPage
	
		self.next_page_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[Next]', relx=-23, rely=-3)
		self.next_page_btn.whenPressed = self.nextPage
		
		self.last_page_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[Last]', relx=-13, rely=-3)
		self.last_page_btn.whenPressed = self.lastPage

	def afterEditing(self):
	
		# get # of rows per page
		try:
			self.results_per_page = int(self.results_per_page_title_text.value)
			if self.results_per_page < 1:
				self.results_per_page = 1
			elif self.results_per_page > 10:
				self.results_per_page = 10
		except:
			npyscreen.notify_confirm("Error: You may only display 1-10 results per page.")
			self.parentApp.switchForm('SQL_RUN')
			
		try:		
			#	sql stmt execution
			self.colnames, self.results = self.parentApp.sql.run_sql(self.SQL_command.value)
			
			# pagination
			self.page = 0
			self.total_pages = int(ceil(len(self.results) / float(self.results_per_page)))
			self.displayResultsGrid(self.page)
			
		except Exception, e:
			npyscreen.notify_confirm("e: %s" % e)
					
	def firstPage(self):
		self.page = 0
		self.displayResultsGrid(self.page)
		self.SQL_display.update(clear=False)
		self.display()
		
	def lastPage(self):
		self.page = self.total_pages - 1
		self.displayResultsGrid(self.page)
		self.SQL_display.update(clear=False)
		self.display()

	def nextPage(self):
		if self.page < self.total_pages - 1: # Only show pages that have data
			self.page += 1
		self.displayResultsGrid(self.page)
		self.SQL_display.update(clear=False)
		self.display()

	def prevPage(self):
		if self.page > 0: 
			self.page -= 1
		self.displayResultsGrid(self.page)
		self.SQL_display.update(clear=False)
		self.display()

	def displayResultsGrid(self, page):
		# column titles
		self.SQL_display.col_titles = self.colnames

		# pagination
		start = self.page * self.results_per_page
		end = start + self.results_per_page

		# grid results displayed from 2d array
		self.SQL_display.values = []
		for result in self.results[start:end]:
			row = []
			for i in xrange(0, len(self.colnames)):
				row.append(result[i])
			self.SQL_display.values.append(row)

################################################################
# TABLE LIST FORM
################################################################

class TableList(npyscreen.MultiLineAction):
    def actionHighlighted(self, act_on_this, keypress):
		if self.parent.parentApp.action == 'b':
			self.parent.parentApp.getForm('BROWSE').value = act_on_this
			self.parent.parentApp.switchForm('BROWSE') # implement some kind of logic here, so it can route to "Structure" form, too
		else:
			self.parent.parentApp.getForm('STRUCTURE').value = act_on_this
			self.parent.parentApp.switchForm('STRUCTURE')
			
class ChooseTableForm(npyscreen.ActionFormMinimal, MainForm):
	
	OK_BUTTON_TEXT = "Back to Main Menu"
		
	def create(self):
		self.menu = self.new_menu(name="Main Menu", shortcut='m')
		self.menu.addItem("Structure", self.structure, "s")
		self.menu.addItem("SQL Runner", self.sql_run, "q")
		self.menu.addItem("Browse", self.browse, "b")
		self.menu.addItem("Close Menu", self.close_menu, "^c")
		self.menu.addItem("Quit Application", self.exit_form, "^X")
				
		self.table_list = self.add(TableList, rely = 4, scroll_exit = True)
	
	#Pretty shamelessly stolen from http://npyscreen.readthedocs.org/example-addressbk.html
	def beforeEditing(self):
		if self.parentApp.action == 'b':
			self.parentApp.results_per_page = self.add(npyscreen.TitleText, begin_entry_at=31, rely = 2, name="# Results Per Page (Max 15):", value="15")
		#	if self.parentApp.results_per_page > 15 or self.parentApp..results_per_page < 1:
		#		npyscreen.notify_confirm("Error. Please enter a number between 1 - 15.")
				
		self.table_list.values = self.parentApp.sql.get_table_list()
		self.table_list.display()

################################################################
# BROWSE FORM
################################################################

class BrowseForm(npyscreen.ActionFormMinimal, MainForm):
	
	OK_BUTTON_TEXT = "Return to Main"
	MAX_PAGE_SIZE = 15

	def create(self):

		# globals
		self.page = 0
		self.colnames = []
		self.results = []

		# menu items
		self.menu = self.new_menu(name="Main Menu", shortcut='m')
		self.menu.addItem("Structure", self.structure, "s")
		self.menu.addItem("SQL Runner", self.sql_run, "q")
		self.menu.addItem("Browse", self.browse, "b")
		self.menu.addItem("Close Menu", self.close_menu, "^c")
		self.menu.addItem("Quit Application", self.exit_form, "^X")
	
		# widgets		
		self.SQL_display = self.add(npyscreen.GridColTitles, max_height=17, editable=False, rely=(2))
		
		self.first_page_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[First]', relx=-43, rely=-5)
		self.first_page_btn.whenPressed = self.firstPage
	
		self.prev_page_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[Prev]', relx=-33, rely=-5)
		self.prev_page_btn.whenPressed = self.prevPage
	
		self.next_page_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[Next]', relx=-23, rely=-5)
		self.next_page_btn.whenPressed = self.nextPage
		
		self.last_page_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[Last]', relx=-13, rely=-5)
		self.last_page_btn.whenPressed = self.lastPage
		
	def beforeEditing(self):
		try:
			self.parentApp.results_per_page = int(self.parentApp.results_per_page.value)
			if self.parentApp.results_per_page < 1:
				self.parentApp.results_per_page = 1
			elif self.parentApp.results_per_page > 15:
				self.parentApp.results_per_page = 15
		except:
			npyscreen.notify_confirm("Error: You may only display 1-15 results per page.")
			self.parentApp.switchForm('CHOOSE')
		
		self.name = "Browsing table %s" % self.value
		try:
			#	sql stmt execution
			self.colnames, self.results = self.parentApp.sql.browse_table(self.value)

			# pagination
			self.page = 0
			self.total_pages = int(ceil(len(self.results) / float(self.parentApp.results_per_page)))
			self.displayResultsGrid(self.page)
			
		except Exception, e:
			npyscreen.notify_confirm("e: %s" % e)
			
	def afterEditing(self):
		self.parentApp.setNextForm('MAINMENU')
		
	def firstPage(self):
		self.page = 0
		self.displayResultsGrid(self.page)
		self.SQL_display.update(clear=False)
		self.display()
		
	def lastPage(self):
		self.page = self.total_pages - 1
		self.displayResultsGrid(self.page)
		self.SQL_display.update(clear=False)
		self.display()
	
	def nextPage(self):
		if self.page < self.total_pages - 1:
			self.page += 1
		self.displayResultsGrid(self.page)
		self.SQL_display.update(clear=False)
		self.display()

	def prevPage(self):
		if self.page > 0:
			self.page -= 1
		self.displayResultsGrid(self.page)
		self.SQL_display.update(clear=False)
		self.display()

	def displayResultsGrid(self, page):
		# column titles
		self.SQL_display.col_titles = self.colnames

		# pagination
		start = self.page * self.parentApp.results_per_page
		end = start + self.parentApp.results_per_page
		# grid results displayed from 2d array
		self.SQL_display.values = []
		for result in self.results[start:end]:
			row = []
			for i in xrange(0, len(self.colnames)):
				row.append(result[i])
			self.SQL_display.values.append(row)
	
################################################################
# STRUCTURE FORM
################################################################

class StructureList(npyscreen.MultiLineAction):

	def display_value(self, v1):
		'''
		Bit of contra-intuitive magic here. The v1 values that get passed
		from wMain.values are not, in fact, a list of lists, but just a 
		bunch of pseudo related lists. So v[0] actually represents column 0
		for all rows (and will subsequently print out column 0 for all rows).

		This return statement creates a 20x wide left-justified column cell 
		for each column and displays it to the screen as a text field.

		'''
		colNum = len(v1)
		return '\n'.join(['%s' % str(v1[i]).ljust(20) for i in range(0, colNum)])

	def actionHighlighted(self, act_on_this, keypress):
		self.parent.parentApp.getForm('EDITRECORDFM').value = act_on_this
		self.parent.parentApp.switchForm('EDITRECORDFM')

class StructureForm(npyscreen.FormMutt, MainForm):
	MAIN_WIDGET_CLASS = StructureList

	def beforeEditing(self):
		self.update_list()

	def update_list(self):
		self.wMain.values = self.parentApp.sql.table_structure(self.value)
		self.wMain.display()

class EditRecord(npyscreen.ActionForm):
	def create(self):

		self.value = None
		self.wgNullable = self.add(npyscreen.TitleText, name="Nullable:")

		''' TODO: add the rest of the fields '''

	def on_ok(self):

		''' TODO: add code here to actually commit changes to db '''

		self.parentApp.switchForm('STRUCTURE')

	def on_cancel(self):
		self.parentApp.switchForm('STRUCTURE')



# class StructureForm(npyscreen.SplitForm, MainForm):

# 	OK_BUTTON_TEXT = "Return to Main"
# 	MAX_PAGE_SIZE = 15

# 	def create(self):

# 		# globals
# 		self.page = 0
# 		self.colnames = []
# 		self.results = []

# 		# menu items
# 		self.menu = self.new_menu(name="Main Menu", shortcut='m')
# 		self.menu.addItem("Structure", self.structure, "s")
# 		self.menu.addItem("SQL Runner", self.sql_run, "q")
# 		self.menu.addItem("Browse", self.browse, "b")
# 		self.menu.addItem("Close Menu", self.close_menu, "^c")
# 		self.menu.addItem("Quit Application", self.exit_form, "^X")
	
# 		# widgets
# 		self.SQL_display = self.add(npyscreen.GridColTitles, max_height=17, editable=False, rely=(2))
	
# 		self.next_page_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[Next]', relx=-13, rely=-5)
# 		self.next_page_btn.whenPressed = self.nextPage

# 		self.prev_page_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[Prev]', relx=-23, rely=-5)
# 		self.prev_page_btn.whenPressed = self.prevPage
		
# 	def beforeEditing(self):
# 		self.name = "Structure of Table %s" % self.value
# 		try:
# 			#	sql stmt execution
# 			self.colnames, self.results = self.parentApp.sql.table_structure(self.value)

# 			# pagination
# 			self.page = 0
# 			self.total_pages = int(ceil(len(self.results) / float(self.MAX_PAGE_SIZE)))
# 			self.displayResultsGrid(self.page)
			
# 		except Exception, e:
# 			npyscreen.notify_confirm("e: %s" % e)
			
# 	def afterEditing(self):
# 		self.parentApp.setNextForm('MAINMENU')

# 	def nextPage(self):
# 		if self.page < self.total_pages - 1:
# 			self.page += 1
# 		self.displayResultsGrid(self.page)
# 		self.SQL_display.update(clear=False)
# 		self.display()

# 	def prevPage(self):
# 		if self.page > 0:
# 			self.page -= 1
# 		self.displayResultsGrid(self.page)
# 		self.SQL_display.update(clear=False)
# 		self.display()

# 	def displayResultsGrid(self, page):

# 		# pagination
# 		start = self.page * self.MAX_PAGE_SIZE
# 		end = start + self.MAX_PAGE_SIZE

# 		# column titles
# 		self.SQL_display.col_titles = ['E', 'X'] + self.colnames

# 		# grid results displayed from 2d array
# 		columnNum = len(self.colnames)
# 		self.SQL_display.values = []
# 		for result in self.results[start:end]:
# 			row = []
# 			row.append()
# 			for i in xrange(0, columnNum):
# 				row.append(result[i])
# 			self.SQL_display.values.append(row)
		
################################################################
# APP SETUP
################################################################
			
class App(npyscreen.NPSAppManaged):
	def onStart(self):
		self.addForm('MAIN', ConnectForm, name="Connect to your postgreSQL database!", draw_line_at = 22)
		self.addForm('MAINMENU', MainForm, name="Open the Menu to view available actions.")
		self.addForm('SQL_RUN', SQLForm, name="SQL Runner", draw_line_at = 8)
		self.addForm('CHOOSE', ChooseTableForm, name="Choose a table")
		self.addForm('BROWSE', BrowseForm, name="Browse")
		self.addForm('STRUCTURE', StructureForm, name="Structure")
		self.addForm('EDITRECORDFM', EditRecord, name="EditRecord")

if __name__ == "__main__":
	app = App().run()
	print "Thanks, goodbye!"