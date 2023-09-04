#Import necessary libraries
from flask import Flask, Response, redirect, render_template, request, session
from werkzeug.security import check_password_hash

# Libraries used 
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError

from functions import names, display, lessons
import threading
import time
from turbo_flask import Turbo
import cv2
import cs50
import os
import datetime

from helpers import login_required, apology

#Initialize the Flask app
app = Flask(__name__)
app.config.update(SESSION_COOKIE_NAME='studentSession')
turbo = Turbo(app)

video_capture = cv2.VideoCapture(0)

@app.before_first_request
def before_first_request():
    threading.Thread(target=update_load).start()

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
filepath = os.path.join(r'D:\Desktop\Documents\Programming Project\Test\Teacher interface','teacherInterface.db')     # Specifies the location to create the database
db = cs50.SQL("sqlite:///"+filepath)    # Links the library and database file through the db variable

# Make sure API key is set
os.environ['API_KEY'] = 'pk_94949beadebd4b6ab617125cc67c82ff'
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route('/', methods=["GET", "POST"])
@login_required
def index():
    if request.method == "GET":
        return render_template("index.html")

    else:
        if request.form.get("yes"):
            return redirect('/success')
        elif request.form.get("no"): 
            return redirect('/failure')

    return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    with app.app_context():
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
            currentDate = datetime.datetime.now()
            currentDay = currentDate.strftime("%A")
            currentTime = currentDate.time()
            classtime = datetime.datetime(2020, 5, 13, 9, 10, 00).time() 
            if currentDay == "Monday" and currentTime < classtime:
                update = db.execute("UPDATE classToStudent SET attendance = '.'")

            return render_template("login.html")

@app.route('/success')
@login_required
def success():
    print("success-GET")
    # name is initially blank
    name = ''

    # Iterates until a match for the user in frame is found 
    while True:
        nameslist = names(video_capture)[2]
        if nameslist:
            name = nameslist[0].title()
            break
    print('Name from face recognition: {}'.format(name))
    form = "default"

    # Variable containing the value for the "name" key in the session dictionary
    nameTest = session.get("name")
    if nameTest: 
        name = session["name"].title()
        print('Name from failure route: {}'.format(name))
        form = session["form"].upper()
        session.pop("name")
        session.pop("form")
    combinedName = name.split(" ", 1)
    forename = combinedName[0]
    surname = combinedName[1]
    

    # Values returned from the lessons function are assigned to variables 
    attendance, classTime, currentDay, week = lessons()
    print('Attendance: {}'.format(attendance))
    print('Class start time: {}'.format(classTime))
    print('The current day of the week: {}'.format(currentDay))
    print('Week (A or B): {}'.format(week))
    if attendance == 0:
        return apology("No lesson at the moment!")
    
    # classDict = variable containing array with class ID and class name of 
    # all the classes happening at the moment in time in which the success route is called
    classDict = db.execute("""SELECT classID, name FROM classes LEFT JOIN times ON classes.timeID = times.timeID LEFT JOIN days ON times.dayID = days.dayID 
    LEFT JOIN clock ON clock.clockID = times.clockID LEFT JOIN classNames ON classes.nameID = classNames.nameID 
    WHERE teacherID = :ID AND day = :days AND week = :week AND clock.time = :time""", ID = session["user_id"], days = currentDay, week = week, time = classTime)
    ############ Delete above when taking example images
    if len(classDict) == 0:
        return apology("No class at the moment!")
    classID = classDict[0]["classID"]
    className = classDict[0]["name"]
    if className != form.upper() and form != "default":
        return apology("No such class at the moment!")
    form = className

    # studentDict = variable containing array which contains studentIDs of 
    # students with the forename and surname given
    studentDict = db.execute("SELECT studentID FROM students WHERE forename = :forename AND surname = :surname", forename = forename, surname = surname)
    ############ Delete above when taking example images
    if len(studentDict) == 0:
        return apology("No such student in database!")
    studentID = studentDict[0]["studentID"]
        
    # update = variable containing number of rows changed when updating database
    update = db.execute("UPDATE classToStudent SET attendance = :attendance WHERE classID = :classID AND studentID = :studentID", attendance = attendance, classID = classID, studentID = studentID)
    ############ Delete above when taking example images
    if update != 1:
        return apology("No such student in current class!")

    return render_template('success.html', name = name, form = form)


@app.route('/failure', methods=["GET", "POST"])
@login_required
def failure():
    if request.method == "GET":
        print("failure-GET")
        return render_template("failure.html")
    else:
        print("failure-POST")
        forename = request.form.get("forename").title()
        surname = request.form.get("surname").title()
        form = request.form.get("form").upper()
        combinedName = forename+" "+surname
        session["name"] = combinedName
        session["form"] = form
        return redirect("/success")

# Route to display webcam feed with overlays
@app.route('/video_feed')
@login_required
def video_feed():
    # Returns a Response instance which can then be passed to other files
    return Response(display(video_capture), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.context_processor
def inject_load():
    nameslist = names(video_capture)[2]
    if nameslist:
        name = nameslist[0]
    else:
        name = '...'
    return {'fullname': name}

def update_load():
    with app.app_context():
        while True:
            time.sleep(1)
            turbo.push(turbo.replace(render_template('name.html'), 'placeholder'))


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


if __name__ == "__main__":
    app.run(debug=True)