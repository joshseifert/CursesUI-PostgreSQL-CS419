#!/usr/bin/env python

import curses
import npyscreen
from postgres import *
from math import ceil

################################################################
# CONNECT FORM
#
# This is the first form the user sees when they launch the
# application. It instructs them to enter in the information to 
# connect to a database. The default values are those that 
# connect to our VM-hosted database, when running this program 
# locally. 
################################################################

class ConnectForm(npyscreen.ActionForm, npyscreen.SplitForm):

	# Reposition, rename buttons to indicate functionality
	OK_BUTTON_TEXT = "Quit"	
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
	
	# npyscreen always tabs to the "cancel" button before the "ok" button. We want the program to tab to "connect" before 
	# "quit", so we overrode the on_cancel function to connect to the database, and the on_ok function to quit. We feel 
	# that this code, while somewhat counter-intuitive, provides a better experience for the user.
	
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
# 
# This is the landing screen once the user successfully connects
# to their database. It does not contain any database-specific
# functionality; instead, it provides the user with a brief 
# overview of the program, and tells them how to access the 
# navigation menu.
################################################################

class MainForm(npyscreen.FormWithMenus):

	OK_BUTTON_TEXT = ""

	def create(self):
		# The pop-up menu that is accessible from (almost) every other form.
		# This gets inherited by other forms so that the user can easily navigate between screens
		self.menu = self.new_menu(name="Main Menu", shortcut='m')
		self.menu.addItem("Structure", self.structure, "s")
		self.menu.addItem("SQL Runner", self.sql_run, "q")
		self.menu.addItem("Browse", self.browse, "b")
		self.menu.addItem("Close Menu", self.close_menu, "^c")
		self.menu.addItem("Quit Application", self.exit_form, "^X")
	
		# Description of our program for the user. 
		# ASCII art slightly modified from original at http://www.asciiworld.com/-Computers-.html
		self.add(npyscreen.MultiLineEdit, editable=False, value="\
                            ________________  Welcome!\n\
                           /               /| \n\
                          /_______________/ | This is an NCurses and \n\
    ________________      |  __________  |  | Npyscreen-based database UI\n\
   /               /|     | |          | |  | \n\
  /               / |     | | NCurses  | |  | Press ctrl-x to open the \n\
 /_______________/  |/\   | |          | |  | navigation window.\n\
(_______________(   |  \  | |__________| | /    \n\
(_______________(   |   \ |______________|/ ___/\ \n\
(_______________(  /     |____>______<_____/     \ \n\
(_______________( /     / = ==== ==== ==== /|    _|_ \n\
(   postgreSQL  (/     / ========= === ===/ /   //// \n\
(_______________      / ========= === ===/ /   /__/  \n\
                     <__________________<_/     \n\n\
			You may Browse tables in your database, viewing, selecting, editing, and \n\
			deleting individual rows. You may also view and edit the structure of \n\
			tables, and perform more complex queries with manual SQL commands.\n\n\
			This is a project for CS 419 - Group 9: \n\
					Josh Seifert, Emma Murray, Bailey Roe\n")
		
	# Allows the user to quit the program
	def on_ok(self):
		exiting = npyscreen.notify_yes_no("Are you sure you want to quit?","Quit?")
		if exiting:
			npyscreen.notify_confirm("Goodbye!")
			self.parentApp.switchForm(None)
		else:
			pass
			
	def sql_run(self):
		form = 'SQL_RUN'
		self.parentApp.switchForm(form)
		
	# If viewing either "Structure" or "Browse" page, need to select a table first, so 
	# switch to form where user selects a table. The "action" variable keeps track of 
	# which behavior the user wants from the selected table.
	
	def structure(self):
		form = 'CHOOSE'
		self.parentApp.action = 's'
		self.parentApp.switchForm(form)
		
	def browse(self):
		form = 'CHOOSE'
		self.parentApp.action = 'b'
		self.parentApp.switchForm(form)
	
	def exit_form(self):
		exiting = npyscreen.notify_yes_no("Are you sure you want to quit?","Quit?")
		if exiting:
			npyscreen.notify_confirm("Goodbye!")
			exit()
		else:
			pass
			
	def close_menu(self):
		pass

