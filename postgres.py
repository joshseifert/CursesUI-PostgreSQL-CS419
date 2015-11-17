import psycopg2
import npyscreen

class PostgreSQL():
	def __init__(self, database, user, password, host, port):
		self.conn = psycopg2.connect(database=database, 
			user=user, 
			password=password, 
			host=host, 
			port=port)
			
	def run_sql(self, query):
		try:
			c = self.conn.cursor()
			c.execute(query)
			# http://stackoverflow.com/questions/10252247/how-do-i-get-a-list-of-column-names-from-a-psycopg2-cursor
			colnames = [desc[0] for desc in c.description]
			results = c.fetchall()
			return colnames, results
		except Exception, e:
			# psql transactions posted after a failed transaction
			# on the same cxn will fail if the original transaction 
			# is not rolled back first
			# http://stackoverflow.com/questions/10399727/psqlexception-current-transaction-is-aborted-commands-ignored-until-end-of-tra
			npyscreen.notify_confirm("e: %s" % e)
			c.execute("ROLLBACK;")			
		finally:
			c.close()	
		
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
			rows = []
			rows.append(colnames)
			for result in results:
				rows.append(list(result))
			return rows
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
			rows = []
			rows.append(colnames)
			for result in results:
				rows.append(list(result))
			return rows
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
