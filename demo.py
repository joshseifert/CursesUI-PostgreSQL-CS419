#!/usr/bin/env python

import npyscreen
		
class ConnectForm(npyscreen.ActionForm, npyscreen.SplitForm):
	def create(self):
		self.dbname = self.add(npyscreen.TitleText, begin_entry_at=24, name="Database Name:")
		self.dbuser = self.add(npyscreen.TitleText, begin_entry_at=24, name="Database User:")
		self.dbpass = self.add(npyscreen.TitleText, begin_entry_at=24, name="Database Password:")
		
	def on_ok(self):		
		npyscreen.notify_confirm("Successfully connected to the database!","Connected", editw=1)
		self.parentApp.setNextForm('MAINMENU')
		
	def on_cancel(self):
		exiting = npyscreen.notify_yes_no("Are you sure you want to quit?","Cancel?")
		if exiting:
			npyscreen.notify_confirm("Goodbye!")
			self.parentApp.setNextForm(None)
		else:
			npyscreen.notify_confirm("Carry on, as you were.", "Back to it!")

class MainForm(npyscreen.FormWithMenus):
	def create(self):
		self.menu = self.new_menu(name="Main Menu", shortcut='m')
		self.menu.addItem("Structure", self.structure, "s")
		self.menu.addItem("SQL Runner", self.sql_run, "q")
		self.menu.addItem("Browse", self.browse, "b")
		self.menu.addItem("Quit Application", self.exit_form, "^X")
		
	def structure(self):
		#form = 'STRUCTURE'
		#self.parentApp.switchForm(form)
		npyscreen.notify_confirm("TO DO: Structure Window.", editw=1)
		
	def sql_run(self):
		form = 'SQL_RUN'
		self.parentApp.switchForm(form)
		#npyscreen.notify_confirm("TO DO: SQL Run Window.", editw=1)
		
	def browse(self):
		#form = 'BROWSE'
		#self.parentApp.switchForm(form)
		npyscreen.notify_confirm("TO DO: Browse Window.", editw=1)
	
	def exit_form(self):
		exiting = npyscreen.notify_yes_no("Are you sure you want to quit?","Quit?")
		if exiting:
			npyscreen.notify_confirm("Goodbye!")
			self.parentApp.switchForm(None)
		else:
			pass

class SQLForm(npyscreen.SplitForm, MainForm): #inheriting MainForm makes menu option appear, but menu is empty....
	def create(self):
		SQL_command = self.add(npyscreen.MultiLineEditableBoxed, name="SQL Command:", max_height=8, max_width=75, scroll_exit=True, edit=True)
	
	def afterEditing(self):
		self.parentApp.setNextForm('MAINMENU')
		
class BrowseForm(npyscreen.Form):
	pass
	
class StructureForm(npyscreen.Form):
	pass
			
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