################################################################
# SQL RUNNER FORM
#
# This page is based on the SQL Runner from PHPMyAdmin. The user
# is provided an editable text box where they can enter in a SQL
# query and then run it. The results are then returned to the 
# user in the display on the bottom half of the screen. The user 
# has the option to display the number of results per page when 
# running the query, and can browse between pages of results once
# the query has been run.
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
	
		self.first_page_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[First]', relx=-43, rely=-3, editable=False)
		self.first_page_btn.whenPressed = self.firstPage
	
		self.prev_page_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[Prev]', relx=-33, rely=-3, editable=False)
		self.prev_page_btn.whenPressed = self.prevPage
	
		self.next_page_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[Next]', relx=-23, rely=-3, editable=False)
		self.next_page_btn.whenPressed = self.nextPage
		
		self.last_page_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[Last]', relx=-13, rely=-3, editable=False)
		self.last_page_btn.whenPressed = self.lastPage
		
	def afterEditing(self):
	
		# get # of rows per page. User is instructed to enter a number between 1-10.
		# If the user does not enter a number, they receive an error message. If they
		# attempt to enter a number less than 1 or greater than 10, the number is rounded 
		# to those respective bounds.
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
			# sql stmt execution
			if self.SQL_command.value != '':
				# Only select returns database results, second argument is a flag to return values
				if self.SQL_command.value[:6].upper() == 'SELECT':
					self.colnames, self.results = self.parentApp.sql.run_sql(self.SQL_command.value, True)
				else:
					self.parentApp.sql.run_sql(self.SQL_command.value, False)
			
				# pagination
				self.page = 0
				self.total_pages = int(ceil(len(self.results) / float(self.results_per_page)))
				self.displayResultsGrid(self.page)
				
				# User may select pagination buttons only once query is run
				self.first_page_btn.editable = True
				self.prev_page_btn.editable = True
				self.next_page_btn.editable = True
				self.last_page_btn.editable = True
			
		#except StopIteration:
		#	pass
		except Exception, e:			
			npyscreen.notify_confirm("e: %s" % e) #this is where the "nonetype object not iterable" error is being thrown. 
	
	# These are the functions of the pagination buttons
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
		# Only show pages that have data
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
# TABLE LIST WIDGET
#
# This is a custom widget that lists all of the tables in the 
# database. "act_on_this" and "keypress" are built-in functions 
# of npyscreen. act_on_this returns the value of the element (in
# this case, the table) the user selects.
################################################################

class TableList(npyscreen.MultiLineAction):
    def actionHighlighted(self, act_on_this, keypress):
		if self.parent.parentApp.action == 'b':
			self.parent.parentApp.getForm('BROWSE').value = act_on_this
			self.parent.parentApp.switchForm('BROWSE')
		else:
			self.parent.parentApp.getForm('STRUCTURE').value = act_on_this
			self.parent.parentApp.switchForm('STRUCTURE')

################################################################
# TABLE LIST FORM
#
# The bulk of this form is the custom widget, above. It displays 
# the available tables, and then navigates to the next form, 
# passing the values of the table the user selected, and whether 
# they want to browse, or view the structure of the table. If 
# the user wants to browse the table, this is also when they have 
# the option to select the number of results per page.
################################################################
			
class ChooseTableForm(npyscreen.ActionFormMinimal, MainForm):
	
	OK_BUTTON_TEXT = "Back to Main Menu"
	
	def on_ok(self):
		self.parentApp.switchForm('MAINMENU')
		
	def create(self):
		self.menu = self.new_menu(name="Main Menu", shortcut='m')
		self.menu.addItem("Structure", self.structure, "s")
		self.menu.addItem("SQL Runner", self.sql_run, "q")
		self.menu.addItem("Browse", self.browse, "b")
		self.menu.addItem("Close Menu", self.close_menu, "^c")
		self.menu.addItem("Quit Application", self.exit_form, "^X")
				
		self.table_list = self.add(TableList, rely = 4, scroll_exit = True)
	
	# Based on sample code from the official documentation at: http://npyscreen.readthedocs.org/example-addressbk.html
	def beforeEditing(self):
		if self.parentApp.action == 'b':
			self.parentApp.results_per_page = self.add(npyscreen.TitleText, begin_entry_at=31, rely = 2, name="# Results Per Page (Max 15):", value="15")	
		self.table_list.values = self.parentApp.sql.get_table_list()
		self.table_list.display()

