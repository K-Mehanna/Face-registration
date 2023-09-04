# Libaries to help with the database
import os
import cs50
import datetime
from PIL import Image 
import PIL 
import csv

# Libraries used 
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

# Functions imported from helpers.py
from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates (html webpages) are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Specifies the location to save files
UPLOAD_FOLDER = r"D:\Desktop\Documents\Programming Project\Test\static\images"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
cwd = os.path.dirname(os.path.realpath(__file__))
filepath = os.path.join(cwd,'teacherInterface.db')     # Specifies the location to create the database
db = cs50.SQL("sqlite:///"+filepath)    # Links the library and database file through the db variable

# Make sure API key is set
os.environ['API_KEY'] = 'pk_94949beadebd4b6ab617125cc67c82ff'
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    currentDate = datetime.datetime.now()
    currentDay = currentDate.strftime("%A")
    currentWeek = currentDate.strftime("%W")

    if int(currentWeek) % 2 == 1:
        week = "A"
    else:
        week = "B"

    # Variable containing a list which stores a dictionary for each class on the current day for the teacher signed in
    # The dictionary for each class contains the necessary information about each class to display on the dashboard
    classes = db.execute("""SELECT classID, name, numberOfStudents, week, day, time, classes.timeID FROM classes LEFT JOIN 
    times ON classes.timeID = times.timeID LEFT JOIN days ON times.dayID = days.dayID LEFT JOIN clock ON clock.clockID = 
    times.clockID LEFT JOIN classNames ON classes.nameID = classNames.nameID WHERE teacherID = :ID AND day = :days AND 
    week = :week ORDER BY week, days.dayID, clock.clockID""", ID = session["user_id"], days = currentDay, week = week)
    
    # If there are no classes for the current day, a specific blank HTML is loaded
    if len(classes) == 0:
        return render_template("blank index.html")

    else:
        # List storing the classID for every class on the current day
        classIDlist = []
        for item in classes:
            classIDlist.append(item["classID"])
        
        attendance = []
        # Iterates through each class and identifies the number of students present, then appends it to the attendance list
        for classID in classIDlist:
            present = db.execute("""SELECT forename, surname, attendance FROM students LEFT JOIN classToStudent ON 
            students.studentID = classToStudent.studentID LEFT JOIN classes ON classes.classID = classToStudent.classID 
            LEFT JOIN classNames ON classNames.nameID = classes.nameID WHERE classes.classID = :ID AND attendance != '.'
            """, ID = classID)
            attendance.append(len(present))

        # Calculates the percentage attendance for each class and adds it to the dictionary for that class
        for i in range((len(classes))):
            item = classes[i]
            total = int(item["numberOfStudents"])
            present = attendance[i]
            item["present"] = present
            percentage = round((present / total) * 100)
            item["percentage"] = str(percentage)
        
        return render_template("index.html", classes = classes)
    
        



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    session.clear()

    # If the form is submitted
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM teachers WHERE username = :username", username=request.form.get("username").lower())

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["teacherID"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # If the form is submitted
    if request.method == "POST":

        # Checks if any fields are left blank and that passwords match

        if not request.form.get("forename"):
            return apology("must provide forename!")

        elif not request.form.get("surname"):
            return apology("must provide surname!")

        elif not request.form.get("username"):
            return apology("must provide username!")

        elif not request.form.get("password"):
            return apology("must provide password!")

        elif not request.form.get("confirm"):
            return apology("must provide confirmation of password!")

        elif request.form.get("confirm") != request.form.get("password"):
            return apology("passwords must match!")

        # Gets the forename and surname from the form
        forenames =  request.form.get("forename").title()
        surnames =  request.form.get("surname").title()

        # Creates the hashed password
        hash_pass = generate_password_hash(request.form.get("password"))

        # Gets the username from the form
        usernames = request.form.get("username").lower()
        rows = db.execute("SELECT * FROM teachers WHERE username = :username", username=usernames)
        
        if len(rows) == 0:
            # Adds the user's username and password to the database
            insert = db.execute("INSERT INTO teachers (forename, surname, username, hash) VALUES (:forename, :surname, :username, :hashs)", forename = forenames, surname = surnames, username = usernames, hashs = hash_pass)

        # If the user's details could not be inserted (username is already taken), an apology is created
        else:
            return apology("Username is taken!")

        row = db.execute("SELECT * FROM teachers WHERE username = :username", username = usernames)
        session["user_id"] = row[0]["teacherID"]

        return redirect("/login")

    else:
        return render_template("register.html")



@app.route("/add-class", methods=["GET", "POST"])
@login_required
def addClass():
    # If the form is submitted
    if request.method == "POST":

        # Checks if any fields are left blank and that passwords match
        if not request.form.get("class_name"):
            return apology("must provide class name!")

        elif not request.form.get("student_number"):
            return apology("must provide number of students!")

        elif not request.form.get("lesson_number"):
            return apology("must provide number of lessons!")

        # Gets the class name from the form
        names = request.form.get("class_name").upper()

        # Gets the number of students and lessons a fortnight
        # And checks that the numbers are positive
        student_numbers = request.form.get("student_number")
        lesson_numbers = request.form.get("lesson_number")
        if int(student_numbers) < 0:
            return apology("must be positive")
        elif int(lesson_numbers) < 0:
            return apology("must be positive")
        teacherID = session["user_id"]

        # Gets the nameID for the class name, in case another teacher teaches the same class
        nameID = db.execute("SELECT nameID FROM classNames WHERE name = :name", name = names)
        if len(nameID) != 0:
            # Tests if the current teacher already has that class registered
            duplicates = db.execute("""SELECT * FROM classes WHERE nameID = :name AND 
            teacherID = :ID""", name = nameID[0]['nameID'], ID = teacherID)
            # Error message if there are duplicates
            if len(duplicates) != 0:
                return apology("Class already exists")

        session["name"] = names
        session["student_numbers"] = student_numbers
        session["lesson_numbers"] = lesson_numbers

        print("Class name: {}".format(names))
        print("No. of students: {}".format(student_numbers))
        print("No. of lessons a fortnight: {}".format(lesson_numbers))

        return redirect("/class-details")

    else:
        return render_template("add class.html")



@app.route("/class-details", methods=["GET", "POST"])
@login_required
def classDetails():
    # Number of lessons a fortnight is stored as an integer
    temp = session["lesson_numbers"]
    lesson_numbers = int(temp)
    teacherID = session["user_id"] 

    # Populates a list with the same number of items as there are classes in a fortnight
    loopingList = []
    for i in range(lesson_numbers):
        loopingList.append(i)

    # If the form is submitted
    if request.method == "POST":
        timesList = []

        for item in loopingList:
            # Stores the week, day and time of each lesson over the fortnight
            weeks = request.form.get("week"+str(item))
            days = request.form.get("day"+str(item))
            times = request.form.get("time"+str(item))

            # Finds the timeID for each lesson
            ID_dict = db.execute("""SELECT timeID FROM times LEFT JOIN days ON times.dayID
             = days.dayID LEFT JOIN clock ON clock.clockID = times.clockID WHERE day = :day
             AND time = :time AND week = :week""", day=days, time=times, week=weeks)
            timeID = ID_dict[0]["timeID"]

            # Checks if the timeID is already being used by a class
            duplicateTest = db.execute("""SELECT * FROM classes WHERE timeID = :timeID and 
            teacherID = :ID""", timeID = timeID, ID = teacherID)

            # If the timeID is being used then an error message is shown
            if len(duplicateTest) != 0:
                return apology("Time slot already filled!")

            # The timeID is added to a list containing all the timeIDs for that class
            timesList.append(timeID)

        session["timesList"] = timesList

        # Redirects teacher to route to specify names and upload images depending on whether 
        # they want to enter names individually or upload a CSV
        inputType = request.form.get("type")
        if inputType == "Individually":
            return redirect("/students-individual")
        else:
            return redirect("/students-csv")
        
    else:
        return render_template("class-details.html", loopingList = loopingList)


@app.route("/students-csv", methods=["GET", "POST"])
@login_required
def studentsCSV():
    # Function to check that the file extension is allowed 
    def allowed_file(filename):
        allowedExtensions = {'png', 'jpg', 'jpeg'}
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowedExtensions
    
    className = session["name"]

    # When the form is submitted
    if request.method == "POST":
        # Inserts the name of the class into the database
        nameID = db.execute("INSERT INTO classNames (name) VALUES (:name)", name = className)
        timesList = session["timesList"]
        student_numbers = session["student_numbers"] 
        teacherID = session["user_id"] 

        # Inserts each specific class instance into the database
        for timeID in timesList:
            db.execute("""INSERT INTO classes (teacherID, nameID, numberOfStudents, 
            timeID) VALUES (:ID, :nameID, :number, :timeID)
            """, ID = teacherID, nameID = nameID, number = student_numbers, timeID = timeID)

        i=0
        # Variable containing a list of the names of the images
        images = request.files.getlist('images')
        # Variable containing the CSV file
        names = request.files["names"]
        if names.filename == '':
            return apology("must include CSV")
        # CSV file is saved into the correct directory
        names.save(os.path.join(os.getcwd(), names.filename))

        # Iterates through each line in the CSV
        with open(names.filename, 'r') as namesfile:
            reader = csv.reader(namesfile)
            for row in reader:
                # Extracts student's first and last names
                forename = row[0].title()
                surname = row[1].title()
                combinedName = ' '.join(row)
                image = images[i]
                name = image.filename
                if name == '':
                    return apology("Please upload photos")
                extension = os.path.splitext(name)[1]
                combinedFileName = combinedName.title() + extension

                # Saves image as student_name.extension
                if image and allowed_file(name):
                    image.save(os.path.join(app.config['UPLOAD_FOLDER'], combinedFileName))

                # Tests if the student is already in the database
                duplicateTest = db.execute("""SELECT studentID FROM students WHERE forename
                 = :forename AND surname = :surname""", forename = forename, surname = surname)
                if len(duplicateTest) == 0:
                    studentID = db.execute("""INSERT INTO students (forename, surname) VALUES 
                    (:forename, :surname)""", forename = forename, surname = surname)
                else:
                    studentID = duplicateTest[0]["studentID"]

                nameDict = db.execute("SELECT nameID FROM classNames WHERE name = :name", name = className)
                nameID = nameDict[0]["nameID"]

                classIDs = db.execute("""SELECT classID FROM classes LEFT JOIN classNames on classes.nameID = 
                classNames.nameID WHERE teacherID = :ID AND name = :name""", ID = session["user_id"], name = className)
                for item in classIDs:
                    classID = item["classID"]
                    # Adds student to classToStudent table which maps a student to a class
                    insert = db.execute("""INSERT INTO classToStudent (classID, studentID)
                     VALUES (:classID, :studentID)""", classID = classID, studentID = studentID)
                i += 1

        flash("Class added!")
        return redirect("/")
    else:
        return render_template("students-csv.html")


@app.route("/students-individual", methods=["GET", "POST"])
@login_required
def studentsInd():
    # Checks uploaded file is of the correct type
    def allowed_file(filename):
        allowedExtensions = {'png', 'jpg', 'jpeg'}
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowedExtensions
    
    names = session["name"] 
    student_numbers = session["student_numbers"]

    # List to iterate through with same length as number of students
    # Allows each input to be assigned a unique ID
    nums = int(student_numbers)
    loopingList = []
    for i in range(nums):
        loopingList.append(i)

    # When the form is submitted
    if request.method == "POST":
        # Inserts the name of the class into the database
        nameID = db.execute("INSERT INTO classNames (name) VALUES (:name)", name = names)
        timesList = session["timesList"]
        student_numbers = session["student_numbers"] 
        teacherID = session["user_id"]

        # Inserts each specific class instance into the database
        for timeID in timesList:
            db.execute("""INSERT INTO classes (teacherID, nameID, numberOfStudents, timeID) VALUES (:ID, :nameID, 
            :number, :timeID)""", ID = teacherID, nameID = nameID, number = student_numbers, timeID = timeID)

        # Iterates through every student in the class
        for item in loopingList:
            # Gets student's first and last name from input form 
            # And checks that the field is filled
            combinedName = request.form.get("name"+str(item))
            if not combinedName:
                return apology("student name missing!")
            combinedName = combinedName.title()
            nameList = combinedName.split(" ", 1)
            forename = nameList[0]
            surname = nameList[1]

            # Gets the file related to that student
            file = request.files["image"+str(item)]

            # Creates the file name by combining the student's name with the file extension
            name = file.filename
            extension = os.path.splitext(name)[1]
            combinedFileName = combinedName + extension

            # If the user does not select a file, the browser submits an empty file without a filename
            # The user is asked to try again and redirected to the same page
            if file.filename == '':
                flash('No selected file')
                return redirect("/students")
            # If the user submits a file and it has an allowed extension, it is saved to the Images folder
            if file and allowed_file(file.filename):
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], combinedFileName))

            # Checks that the student isn't already in the database
            # If they are, then they are not added again
            duplicateTest = db.execute("""SELECT studentID FROM students WHERE forename = :forename AND 
            surname = :surname""", forename = forename, surname = surname)
            if len(duplicateTest) == 0:
                studentID = db.execute("""INSERT INTO students (forename, surname) VALUES (:forename, 
                :surname)""", forename = forename, surname = surname)
            else:
                studentID = duplicateTest[0]["studentID"]

            nameDict = db.execute("SELECT nameID FROM classNames WHERE name = :name", name = names)
            nameID = nameDict[0]["nameID"]  

            classIDs = db.execute("""SELECT classID FROM classes LEFT JOIN classNames on classes.nameID = 
            classNames.nameID WHERE teacherID = :ID AND name = :name""", ID = session["user_id"], name = names)
            for item in classIDs:
                classID = item["classID"]
                insert = db.execute("""INSERT INTO classToStudent (classID, studentID) VALUES (:classID, 
                :studentID)""", classID = classID, studentID = studentID)


        flash("Class added!")
        return redirect("/")
    else:
        return render_template("students-ind.html", loopingList = loopingList)




