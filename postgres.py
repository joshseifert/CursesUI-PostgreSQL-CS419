import psycopg2
import npyscreen

from psycopg2.extensions import AsIs

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
			# http://www.postgresql.org/docs/9.1/static/information-schema.html
			# http://dba.stackexchange.com/questions/32975/error-could-not-find-array-type-for-datatype-information-schema-sql-identifier
			# retreive column and key column usage metadata
			query_string = 'SELECT c.column_name, c.data_type, c.collation_name, \
			c.is_nullable, c.column_default, array_agg(cc.constraint_type::text) AS constraints\
			FROM information_schema.columns c\
			LEFT JOIN ( \
				SELECT tc.constraint_type, kcu.column_name \
				FROM information_schema.table_constraints tc \
				JOIN information_schema.key_column_usage kcu \
					ON tc.constraint_catalog = kcu.constraint_catalog \
					AND tc.constraint_schema = kcu.constraint_schema \
					AND tc.constraint_name = kcu.constraint_name \
				WHERE tc.constraint_type = \'PRIMARY KEY\' \
					OR tc.constraint_type = \'UNIQUE\' \
			) AS cc \
				ON c.column_name = cc.column_name \
			WHERE c.table_name = \'%s\' \
			GROUP BY c.column_name, c.data_type, c.collation_name, \
			c.is_nullable, c.column_default;' % table_name

			c.execute(query_string)
			colnames = [desc[0] for desc in c.description]
			results = c.fetchall()

			npyscreen.notify_confirm('%s' % results)

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
		# try:
		# 	c = self.conn.cursor()

		# 	if column_values['collation']:
		# 		npyscreen.notify_confirm('creation w/ collation sql') #debug
		# 		c.execute('ALTER TABLE ' + table_name + ' ADD COLUMN %s %s COLLATE %s;', (AsIs(column_values['colname']), AsIs(column_values['datatype']), AsIs(column_values['collation'])))
		# 	else:
		# 		npyscreen.notify_confirm('creation sql') #debug
		# 		c.execute('ALTER TABLE ' + table_name + ' ADD COLUMN %s %s;', (AsIs(column_values['colname']), AsIs(column_values['datatype'])))

		# 	if column_values['nullable'] == [1]:
		# 		npyscreen.notify_confirm('null sql') #debug
		# 		c.execute('ALTER TABLE ' + table_name + ' ALTER COLUMN %s SET NOT NULL;', (AsIs(column_values['colname']),))
				
		# 	if column_values['default']:
		# 		npyscreen.notify_confirm('default sql') #debug
		# 		c.execute('ALTER TABLE ' + table_name + ' ALTER COLUMN %s SET DEFAULT %s;', (AsIs(column_values['colname']), column_values['default']))
				
		# 	if column_values['unique'] == [0]:
		# 		npyscreen.notify_confirm('unique sql') #debug
		# 		c.execute('ALTER TABLE ' + table_name + ' ADD UNIQUE (%s);', (AsIs(column_values['colname']),))
				
		# 	if primarykey and column_values['pk'] == [0]:
		# 		npyscreen.notify_confirm('Add column aborted. You already have a primary \
		# 		key set on the %s field.' % primarykey[0])
		# 		return
		# 	elif column_values['pk'] == [0]:
		# 		npyscreen.notify_confirm('pk sql') #debug
		# 		c.execute('ALTER TABLE ' + table_name + ' ADD PRIMARY KEY (%s);', (AsIs(column_values['colname']),))

		# 	npyscreen.notify_confirm('Field added.')
		# except Exception, e:
		# 	npyscreen.notify_confirm('e: %s' % e)
		# 	c.execute('ROLLBACK;')
		# finally:
		# 	c.close()

	def add_column(self, table_name, column_values):

		# determines if there is already a primary key on the table
		query_getpk_string = 'SELECT kcu.column_name \
				FROM information_schema.table_constraints tc \
				JOIN information_schema.key_column_usage kcu \
					ON tc.constraint_catalog = kcu.constraint_catalog \
					AND tc.constraint_schema = kcu.constraint_schema \
					AND tc.constraint_name = kcu.constraint_name \
				WHERE tc.constraint_type = \'PRIMARY KEY\' \
					AND tc.table_name = \'%s\';' % table_name

		primarykey = ''
		try:
			c = self.conn.cursor()
			c.execute(query_getpk_string)
			primarykey = c.fetchall()
		except Exception, e:
			npyscreen.notify_confirm('e: %s' % e)
			c.execute('ROLLBACK;')
			return
		finally:
			c.close()

		# constructs the column from user input
		# multiple execute statements are used here because psycopg2 automatically encapsulates
		# list/tuple insertions in quotes, which is an SQL syntax error for things like column name
		# and table name; the pyscopg2.extensions.AsIs module does not support unpackaging and inserting
		# for a list but is required to escape the psycopg2 quotes. To deal with these problems, each
		# variable option was broken out into its own SQL alter statement.
		try:
			c = self.conn.cursor()

			if column_values['collation']:
				npyscreen.notify_confirm('creation w/ collation sql') #debug
				c.execute('ALTER TABLE ' + table_name + ' ADD COLUMN %s %s COLLATE %s;', (AsIs(column_values['colname']), AsIs(column_values['datatype']), AsIs(column_values['collation'])))
			else:
				npyscreen.notify_confirm('creation sql') #debug
				c.execute('ALTER TABLE ' + table_name + ' ADD COLUMN %s %s;', (AsIs(column_values['colname']), AsIs(column_values['datatype'])))
				
			if column_values['default']:
				npyscreen.notify_confirm('default sql') #debug
				c.execute('ALTER TABLE ' + table_name + ' ALTER COLUMN %s SET DEFAULT %s;', (AsIs(column_values['colname']), column_values['default']))
				
			if column_values['nullable'] == [1]:
				npyscreen.notify_confirm('null sql') #debug
				# postgresql will not allow user to update column to NOT NULL if the column already
				# contains null values - this sets all values in the column to a required default value
				c.execute('UPDATE ' + table_name + ' SET %s = %s WHERE %s IS NULL;', (AsIs(column_values['colname']), AsIs(column_values['default']), AsIs(column_values['colname'])))
				c.execute('ALTER TABLE ' + table_name + ' ALTER COLUMN %s SET NOT NULL;', (AsIs(column_values['colname']),))

			if column_values['unique'] == [0]:
				npyscreen.notify_confirm('unique sql') #debug
				c.execute('ALTER TABLE ' + table_name + ' ADD UNIQUE (%s);', (AsIs(column_values['colname']),))
				
			if primarykey and column_values['pk'] == [0]:
				npyscreen.notify_confirm('Add column aborted. You already have a primary \
				key set on the %s field.' % primarykey[0])
				return
			elif column_values['pk'] == [0]:
				npyscreen.notify_confirm('pk sql') #debug
				c.execute('ALTER TABLE ' + table_name + ' ADD PRIMARY KEY (%s);', (AsIs(column_values['colname']),))

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
			query_string += (columns[x] + " = %s, ")
		query_string = query_string[:-2] + ' WHERE ('
		for x in range(0, len(columns)):
			query_string += (columns[x] + " = %s AND ")
		query_string = query_string[:-5] + ');'
		
		# pass parameters as separate list. psycopg2 automatically converts Python objects to 
		# SQL literals, prevents injection attacks
		data = []
		for x in range(0, len(columns)):
			data.append(str(new_values[x]))
		for x in range(0, len(columns)):
			data.append(str(old_values[x]))
		
		npyscreen.notify_confirm(query_string) # debug
		npyscreen.notify_confirm(data) # debug
		
		try:
			c = self.conn.cursor()
			c.execute(query_string, data)
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
		query_string = query_string[:-1] + ") VALUES ("
		for x in range(0, len(columns)):
			query_string += "%s" + ","
		query_string = query_string[:-1] + ");"
		
		# pass parameters as separate list. psycopg2 automatically converts Python objects to 
		# SQL literals, prevents injection attacks
		data = []
		for x in range(0, len(columns)):
			data.append(str(new_values[x]))
						
		npyscreen.notify_confirm(query_string) # debug
		npyscreen.notify_confirm(data) # debug
		
		try:
			c = self.conn.cursor()
			c.execute(query_string, data)
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
