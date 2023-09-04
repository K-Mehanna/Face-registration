import os

from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

import cs50
# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

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
filepath = os.path.join(cwd,'teacherInterface.db')     # Specifies the location to create the database """
open(filepath,"w").close()     # Creates the database file

db = cs50.SQL("sqlite:///"+filepath)    # Links the library and database file through the db variable

# Creates the tables in the database as shown in the design section
db.execute("CREATE TABLE teacher (teacherID INTEGER, forename TEXT, surname TEXT, PRIMARY KEY(teacherID))")
db.execute("CREATE TABLE student (studentID INTEGER, forename TEXT, surname TEXT, PRIMARY KEY(studentID))")
db.execute("CREATE TABLE time (timeID INTEGER, time TEXT, PRIMARY KEY(timeID))")
db.execute("CREATE TABLE class (classID INTEGER, teacherID INTEGER, className TEXT, timeID INTEGER, PRIMARY KEY(classID), FOREIGN KEY(teacherID) REFERENCES teacher(teacherID), FOREIGN KEY(timeID) REFERENCES time(timeID))")
db.execute("CREATE TABLE classToStudent (classID INTEGER, studentID INTEGER, FOREIGN KEY(classID) REFERENCES class(classID), FOREIGN KEY(studentID) REFERENCES student(studentID))")

# Table for logging in
db.execute("CREATE TABLE users (username TEXT, teacherID INTEGER, hash TEXT, PRIMARY KEY(username), FOREIGN KEY(teacherID) REFERENCES teacher(teacherID))")


# Make sure API key is set
os.environ['API_KEY'] = 'pk_94949beadebd4b6ab617125cc67c82ff'
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    stocks = db.execute("SELECT Symbol, Name, Shares FROM portfolio WHERE id = :ids", ids = session['user_id'])
    result = db.execute("SELECT cash FROM users WHERE id = :ids", ids = session['user_id'])
    cash = float(result[0]['cash'])
    total = cash
    prices = {}
    totals = {}

    for row in stocks:
        symbol = str(row["Symbol"])
        shares = int(row["Shares"])
        quote = lookup(symbol)
        price = quote['price']
        total_value = price * shares
        total += total_value
        prices[symbol] = format(price, '.2f')
        totals[symbol] = "{:0,.2f}".format(float(total_value))

    money = "{:0,.2f}".format(float(cash))
    total = "{:0,.2f}".format(float(total))
    return render_template("index.html", stocks = stocks, cash = money, total = total, prices=prices, totals=totals)
    


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

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

    if request.method == "POST":

        if not request.form.get("username"):
            return apology("must provide username!")

        elif not request.form.get("password"):
            return apology("must provide password!")

        elif not request.form.get("confirm"):
            return apology("must provide confirmation of password!")

        elif request.form.get("confirm") != request.form.get("password"):
            return apology("passwords must match!")

        # Creates the hashed password
        hash_pass = generate_password_hash(request.form.get("password"))

        usernames = request.form.get("username")

        # Adds the user's username and password to the database
        insert = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hashs)", username = usernames, hashs = hash_pass)

        # If the user's details could not be inserted (username is already taken), an apology is created
        if not insert:
            return apology("Username is taken!")

        rows = db.execute("SELECT * FROM users WHERE username = :username", username = usernames)

        session["user_id"] = rows[0]["id"]

        flash("Registered!")
        return redirect("/login")

    else:
        return render_template("register.html")









@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    if request.method == "GET":
        return render_template("buy.html")

    else:
        symbol = request.form.get("symbol").upper()
        result = lookup(symbol)
        num = request.form.get("shares")

        if not symbol:
            return apology("must provide a symbol")

        elif result == None:
            return apology("must provide a valid symbol")

        elif not num:
            return apology("must provide number of shares")

        num = int(num)
        if num < 1:
            return apology("Number of shares must be above 0")

        result2 = db.execute("SELECT cash FROM users WHERE id = :ids", ids = session["user_id"])
        cash = float(result2[0]['cash'])

        total = result["price"] * num
        name = result['name']
        total = cash - total


        if cash < total:
            return apology("not enough cash")
        else:
            y = db.execute("SELECT Shares FROM portfolio WHERE id=:ids AND Symbol=:symbol", ids = session['user_id'], symbol = symbol)
            print(y)
            if not y:
                db.execute("INSERT INTO portfolio (id, Symbol, Name, Shares, Price) VALUES (:ids, :symbol, :name, :shares, :price)", ids=session['user_id'], symbol=symbol, name=name, shares=num, price=result['price'])
            else:
                shares = int(y[0]['Shares'])
                shares += num
                db.execute("UPDATE portfolio SET Shares = :shares WHERE id = :ids AND Symbol= :symbol", shares=shares, ids = session['user_id'], symbol = symbol)

            price = result["price"] * (-1)
            db.execute("INSERT INTO history (id, Symbol, Name, Shares, Price) VALUES (:ids, :symbol, :name, :shares, :price)", ids=session['user_id'], symbol=symbol, name=name, shares=num, price=price)
            db.execute("UPDATE users SET cash = :total WHERE id=:ids", total=total, ids=session['user_id'])

            flash("Bought!")
            return redirect("/")