@app.route("/view-all")
@login_required
def viewAll():

    # List containing dictionaries for each class
    # Each dictionary contains the name, week, day, and time of the class
    classes = db.execute("""SELECT classID, name, numberOfStudents, week, day, time FROM classes 
    LEFT JOIN times ON classes.timeID = times.timeID LEFT JOIN days ON times.dayID = days.dayID 
    LEFT JOIN clock ON clock.clockID = times.clockID LEFT JOIN classNames ON classes.nameID = 
    classNames.nameID WHERE classes.teacherID = :ID ORDER BY week, days.dayID, clock.clockID""", ID = session["user_id"])

    return render_template("view all.html", classes = classes)


@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    if request.method == "POST":
        # Variable containing the selected class
        answer = request.form.get("answer").upper()
        # The nameID of the selected class is found
        nameDict = db.execute("SELECT nameID FROM classNames WHERE name = :name", name = answer)
        nameID = nameDict[0]["nameID"]

        # All class-to-student mappings involving the selected class are deleted
        classIDs = db.execute("SELECT classID FROM classes WHERE nameID = :nameID", nameID = nameID)
        for item in classIDs:
            classID = item["classID"]
            delete = db.execute("DELETE FROM classToStudent WHERE classID = :classID;", classID = classID)

        # All instances of the selected class are deleted
        classes = db.execute("DELETE FROM classes WHERE nameID = :nameID;", nameID = nameID)
        
        classNames = db.execute("DELETE FROM classNames WHERE name = :name", name = answer)
        flash("Class deleted!")
        return redirect("/view-all")

    else:
        # Generates a list of all the instances of every class for that teacher
        classes = db.execute("""SELECT name FROM classes LEFT JOIN classNames ON classes.nameID = 
        classNames.nameID WHERE classes.teacherID = :ID ORDER BY name""", ID = session["user_id"])
        namesList = []
        # Creates a list with only unique class names
        for i in range(len(classes)):
            name = classes[i]["name"]
            if name in namesList:
                continue
            else:
                namesList.append(name)
        return render_template("delete.html", names = namesList)



