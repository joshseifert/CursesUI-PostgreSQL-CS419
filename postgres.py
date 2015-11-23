import psycopg2
import npyscreen

class PostgreSQL():
	def __init__(self, database, user, password, host, port):
		self.conn = psycopg2.connect(database=database, 
			user=user, 
			password=password, 
			host=host, 
			port=port)
		c = self.conn.cursor()
		c.execute("ROLLBACK;")
		c.close()

################################################################
# TABLE FUNCTIONS
################################################################		
		
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
			# rows = []
			# rows.append(colnames)
			# for result in results:
			# 	rows.append(list(result))
			return colnames, results
		except Exception, e:
			npyscreen.notify_confirm("e: %s" % e)
			c.execute("ROLLBACK;")			
		finally:
			c.close()	
		
	def browse_table(self, table_name):
		try:
			c = self.conn.cursor()
			c.execute("SELECT * FROM %s ORDER BY 1 ASC;" % table_name)
			colnames = [desc[0] for desc in c.description]
			results = c.fetchall()
			rows = []
			#rows.append(colnames)
			for result in results:
				rows.append(list(result))
			return colnames, rows
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

################################################################
# COLUMN FUNCTIONS
################################################################

	def delete_column(self, table_name, column_values):
		column_name = column_values[0]
		query_string = 'ALTER TABLE ' + table_name + ' DROP COLUMN ' + column_name + ';'

		try:
			c = self.conn.cursor()
			c.execute(query_string)
			npyscreen.notify_confirm('Field deleted.')
		except Exception, e:
			npyscreen.notify_confirm('e: %s' % e)
			c.execute('ROLLBACK;')
		finally:
			c.close()

	#def edit_column(self, table_name, old_column_values, new_column_values):

	def add_column(self, table_name, column_values):
		# unpack column values for code clarity
		self.name = column_values[0]
		self.datatype = column_values[1]
		self.collation = column_values[2]
		self.nullable = column_values[3]
		self.default = column_values[4]

		query_string = 'ALTER TABLE ' + table_name + ' ADD COLUMN'
		query_string += ' ' + self.name + ' ' + self.datatype

		if self.default:
			query_string += ' ' + self.default

		# this may not be applicable for adding a new column...
		if self.collation:
			query_string += ' ' + self.collation

		if self.nullable == 'NO':
			query_string += ' NOT NULL'

		query_string += ';'

		npyscreen.notify_confirm(query_string) # debug

		try:
			c = self.conn.cursor()
			c.execute(query_string)
			npyscreen.notify_confirm('Field added.')
		except Exception, e:
			npyscreen.notify_confirm('e: %s' % e)
			c.execute('ROLLBACK;')
		finally:
			c.close()


################################################################
# ROW FUNCTIONS
################################################################
			
	def delete_row(self, table_name, columns, values):
		query_string = '('
		for x in range(0, len(columns)):
			query_string += (columns[x] + " = '" + str(values[x]) + "' AND ")
		query_string = "DELETE FROM %s WHERE " % table_name + query_string[:-5] + ');'	
		npyscreen.notify_confirm(query_string) # debug
		
		try:
			c = self.conn.cursor()
			c.execute(query_string)
			npyscreen.notify_confirm("Row deleted.")
		except Exception, e:
			npyscreen.notify_confirm("e: %s" % e)
			c.execute("ROLLBACK;")
		finally:
			c.close()
			
	def edit_row(self, table_name, columns, new_values, old_values):

		#This part is just building the query string
		query_string = "UPDATE %s SET " % table_name
		for x in range(0, len(columns)):
			query_string += (columns[x] + " = '" + str(new_values[x]) + "', ")
		query_string = query_string[:-2] + ' WHERE ('
		for x in range(0, len(columns)):
			query_string += (columns[x] + " = '" + str(old_values[x]) + "' AND ")
		query_string = query_string[:-5] + ');'

		npyscreen.notify_confirm(query_string) # debug

		try:
			c = self.conn.cursor()
			c.execute(query_string)
			npyscreen.notify_confirm("Row updated.")
		except Exception, e:
			npyscreen.notify_confirm("e: %s" % e)
			c.execute("ROLLBACK;")
		finally:
			c.close() 

			
	def add_row(self, table_name, columns, new_values):
		query_string = "INSERT INTO %s (" % table_name
		for x in range(0, len(columns)):
			query_string += (str(columns[x])) + ","
		query_string = query_string[:-1] + ") VALUES ('"
		for x in range(0, len(columns)):
			query_string += (str(new_values[x])) + "','"
		query_string = query_string[:-2] + ");"
		
		npyscreen.notify_confirm(query_string) # debug
		
		try:
			c = self.conn.cursor()
			c.execute(query_string)
			npyscreen.notify_confirm("Row added.")
		except Exception, e:
			npyscreen.notify_confirm("e: %s" % e)
			c.execute("ROLLBACK;")
		finally:
			c.close()

################################################################
# UTILITY FUNCTIONS
################################################################

	def get_col_type(self, table_name):
		try:
			c = self.conn.cursor()
			c.execute("SELECT data_type FROM \
				information_schema.columns WHERE table_name = '%s';" % table_name)
			results = c.fetchall()
			rows = []
			for result in results:
				rows.append(list(result))
			# npyscreen.notify_confirm(str(rows)) # Debug
			return rows
		except Exception, e:
			npyscreen.notify_confirm("e: %s" % e)
			c.execute("ROLLBACK;")			
		finally:
			c.close()	

	def run_sql(self, query, return_flag):
		if query:			
			try:
				c = self.conn.cursor()			
				c.execute(query)
				
				if query[:6].upper() in ['INSERT','UPDATE','DELETE']:
					row_count = c.rowcount
					npyscreen.notify_confirm("Successful " + query[0:6] + " on %s rows" % row_count)
				
				if return_flag:
					# http://stackoverflow.com/questions/10252247/how-do-i-get-a-list-of-column-names-from-a-psycopg2-cursor
					colnames = [desc[0] for desc in c.description]
					results = c.fetchall()
					return colnames, results
				else:
					return
			except Exception, e:
				# psql transactions posted after a failed transaction
				# on the same cxn will fail if the original transaction 
				# is not rolled back first
				# http://stackoverflow.com/questions/10399727/psqlexception-current-transaction-is-aborted-commands-ignored-until-end-of-tra			
				npyscreen.notify_confirm("e: %s" % e)
				c.execute("ROLLBACK;")			
			finally:
				c.close()	
