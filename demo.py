#!/usr/bin/env python

import npyscreen
import psycopg2
from math import ceil

# Changed this to make it more object-oriented, in case we do MySQL later...
class PostgreSQL():
	def __init__(self, database, user, password, host, port):
		self.conn = psycopg2.connect(database=database, 
			user=user, 
			password=password, 
			host=host, 
			port=port)
			
	def run_sql(self, query):
		pass # Optional, if we want to refactor to be more OO
		
	def table_structure(self, table_name):
		try:
			c = self.conn.cursor()
			#https://docs.oracle.com/cd/E17952_01/refman-5.0-en/columns-table.html
			#Trying to formulate this based on the PHPMyAdmin screen, it doesn't all fit horizontally. Make it vertical?
			c.execute("SELECT column_name, data_type, \
				collation_name, is_nullable, column_default FROM \
				information_schema.columns WHERE table_name = '%s';" % table_name)
			colnames = [desc[0] for desc in c.description]
			results = c.fetchall()
			return colnames, results
		except Exception, e:
			npyscreen.notify_confirm("e: %s" % e)
			c.execute("ROLLBACK;")			
		finally:
			c.close()	
		
	def browse_table(self, table_name):
		try:
			c = self.conn.cursor()
			c.execute("SELECT * FROM %s;" % table_name)
			colnames = [desc[0] for desc in c.description]
			results = c.fetchall()
			return colnames, results
		except Exception, e:
			npyscreen.notify_confirm("e: %s" % e)
			c.execute("ROLLBACK;")			
		finally:
			c.close()
			
	def get_table_list(self):
		try:
			# http://www.linuxscrew.com/2009/07/03/postgresql-show-tables-show-databases-show-columns/
			c = self.conn.cursor()
			c.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
			result = c.fetchall()
			tables = []
			for table in result:
				tables.append(str(table).split("'")[1])	
			return tables
		except Exception, e:
			npyscreen.notify_confirm("e: %s" % e)
			c.execute("ROLLBACK;")
		finally:
			c.close()

"""
This is the first page the user will encounter. It prompts them to enter the database information.
The values of "myapp" and "dbpass" are part of the vagrantfile, so I made them the default values. I believe
that vagrantfile defines the default host as something other than 5432, but that port defaults to whatever
port vagrant actually uses, and 5432 is a standard value, so I'm leaving it as it. I'm honestly not super 
sure why the host needs to be 0.0.0.0...I got that just from googling. Psycopg says it uses "UNIX socket"
(whatever that means) but I don't think it works on VMs.
"""
class ConnectForm(npyscreen.ActionForm, npyscreen.SplitForm):

	OK_BUTTON_TEXT = "Connect"	# Reposition, rename buttons to indicate functionality
	OK_BUTTON_BR_OFFSET = (2, 15)
	CANCEL_BUTTON_TEXT = "Quit"
	CANCEL_BUTTON_BR_OFFSET = (2, 8)
	
	def create(self):
		self.dbname = self.add(npyscreen.TitleText, begin_entry_at=24, name="Database Name:", value="myapp")
		self.dbuser = self.add(npyscreen.TitleText, begin_entry_at=24, name="Database User:", value="myapp")
		self.dbpass = self.add(npyscreen.TitleText, begin_entry_at=24, name="Database Password:", value="dbpass")
		self.dbhost = self.add(npyscreen.TitleText, begin_entry_at=24, name="Database Host:", value="127.0.0.1")
		self.dbport = self.add(npyscreen.TitleText, begin_entry_at=24, name="Database Port:", value="15432")

	#Connect to the database using psycopg2 library. Reference: http://initd.org/psycopg/docs/module.html#psycopg2.connect
	def on_ok(self):
		try:
			self.parentApp.psql = PostgreSQL(self.dbname.value, self.dbuser.value, self.dbpass.value, self.dbhost.value, self.dbport.value)
			#self.parentApp.psql = psycopg2.connect(database=self.dbname.value, user=self.dbuser.value, password=self.dbpass.value, host=self.dbhost.value, port=self.dbport.value)
			npyscreen.notify_confirm("Successfully connected to the database!","Connected", editw=1)
			self.parentApp.setNextForm('MAINMENU')
		except:
			npyscreen.notify_confirm("Error: Could not connect to database. If you are unsure, do not alter the Host or Port values.")
			self.parentApp.setNextForm('MAIN')

	def on_cancel(self):
		exiting = npyscreen.notify_yes_no("Are you sure you want to quit?","Cancel?")
		if exiting:
			npyscreen.notify_confirm("Goodbye!")
			self.parentApp.setNextForm(None)
		else:
			npyscreen.notify_confirm("Please enter login information.", "Back to it!")
			
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
			self.parentApp.switchForm(None)
		else:
			pass
			
	def close_menu(self):
		pass