@app.route("/table", methods=["POST"])
@login_required
def table():
    if request.method == "POST":
        className = request.get_json()['name'].upper()
        session["className"] = className
        classTime = request.get_json()['time']
        classWeek = request.get_json()['week']
        classDay = request.get_json()['day']
        print("Class name: {}".format(className))
        print("Class name: {}".format(classTime))
        print("Class name: {}".format(classWeek))
        print("Class name: {}".format(classDay))

        timeIDdict = db.execute("""SELECT classes.timeID FROM classes LEFT JOIN times ON 
        classes.timeID = times.timeID LEFT JOIN days ON times.dayID = days.dayID LEFT JOIN 
        clock ON clock.clockID = times.clockID LEFT JOIN classNames ON classes.nameID = classNames.nameID 
        WHERE teacherID = :ID AND day = :days AND week = :week AND classNames.name = :name AND clock.time 
        = :time""", ID = session["user_id"], days = classDay, week = classWeek, name = className, time = classTime)
        timeID = timeIDdict[0]["timeID"]
    

        classes = db.execute("""SELECT forename, surname, attendance FROM students LEFT JOIN classToStudent 
        ON students.studentID = classToStudent.studentID LEFT JOIN classes ON classes.classID = classToStudent.classID 
        LEFT JOIN classNames ON classNames.nameID = classes.nameID WHERE classNames.name = :name AND classes.teacherID = :ID 
        AND classes.timeID = :timeID ORDER BY SURNAME""", name = className, ID = session["user_id"], timeID = timeID)

        session["classes"] = classes
        return redirect("/attendance")



@app.route("/attendance")
@login_required
def attendance():
    classname = session["className"]
    classList = session["classes"]
    return render_template("table.html", name = classname, classes = classList)
    





def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

#Runs the website
if __name__ == "__main__":
    app.run(debug=True)
