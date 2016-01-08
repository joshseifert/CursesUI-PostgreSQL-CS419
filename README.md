# cs419-cursesui-db 
This project is an interface for a PostgreSQL database, written for CS 419 at OSU.

Written in Python, this program uses the NCurses and Npyscreen libraries to create a terminal-independent GUI-like interface that can communicate with a database, similar to PHPMyAdmin. The intended users are people who are comfortable using the aforementioned database software. 

Once connected to a database, the software allows the following operations:

The user may browse individual tables in their database, where they may add, delete, or update specific rows

The user may view and edit the table structure itself

The user may perform more complex queries, including all standard CRUD and DDL operations using a traditional SQL Runner

The aforementioned operations also allow the user to change the number of results displayed per page, as well as offering pagination buttons, as requested by the client.
