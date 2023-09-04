import os

from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required


import os
import cs50

# Configure CS50 Library to use SQLite database
cwd = os.path.dirname(os.path.realpath(__file__))
filepath = os.path.join(cwd,'teacherInterface.db')     # Specifies the location to create the database
open(filepath,"w").close()     # Creates the database file

db = cs50.SQL("sqlite:///"+filepath)    # Links the library and database file through the db variable

# Creates the tables in the database as shown in the design section
db.execute("CREATE TABLE teachers (teacherID INTEGER, forename TEXT, surname TEXT, username TEXT UNIQUE, hash TEXT, PRIMARY KEY(teacherID))")
db.execute("CREATE TABLE students (studentID INTEGER, forename TEXT, surname TEXT, PRIMARY KEY(studentID))")
db.execute("CREATE TABLE days (dayID INTEGER, day TEXT, PRIMARY KEY(dayID))")
db.execute("CREATE TABLE clock (clockID INTEGER, time TEXT, PRIMARY KEY(clockID))")
db.execute("CREATE TABLE classNames (nameID INTEGER, name TEXT, PRIMARY KEY(nameID))")
db.execute("CREATE TABLE times (timeID INTEGER, week TEXT, dayID INTEGER, clockID INTEGER, PRIMARY KEY(timeID), FOREIGN KEY(dayID) REFERENCES days(dayID), FOREIGN KEY(clockID) REFERENCES clock(clockID))")
db.execute("CREATE TABLE classes (classID INTEGER, teacherID INTEGER, nameID INTEGER, numberOfStudents INTEGER, timeID INTEGER, PRIMARY KEY(classID), FOREIGN KEY(teacherID) REFERENCES teachers(teacherID), FOREIGN KEY(timeID) REFERENCES times(timeID), FOREIGN KEY(nameID) REFERENCES classNames(nameID))")
db.execute("CREATE TABLE classToStudent (classID INTEGER, studentID INTEGER, attendance TEXT DEFAULT '.', FOREIGN KEY(classID) REFERENCES classes(classID), FOREIGN KEY(studentID) REFERENCES students(studentID))")


days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
for day in days:
    db.execute("INSERT INTO days (day) VALUES (:day)", day = day)

times = ["9:15", "10:35", "11:35", "13:35", "14:35"]
for time in times:
    db.execute("INSERT INTO clock (time) VALUES (:times)", times = time)


weeks = ["A", "B"]
days = [1,2,3,4,5]
times = [1,2,3,4,5]

for week in weeks:
    for day in days:
        for time in times:
            db.execute("INSERT INTO times (week, dayID, clockID) VALUES (:week, :dayID, :times)", week = week, dayID = day, times = time)


""" # Table for logging in
db.execute("CREATE TABLE users (username TEXT, teacherID INTEGER, hash TEXT, PRIMARY KEY(username), FOREIGN KEY(teacherID) REFERENCES teachers(teacherID))") """



