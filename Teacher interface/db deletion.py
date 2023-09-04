import os
import cs50

# Configure CS50 Library to use SQLite database
cwd = os.path.dirname(os.path.realpath(__file__))
filepath = os.path.join(cwd,'teacherInterface.db')     # Specifies the location to create the database
db = cs50.SQL("sqlite:///"+filepath)    # Links the library and database file through the db variable

delete = db.execute("DELETE FROM classToStudent;")
delete = db.execute("DELETE FROM classes;")
delete = db.execute("DELETE FROM students;")
delete = db.execute("DELETE FROM classNames;")