################################################################
# BROWSE FORM
#
# This form has many features, but none are especially complicated.
# In addition to the pagination buttons, as seen in the SQL Runner
# page, this form has buttons to Add, Edit, and Delete rows from 
# the current table. Edit and Delete first verify that a row was 
# selected in the table. The tables are generated dynamically 
# based on the column names of the selected table, and by default
# are sorted in ascending order of the first column, which in most 
# cases will be an integer Primary Key.
################################################################

class BrowseForm(npyscreen.ActionFormMinimal, MainForm):
	
	OK_BUTTON_TEXT = "Return to Main"
	MAX_PAGE_SIZE = 15

	def on_ok(self):
		self.parentApp.switchForm('MAINMENU')
	
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
		self.SQL_display = self.add(npyscreen.SelectOne, max_height=17, editable=True, scroll_exit=True, select_whole_line=True, rely=(4))
		self.col_display = self.add(npyscreen.FixedText, rely=(2))
		
		self.add_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[Add]', relx=-73, rely=-5)
		self.add_btn.whenPressed = self.addRow
		
		self.edit_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[Edit]', relx=-63, rely=-5)
		self.edit_btn.whenPressed = self.editRow
		
		self.delete_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[Delete]', relx=-53, rely=-5)	
		self.delete_btn.whenPressed = self.deleteRow
		
		self.first_page_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[First]', relx=-73, rely=-3)
		self.first_page_btn.whenPressed = self.firstPage
	
		self.prev_page_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[Prev]', relx=-63, rely=-3)
		self.prev_page_btn.whenPressed = self.prevPage
	
		self.next_page_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[Next]', relx=-53, rely=-3)
		self.next_page_btn.whenPressed = self.nextPage
		
		self.last_page_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[Last]', relx=-43, rely=-3)
		self.last_page_btn.whenPressed = self.lastPage	
		
	# addRow and editRow call the same form. The only difference is that editRow
	# checks that a row was selected from the table (a row may be selected with
	# addRow, but it is ignored), and editRow also passes the current values of 
	# row to be edited.
	
	def addRow(self):
		self.parentApp.getForm('EDITROW').col_names = self.colnames
		self.parentApp.getForm('EDITROW').action = "add"
		self.parentApp.getForm('EDITROW').table_name = self.value
		self.parentApp.switchForm('EDITROW')
			
	def editRow(self):
		if self.SQL_display.value:
			self.parentApp.getForm('EDITROW').col_names = self.colnames
			self.parentApp.getForm('EDITROW').col_values = self.results[self.SQL_display.value[0]]
			self.parentApp.getForm('EDITROW').action = "edit"
			self.parentApp.getForm('EDITROW').table_name = self.value
			self.parentApp.switchForm('EDITROW')
		else:
			npyscreen.notify_confirm("Please select a row to edit.")
			
	# deleteRow is similar to editRow in that a row must be selected. It 
	# requires that the user confirms their desire to delete the row. It 
	# does not require traversing to a separate form.
	
	def deleteRow(self):
		if self.SQL_display.value:
			self.yesOrNo = npyscreen.notify_yes_no("You are about to delete a row. This action cannot be undone. Proceed?")
			if self.yesOrNo:
				# This passes the table name, column names, column values to the function that deletes the row.
				self.parentApp.sql.delete_row(self.value, self.colnames, self.results[self.SQL_display.value[0]]) 
				self.parentApp.switchForm('BROWSE')
			else:
				npyscreen.notify_confirm("Aborted. Your row was NOT deleted.")
		else:
			npyscreen.notify_confirm("Please select a row to delete.")
		
	def beforeEditing(self):
		try:
			self.parentApp.rows_per_page = int(self.parentApp.results_per_page.value)
			if self.parentApp.rows_per_page < 1:
				self.parentApp.rows_per_page = 1
			elif self.parentApp.rows_per_page > 15:
				self.parentApp.rows_per_page = 15
		except Exception as e:
			npyscreen.notify_confirm("Error: You may only display 1-15 results per page." + str(e))
			self.parentApp.switchForm('CHOOSE')
		
		self.name = "Browsing table %s" % self.value
		try:
			# sql stmt execution
			self.colnames, self.results = self.parentApp.sql.browse_table(self.value)
			
			col_names = ' ' * 3
			for x in range(0, len(self.colnames)):
				col_names += " | " + self.colnames[x]
			
			self.col_display.value = col_names

			# pagination
			self.page = 0
			self.total_pages = int(ceil(len(self.results) / float(self.parentApp.rows_per_page)))
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
		start = self.page * self.parentApp.rows_per_page
		end = start + self.parentApp.rows_per_page
		# grid results displayed from 2d array
		self.SQL_display.values = []
		for result in self.results[start:end]:
			row = []
			for i in xrange(0, len(self.colnames)):
				row.append(result[i])
			self.SQL_display.values.append(row)

