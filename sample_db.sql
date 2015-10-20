/*
	Simple script to create a postgreSQL database for testing ncurses interface.
	
	I tried to make a separate database, but get complains from the OS that I don't have permission to do so...
	Instead, choose a db that already exists, and run the script from there with the following command:
	
	\i sample_db.sql
*/

DROP DATABASE IF EXISTS curses_test;
CREATE DATABASE curses_test;

DROP TABLE IF EXISTS us_states;

CREATE TABLE us_states (
  id SERIAL PRIMARY KEY,
  name VARCHAR(20) NOT NULL
);

DROP TABLE IF EXISTS us_cities;

CREATE TABLE us_cities (
  id SERIAL PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  population INT,
  state_id INT references us_states(id)
);

INSERT INTO us_states (name) VALUES
	('Alabama'),
	('Alaska'),
	('Arizona'),
	('Arkansas'),
	('California'), /*5*/
	('Colorado'),
	('Connecticut'),
	('Delaware'),
	('Florida'),
	('Georgia'),
	('Hawaii'),
	('Idaho'),
	('Illinois'),
	('Indiana'),
	('Iowa'),
	('Kansas'),
	('Kentucky'),
	('Louisiana'),
	('Maine'), /*19*/
	('Maryland'),
	('Massachusetts'), /*21*/
	('Michigan'),
	('Minnesota'),
	('Mississippi'),
	('Missouri'),
	('Montana'),
	('Nebraska'),
	('Nevada'),
	('New Hampshire'),
	('New Jersey'),
	('New Mexico'),
	('New York'), /*32*/
	('North Carolina'),
	('North Dakota'),
	('Ohio'),
	('Oklahoma'), /*37*/
	('Oregon'),
	('Pennsylvania'),
	('Rhode Island'),
	('South Carolina'),
	('South Dakota'),
	('Tennessee'),
	('Texas'),
	('Utah'),
	('Vermont'),
	('Virginia'), /*46*/
	('Washington'),
	('West Virginia'),
	('Wisconsin'),
	('Wyoming');

INSERT INTO us_cities (name, population, state_id) VALUES
	('Richmond', 600000, 46),
	('Charlottesville', 55000, 46),
	('Fairfax', 1200000, 46),
	('Newport News', 250000, 46),
	('New York City', 8000000, 32),
	('Albany', 1000000, 32),
	('Albany', 40000, 37),
	('Portland', 80000, 19),
	('Portland', 100000, 37),
	('Corvallis', 50000, 37),
	('Salem', 150000, 37),
	('Eugene', 300000, 37),
	('Bend', 110000, 37),
	('Boston', 5000000, 21),
	('Los Angeles', 10000000, 5),
	('San Francisco', 5000000, 5),
	('Sacramento', 2000000, 5);