#!/usr/bin/env python

import npyscreen
import psycopg2

# make the database connection var global?
psql = None


class ConnectForm(npyscreen.ActionForm, npyscreen.SplitForm):
	OK_BUTTON_TEXT = "Connect"	# The text is too long. Find out how to reposition these buttons. relx, rely?
	CANCEL_BUTTON_TEXT = "Quit"
	def create(self):
		self.dbname = self.add(npyscreen.TitleText, begin_entry_at=24, name="Database Name:", value="myapp")
		self.dbuser = self.add(npyscreen.TitleText, begin_entry_at=24, name="Database User:", value="myapp")
		self.dbpass = self.add(npyscreen.TitleText, begin_entry_at=24, name="Database Password:", value="dbpass")
		self.dbhost = self.add(npyscreen.TitleText, begin_entry_at=24, name="Database Host:", value="0.0.0.0")
		self.dbport = self.add(npyscreen.TitleText, begin_entry_at=24, name="Database Port:", value="5432")

	#Connect to the database using psycopg2 library. Reference: http://initd.org/psycopg/docs/module.html#psycopg2.connect
	def on_ok(self):
		try:
			psql = psycopg2.connect(database=self.dbname.value, user=self.dbuser.value, password=self.dbpass.value, host=self.dbhost.value, port=self.dbport.value)
			npyscreen.notify_confirm("Successfully connected to the database!","Connected", editw=1)
			self.parentApp.setNextForm('MAINMENU')
		except:
			npyscreen.notify_confirm("Error: self.dbname = %s, self.dbuser = %s, self.dbpass = %s" % (self.dbname.value, self.dbuser.value, self.dbpass.value))
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
	OK_BUTTON_TEXT = "Back to Main Menu"
	def create(self):
		self.menu = self.new_menu(name="Main Menu", shortcut='m')
		self.menu.addItem("Structure", self.structure, "s")
		self.menu.addItem("SQL Runner", self.sql_run, "q")
		self.menu.addItem("Browse", self.browse, "b")
		self.menu.addItem("Close Menu", self.close_menu, "^c")
		SQL_command = self.add(npyscreen.MultiLineEditableBoxed, name="SQL Command:", max_height=8, max_width=75, scroll_exit=True, edit=True)
	
	def afterEditing(self):
		self.parentApp.setNextForm('MAINMENU')
		
class BrowseForm(npyscreen.SplitForm, MainForm):
	OK_BUTTON_TEXT = "Back to Main Menu"
	def create(self):
		self.menu = self.new_menu(name="Main Menu", shortcut='m')
		self.menu.addItem("Structure", self.structure, "s")
		self.menu.addItem("SQL Runner", self.sql_run, "q")
		self.menu.addItem("Browse", self.browse, "b")
		self.menu.addItem("Close Menu", self.close_menu, "^c")

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