################################################################
# EDIT ROW FORM
#
# This form has a lot going on, and unfortunately suffers from
# some convoluted logic, due to the restrictive nature of the
# npyscreen library, and poor documentation.
#
# The form retrieves the name of the columns, as well as their 
# data type, and presents them as a series of input fields. 
# Because these forms are generated at runtime, they are all
# strings. If the user is editing a row, the current values are 
# passed in as the default values. 
################################################################
			
class EditRowForm(npyscreen.ActionForm):
	def create(self):
		self.value = None

	def beforeEditing(self):
		
		# For a long time this was self.columns.
		# npyscreen fails to mention that this is a reserved name...
		self.cols = [] 
		yPos = 2
		
		self.col_types = (self.parentApp.sql.get_col_type(self.table_name))
		
		if self.action == 'edit':
			self.name = "Edit Row"
			for i, (a, b) in enumerate(zip(self.col_names, self.col_values)):
				#equivalent to self.cols[x] = self.add ...
				self.cols.append(self.add(npyscreen.TitleText, name = str(a) + " (" + str(self.col_types[i])[2:-2] + ")", value=str(b), rely = yPos, begin_entry_at=30))
				yPos += 1
		else:
			self.name = "Add Row"
			for i, a in enumerate(self.col_names):
				self.cols.append(self.add(npyscreen.TitleText, name = str(a) + " (" + str(self.col_types[i])[2:-2] + ")", rely = yPos, begin_entry_at=30))
				yPos += 1
		
		
	# Iffy solution to a problem here. Can't define the values of the widgets when the application starts, 
	# because each table will have different fields. So they have to go in beforeEditing. This copies them 
	# every time the form is called. Call the same form twice, you see each widget twice. Call any form 
	# enough times and the screen runs out of space and throws a fatal error.
	
	# self.cols is just a list of return values, if you delete them, the widgets are still part of the form. 
	# Per npyscreen documentation, you CANNOT delete widgets. The recommended solution was to make the widgets
	# hidden (invisible) and uneditable. This still makes them take up space on the form, so they are all "shoved"
	# into a tiny, overlapping, hidden box in the corner of the field, and the new widgets manually placed where the 
	# old widgets used to be. This is an inelegant solution, but a limitation of the npyscreen library.
		
	def afterEditing(self):
		if self.cols:
			for item in self.cols:
				item.rely=22
				item.relx=40
				item.hidden = True
				item.editable = False	
			
	def on_ok(self):
		self.new_values = []
		for item in self.cols:
			self.new_values.append(item.value)
		# if user is editing a row, pass table name, column names, old values and new values.
		# if user is adding a row, omit the old values.
		if self.action == "edit":
			self.parentApp.sql.edit_row(self.table_name, self.col_names, self.new_values, self.col_values)			
		else:
			self.parentApp.sql.add_row(self.table_name, self.col_names, self.new_values)
	
		self.parentApp.switchForm('BROWSE')

	def on_cancel(self):
		self.parentApp.switchForm('BROWSE')	
			

################################################################
# STRUCTURE FORM
#
# The structure form allows a user to add, edit or delete from 
# the structure of a table, meaning the fields and information 
# associated with the fields, as permitted by the underlying 
# database implementation.
################################################################