class SQLForm(npyscreen.SplitForm, MainForm):
	OK_BUTTON_TEXT = "Run Query"
	OK_BUTTON_BR_OFFSET = (18, 6)

	MAX_PAGE_SIZE = 10

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
			#	psql stmt execution
			c = self.parentApp.psql.conn.cursor()
			c.execute(self.SQL_command.value)
			
			# http://stackoverflow.com/questions/10252247/how-do-i-get-a-list-of-column-names-from-a-psycopg2-cursor
			self.colnames = [desc[0] for desc in c.description]
			self.results = c.fetchall()
			
			# pagination
			self.page = 0
			self.total_pages = int(ceil(len(self.results) / float(self.results_per_page)))
			self.displayResultsGrid(self.page)

			# psql stmt close
			c.close()

			
		except Exception, e:
			npyscreen.notify_confirm("e: %s" % e)
			
			# psql transactions posted after a failed transaction
			# on the same cxn will fail if the original transaction 
			# is not rolled back first
			# http://stackoverflow.com/questions/10399727/psqlexception-current-transaction-is-aborted-commands-ignored-until-end-of-tra
			c.execute("ROLLBACK;")
			c.close()
			
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
				
		self.table_list.values = self.parentApp.psql.get_table_list()
		self.table_list.display()
		
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
			#	psql stmt execution
			self.colnames, self.results = self.parentApp.psql.browse_table(self.value)

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
	
	
class StructureForm(npyscreen.SplitForm, MainForm):
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
	
		self.next_page_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[Next]', relx=-13, rely=-5)
		self.next_page_btn.whenPressed = self.nextPage

		self.prev_page_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[Prev]', relx=-23, rely=-5)
		self.prev_page_btn.whenPressed = self.prevPage
		
	def beforeEditing(self):
		self.name = "Structure of Table %s" % self.value
		try:
			#	psql stmt execution
			self.colnames, self.results = self.parentApp.psql.table_structure(self.value)

			# pagination
			self.page = 0
			self.total_pages = int(ceil(len(self.results) / float(self.MAX_PAGE_SIZE)))
			self.displayResultsGrid(self.page)
			
		except Exception, e:
			npyscreen.notify_confirm("e: %s" % e)
			
	def afterEditing(self):
		self.parentApp.setNextForm('MAINMENU')

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
		self.SQL_display.values = []
		for result in self.results[start:end]:
			row = []
			for i in xrange(0, len(self.colnames)):
				row.append(result[i])
			self.SQL_display.values.append(row)
		

			
class App(npyscreen.NPSAppManaged):
	def onStart(self):
		self.addForm('MAIN', ConnectForm, name="Connect to your postgreSQL database!", draw_line_at = 22)
		self.addForm('MAINMENU', MainForm, name="Open the Menu to view available actions.")
		self.addForm('SQL_RUN', SQLForm, name="SQL Runner", draw_line_at = 8)
		self.addForm('CHOOSE', ChooseTableForm, name="Choose a table")
		self.addForm('BROWSE', BrowseForm, name="Browse")
		self.addForm('STRUCTURE', StructureForm, name="Structure")

if __name__ == "__main__":
	app = App().run()
	print "Thanks, goodbye!"