@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    total = {}
    total_value = 0

    rows = db.execute("SELECT * FROM history WHERE id=:ids", ids=session["user_id"])
    for row in rows:
        total_value = float(row['Price']) * row['Shares']
        total_value = "{:0,.2f}".format(float(total_value))
        total[row['Symbol']] = total_value
    return render_template("history.html", total=total, rows=rows)



@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "GET":
        return render_template("quote.html")

    else:
        if not request.form.get("symbol"):
            return apology("must provide a symbol!")

        results = lookup(request.form.get("symbol"))
        if results == None:
            return apology("must provide a valid symbol!")

        return render_template("quoted.html", name=results["name"], price=results["price"], symbol=results["symbol"])





@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    x = db.execute("SELECT Symbol, Name FROM portfolio WHERE id=:ids", ids=session["user_id"])

    if request.method == "POST":

        symbol = request.form.get("symbol").upper()
        if not symbol:
            return apology("Did not specify symbol")

        result = lookup(symbol)
        price = result["price"]
        name = result["name"]

        if not request.form.get("shares"):
            return apology("must enter no. of shares")
        else:
            num = request.form.get("shares")
            num = int(num)

        cash = db.execute("SELECT cash FROM users WHERE id=:ids", ids=session["user_id"])
        cash = cash[0]["cash"]

        shares = db.execute("SELECT Shares FROM portfolio WHERE id=:ids AND Symbol=:symbol", ids=session["user_id"], symbol=symbol)
        shares = shares[0]["Shares"]
        shares=int(shares)

        if shares < num:
            return apology("not enough shares")
        else:
            neg_num = (-1) * num
            pos_num = shares-num
            total_price = price * num

            db.execute("INSERT INTO history (id, symbol, name, shares, price) VALUES (:ids, :symbol, :name, :shares, :price)", ids=session['user_id'], symbol=symbol, name=name, shares=neg_num, price=usd(price))
            if pos_num == 0:
                db.execute("DELETE FROM portfolio WHERE id=:ids AND Symbol=:symbol", ids=session["user_id"], symbol=symbol)
            else:
                db.execute("UPDATE portfolio SET Shares = :num WHERE id=:ids AND Symbol=:symbol", num=pos_num, ids=session["user_id"], symbol=symbol)

        cash += total_price
        db.execute("UPDATE users SET cash = :cash WHERE id=:ids", cash=cash, ids=session["user_id"])

        flash("Sold!")

        return redirect("/")
    else:
        return render_template("sell.html", x = x)


@app.route("/more", methods=["GET", "POST"])
@login_required
def more():
    if request.method == "GET":
        return render_template("more.html")
    else:
        money = request.form.get("money")
        if not money:
            return apology("did not specify amount")
        money = float(money)
        if money < 0:
            return apology("must be positive amount")

        cash = db.execute("SELECT cash FROM users WHERE id=:ids", ids=session["user_id"])
        cash = cash[0]["cash"]
        cash = float(cash)
        cash += money

        db.execute("UPDATE users SET cash = :cash WHERE id=:ids", cash=cash, ids=session["user_id"])

        flash("Money added")

        return redirect("/")


@app.route("/reset", methods=["GET", "POST"])
@login_required
def reset():
    if request.method == "GET":
        return render_template("reset.html")
    else:
        db.execute("UPDATE users SET cash = 10000 WHERE id=:ids", ids=session["user_id"])
        db.execute("DELETE FROM portfolio WHERE id=:ids", ids=session["user_id"])
        db.execute("DELETE FROM history WHERE id=:ids", ids=session["user_id"])

        flash("All assests reset")

        return redirect("/")



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