class StructureForm(npyscreen.ActionFormMinimal, MainForm):

	OK_BUTTON_TEXT = "Return to Main"
	MAX_PAGE_SIZE = 15

	def on_ok(self):
		self.parentApp.switchForm('MAINMENU')

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
		self.SQL_display = self.add(npyscreen.SelectOne, max_height=17, editable=True, scroll_exit=True, select_whole_line=True, rely=(4))
		self.col_display = self.add(npyscreen.FixedText, rely=(2))
		
		self.add_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[Add]', relx=-73, rely=-5)
		self.add_btn.whenPressed = self.addField
		
		self.edit_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[Edit]', relx=-63, rely=-5)
		self.edit_btn.whenPressed = self.editField
		
		self.delete_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[Delete]', relx=-53, rely=-5)	
		self.delete_btn.whenPressed = self.deleteField
		
		self.first_page_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[First]', relx=-73, rely=-3)
		self.first_page_btn.whenPressed = self.firstPage
	
		self.prev_page_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[Prev]', relx=-63, rely=-3)
		self.prev_page_btn.whenPressed = self.prevPage
	
		self.next_page_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[Next]', relx=-53, rely=-3)
		self.next_page_btn.whenPressed = self.nextPage
		
		self.last_page_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[Last]', relx=-43, rely=-3)
		self.last_page_btn.whenPressed = self.lastPage	

	def beforeEditing(self):
		self.name = "Structure of Table %s" % self.value

		try:
			#	sql stmt execution
			self.colnames, self.results = self.parentApp.sql.table_structure(self.value)

			col_names = ' ' * 3
			for x in range(0, len(self.colnames)):
				col_names += " | " + self.colnames[x]

			self.col_display.value = col_names

			# pagination
			self.page = 0
			self.total_pages = int(ceil(len(self.results) / float(self.MAX_PAGE_SIZE)))
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
		start = self.page * self.MAX_PAGE_SIZE
		end = start + self.MAX_PAGE_SIZE

		# grid results displayed from 2d array
		columnNum = len(self.colnames)
		self.SQL_display.values = []
		for result in self.results[start:end]:
			row = []
			for i in xrange(0, columnNum):
				row.append(result[i])
			self.SQL_display.values.append(row)

	# addField and editField call the same form. The only difference is that editField
	# checks that a field was selected from the table (a field may be selected with
	# addField, but it is ignored), and editField also passes the current values of 
	# row to be edited.
	
	def addField(self):
		self.parentApp.getForm('EDITFIELD').col_names = self.colnames
		self.parentApp.getForm('EDITFIELD').col_values = []
		self.parentApp.getForm('EDITFIELD').action = "add"
		self.parentApp.getForm('EDITFIELD').table_name = self.value
		self.parentApp.switchForm('EDITFIELD')
			
	def editField(self):
		if self.SQL_display.value:
			self.parentApp.getForm('EDITFIELD').col_names = self.colnames
			self.parentApp.getForm('EDITFIELD').col_values = self.results[self.SQL_display.value[0]]
			self.parentApp.getForm('EDITFIELD').action = "edit"
			self.parentApp.getForm('EDITFIELD').table_name = self.value
			self.parentApp.switchForm('EDITFIELD')
		else:
			npyscreen.notify_confirm("Please select a field to edit.")
			
	# deleteRow is similar to editRow in that a row must be selected. It 
	# requires that the user confirms their desire to delete the row. It 
	# does not require traversing to a separate form.
	
	def deleteField(self):
		if self.SQL_display.value:
			self.yesOrNo = npyscreen.notify_yes_no("You are about to delete a field. This action cannot be undone. Proceed?")
			if self.yesOrNo:
				# This passes the table name and column name to the column delete function
				column_values = self.results[self.SQL_display.value[0]]
				self.parentApp.sql.delete_column(self.value, column_values) 
				self.parentApp.switchForm('STRUCTURE')
			else:
				npyscreen.notify_confirm("Aborted. Your field was NOT deleted.")
		else:
			npyscreen.notify_confirm("Please select a field to delete.")

################################################################
# EDIT FIELD FORM
#
# Lets a user Add/Edit the information associated with a field
# in the database. Retrieves information about the selected field
# from col_values and uses it to prepopulate the form if the 
# user is editing a field, otherwise defaults all the form values.
################################################################
			
