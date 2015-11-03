#!/usr/bin/env python

import npyscreen
import psycopg2
from math import ceil

# make the database connection var global?
# psql = None

"""
This is the first page the user will encounter. It prompts them to enter the database information.
The values of "myapp" and "dbpass" are part of the vagrantfile, so I made them the default values. I believe
that vagrantfile defines the default host as something other than 5432, but that port defaults to whatever
port vagrant actually uses, and 5432 is a standard value, so I'm leaving it as it. I'm honestly not super 
sure why the host needs to be 0.0.0.0...I got that just from googling. Psycopg says it uses "UNIX socket"
(whatever that means) but I don't think it works on VMs.
"""
class ConnectForm(npyscreen.ActionForm, npyscreen.SplitForm):

	OK_BUTTON_TEXT = "Connect"	# The text is too long. Find out how to reposition these buttons. relx, rely?
	CANCEL_BUTTON_TEXT = "Quit"
	
	def create(self):
		self.dbname = self.add(npyscreen.TitleText, begin_entry_at=24, name="Database Name:", value="myapp")
		self.dbuser = self.add(npyscreen.TitleText, begin_entry_at=24, name="Database User:", value="myapp")
		self.dbpass = self.add(npyscreen.TitleText, begin_entry_at=24, name="Database Password:", value="dbpass")
		self.dbhost = self.add(npyscreen.TitleText, begin_entry_at=24, name="Database Host:", value="127.0.0.1")
		self.dbport = self.add(npyscreen.TitleText, begin_entry_at=24, name="Database Port:", value="15432")

	#Connect to the database using psycopg2 library. Reference: http://initd.org/psycopg/docs/module.html#psycopg2.connect
	def on_ok(self):
		try:
			self.parentApp.psql = psycopg2.connect(database=self.dbname.value, user=self.dbuser.value, password=self.dbpass.value, host=self.dbhost.value, port=self.dbport.value)
			#global psql
			#psql = psycopg2.connect(database=self.dbname.value, user=self.dbuser.value, password=self.dbpass.value, host=self.dbhost.value, port=self.dbport.value)
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
		form = 'STRUCTURE'
		self.parentApp.switchForm(form)
		
	def sql_run(self):
		form = 'SQL_RUN'
		self.parentApp.switchForm(form)
		
	def browse(self):
		form = 'BROWSE'
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
	OK_BUTTON_BR_OFFSET = (15, 6)

	MAX_PAGE_SIZE = 7

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
		self.SQL_display = self.add(npyscreen.GridColTitles, max_height=9, editable=False, rely=(self.get_half_way() + 1))
	
		self.next_page_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[Next]', relx=-13, rely=-3)
		self.next_page_btn.whenPressed = self.nextPage

		self.prev_page_btn = self.add(npyscreen.ButtonPress, max_width=10, name='[Prev]', relx=-23, rely=-3)
		self.prev_page_btn.whenPressed = self.prevPage


	def afterEditing(self):
		try:
			#	psql stmt execution
			c = self.parentApp.psql.cursor()
			c.execute(self.SQL_command.value)
			
			# http://stackoverflow.com/questions/10252247/how-do-i-get-a-list-of-column-names-from-a-psycopg2-cursor
			self.colnames = [desc[0] for desc in c.description]
			self.results = c.fetchall()
			
			# pagination
			self.page = 0
			self.total_pages = int(ceil(len(self.results) / float(self.MAX_PAGE_SIZE)))
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

	def nextPage(self):
		self.page += 1
		self.displayResultsGrid(self.page)
		self.SQL_display.update(clear=False)
		self.display()

	def prevPage(self):
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


class BrowseForm(npyscreen.SplitForm, MainForm):
	OK_BUTTON_TEXT = "Back to Main Menu"
	def create(self):
		self.menu = self.new_menu(name="Main Menu", shortcut='m')
		self.menu.addItem("Structure", self.structure, "s")
		self.menu.addItem("SQL Runner", self.sql_run, "q")
		self.menu.addItem("Browse", self.browse, "b")
		self.menu.addItem("Close Menu", self.close_menu, "c")
	
	# Query DB for list of tables.
	def beforeEditing(self):
		try:
			npyscreen.notify_confirm("self.parentApp.psql = %s" % self.parentApp.psql)
			c = self.parentApp.psql.cursor()
			npyscreen.notify_confirm("c = %s" % c)
			# http://www.linuxscrew.com/2009/07/03/postgresql-show-tables-show-databases-show-columns/
			# SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
			c.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
			result = c.fetchall()
			for each_line in result:
				npyscreen.notify_confirm(each_line)
			#npyscreen.notify_confirm(result)
		except:
			npyscreen.notify_confirm("Error. Werp. :(")

	def afterEditing(self):
		self.parentApp.setNextForm('MAINMENU')
	
class StructureForm(npyscreen.SplitForm, MainForm):
	OK_BUTTON_TEXT = "Back to Main Menu"
	def create(self):
		self.menu = self.new_menu(name="Main Menu", shortcut='m')
		self.menu.addItem("Structure", self.structure, "s")
		self.menu.addItem("SQL Runner", self.sql_run, "q")
		self.menu.addItem("Browse", self.browse, "b")
		self.menu.addItem("Close Menu", self.close_menu, "^c")
		
	def afterEditing(self):
		self.parentApp.setNextForm('MAINMENU')
			
class App(npyscreen.NPSAppManaged):
	def onStart(self):
		self.addForm('MAIN', ConnectForm, name="Connect to your postgreSQL database!", columns=80, lines=25, draw_line_at = 22)
		self.addForm('MAINMENU', MainForm, name="Open the Menu to view available actions.", columns=80, lines=25)
		self.addForm('SQL_RUN', SQLForm, name="SQL Runner", columns=80, lines=25)
		self.addForm('BROWSE', BrowseForm, name="Browse a table", columns=80, lines=25)
		self.addForm('STRUCTURE', StructureForm, name="Structure", columns=80, lines=25)

if __name__ == "__main__":
	app = App().run()
	print "Thanks, goodbye!"