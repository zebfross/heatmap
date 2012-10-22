#!/usr/bin/python

import sys
import MySQLdb

db_connection = {}
db_cursor = {}

def openDbConnection():
	global db_connection
	global db_cursor
	try:
		db_connection = MySQLdb.connect(host = "localhost", user = "zebfross_root", passwd="zebfross", db="zebfross_realestate")
	except MySQLdb.Error, e:
		print "Error %d: %s" % (e.args[0], e.args[1])
		sys.exit(1)

	db_cursor = db_connection.cursor()

def closeDbConnection():
	global db_connection
	global db_cursor
	db_cursor.close()
	db_connection.commit()
	db_connection.close()

def executeUpdate(query):
	global db_cursor
	try:
		db_cursor.execute(query)
		rowsAffected = db_cursor.rowcount
		return rowsAffected
	except MySQLdb.Error, e:
		print "Error %d: %s" % (e.args[0], e.args[1])
		print "SQL Update Error: ", query
		return 0

def executeQuery(query):
	global db_cursor
	try:
		db_cursor.execute(query)
		rows = db_cursor.fetchall()
		return rows
	except MySQLdb.Error, e:
		print "Error %d: %s" % (e.args[0], e.args[1])
		print "SQL Query Error: ", query
		return {}

create_table_query = """
		create table property
		(
			id varchar(15) primary key not null,
			address varchar(100),
			longitude decimal(12, 9),
			latitude decimal(12, 9),
			price decimal(12, 2),
			posted_at timestamp,
			crawled_at timestamp
		)
	"""