class EditFieldForm(npyscreen.ActionForm):
	def create(self):

		self.value = None
		self.wgColumnName = self.add(npyscreen.TitleText, name="Column Name: ")
			
		self.wgDataType = self.add(npyscreen.TitleSelectOne, max_height=5, value = [0,], name="Data Type: ",
          values = [
      "bigint",
			"bigserial",
			"bit varying",
			"boolean",
			"box",
			"bytea",
			"character varying",
			"cidr",
			"circle",
			"date",
			"double precision",
			"inet",
			"integer",
			"json",
			"jsonb",
			"line",
			"lseg",
			"macaddr",
			"money",
			"path",
			"pg_lsn",
			"point",
			"polygon",
			"real",
			"smallint",
			"smallserial",
			"text",
			"tsquery",
			"tsvector",
			"txid_snapshot",
			"uuid",
			"xml"], scroll_exit=True)

		self.wgCollationName = self.add(npyscreen.TitleText, name="Collation Name :")
		self.wgNullable = self.add(npyscreen.TitleSelectOne, max_height=4, value = [1,], name="Nullable: ",
          values = ["Yes","No"], scroll_exit=True)
		self.wgDefault = self.add(npyscreen.TitleText, name="Default: ")
		self.wgUnique = self.add(npyscreen.TitleSelectOne, max_height=4, value = [1,], name="Unique: ",
        	values = ["Yes","No"], scroll_exit=True)
		self.wgPrimaryKey = self.add(npyscreen.TitleSelectOne, max_height=4, value = [1,], name="Primary Key: ",
					values = ["Yes","No"], scroll_exit=True)

	def beforeEditing(self):

		# show field values if this is an edit form
		if self.col_values:
			self.wgColumnName.value = self.col_values[0]
			self.wgDataType.value = [self.wgDataType.values.index(self.col_values[1]),]
			self.wgCollationName.value = self.col_values[2]
			self.wgDefault.value = self.col_values[4]
		
			if self.col_values[3] == "YES":
				self.wgNullable.value = [0,]
			else:
				self.wgNullable.value = [1,]
				
		# otherwise, reset this form
		else:
			self.wgColumnName.value = ""
			self.wgDataType.value = [0,]
			self.wgCollationName.value = ""
			self.wgNullable.value = [1,]
			self.wgDefault.value = ""
			self.wgUnique.value = [1,]
			self.wgPrimaryKey.value = [1,]

	def on_ok(self):

		# get new values from the form - we need to be able to compare with
		# old values to determine what has changed
		self.new_values = {}
		if self.wgColumnName.value == '':
			npyscreen.notify_confirm("Column name is a required field.")
			return
		self.new_values['colname'] = self.wgColumnName.value
		self.new_values['datatype'] = self.wgDataType.values[self.wgDataType.value[0]]
		self.new_values['collation'] = self.wgCollationName.value
		self.new_values['nullable'] = self.wgNullable.value
		self.new_values['default'] = self.wgDefault.value
		self.new_values['unique'] = self.wgUnique.value
		self.new_values['pk'] = self.wgPrimaryKey.value

		if self.action == 'add':
			self.parentApp.sql.add_column(self.table_name, self.new_values)

		self.parentApp.switchForm('STRUCTURE')

	def on_cancel(self):
		self.parentApp.switchForm('STRUCTURE')	
		
################################################################
# APP SETUP
#
# The NPSAppManaged class is built-in to npyscreen. It registers
# all the forms (screens) the user sees. The first screen must 
# have the name 'MAIN', so our ConnectForm (where the user 
# connects to the database) is called 'MAIN', while our actual 
# main page is called 'MAINMENU'
################################################################
			
class App(npyscreen.NPSAppManaged):
	def onStart(self):
		self.addForm('MAIN', ConnectForm, name="Connect to your postgreSQL database!", draw_line_at = 22)
		self.addForm('MAINMENU', MainForm, name="Open the Menu to view available actions.")
		self.addForm('SQL_RUN', SQLForm, name="SQL Runner", draw_line_at = 8)
		self.addForm('CHOOSE', ChooseTableForm, name="Choose a table")
		self.addForm('BROWSE', BrowseForm, name="Browse")
		self.addForm('STRUCTURE', StructureForm, name="Structure")
		#self.addForm('EDITSTRUCTUREFM', EditStructure, name="EditStructure")
		self.addForm('EDITROW', EditRowForm, name="Edit Row")
		self.addForm('EDITFIELD', EditFieldForm, name="Edit Field")
		#self.addForm('EDITBROWSEFM', EditBrowse, name="EditBrowse")

if __name__ == "__main__":
	app = App().run()
	print "Thanks, goodbye!"