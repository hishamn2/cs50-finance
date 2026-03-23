import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user_id = session["user_id"]

    # Get user's current cash
    cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]

    # Get shares grouped by symbol, only where they own > 0
    rows = db.execute("SELECT symbol, SUM(shares) as total_shares FROM transactions WHERE user_id = ? GROUP BY symbol HAVING total_shares > 0", user_id)

    portfolio = []
    total_stock_value = 0

    for row in rows:
        stock = lookup(row["symbol"])
        total_value = stock["price"] * row["total_shares"]
        portfolio.append({
            "symbol": stock["symbol"],
            "name": stock["name"],
            "shares": row["total_shares"],
            "price": stock["price"],
            "total": total_value
        })
        total_stock_value += total_value

    return render_template("index.html", portfolio=portfolio, cash=cash, total=cash + total_stock_value)

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        # 1. Validation: Did they type anything?
        if not symbol:
            return apology("must provide symbol", 400)

        # 2. Validation: Is 'shares' a positive integer?
        try:
            shares = int(shares)
            if shares <= 0:
                return apology("shares must be a positive integer", 400)
        except ValueError:
            return apology("shares must be a number", 400)

        # 3. Lookup the stock price
        stock = lookup(symbol)
        if not stock:
            return apology("invalid symbol", 400)

        # 4. Check user's cash
        user_id = session["user_id"]
        cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]

        total_cost = stock["price"] * shares

        if cash < total_cost:
            return apology("can't afford", 400)


     # Check indentation here!
        db.execute("UPDATE users SET cash = cash - ? WHERE id = ?", total_cost, user_id)

        # Ensure this is inside the POST block
        db.execute("INSERT INTO transactions (user_id, symbol, shares, price, type) VALUES (?, ?, ?, ?, ?)",
           user_id, stock["symbol"], shares, stock["price"], 'buy')
        flash("Bought!")

        return redirect("/")

    else:
        return render_template("buy.html")

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    transactions = db.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY timestamp DESC", session["user_id"])
    return render_template("history.html", transactions=transactions)

@app.route("/password", methods=["GET", "POST"])
@login_required
def change_password():
    """Personal Touch: Change Password"""
    if request.method == "POST":
        old = request.form.get("old_password")
        new = request.form.get("new_password")

        user = db.execute("SELECT hash FROM users WHERE id = ?", session["user_id"])[0]
        if not check_password_hash(user["hash"], old):
            return apology("incorrect old password", 403)

        db.execute("UPDATE users SET hash = ? WHERE id = ?", generate_password_hash(new), session["user_id"])
        flash("Password Updated!")
        return redirect("/")
    return render_template("password.html")


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
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method=="POST":
        symbol=request.form.get("symbol")
        if not symbol:
            return apology("must provide symbol",400)
        quote=lookup(symbol)
        if not quote:
            return apology("invalid symbol",400)
        return render_template("quoted.html",quote=quote)
    else:
        return render_template("quote.html")





@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # 1. Validation
        if not username:
            return apology("must provide username", 400)
        elif not password:
            return apology("must provide password", 400)
        elif not confirmation:
            return apology("must provide confirmation", 400)
        elif password != confirmation:
            return apology("passwords do not match", 400)

        # 2. Hash the password
        hash_value = generate_password_hash(password)

        # 3. Insert into Database
        try:
            # We save the hash, never the raw password!
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash_value)
        except:
            # This triggers if the username already exists
            return apology("username already taken", 400)

        # 4. Redirect to login
        return redirect("/login")

    else:
        return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    user_id = session["user_id"]

    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares_to_sell = request.form.get("shares")

        # 1. Validation: Did they select a symbol?
        if not symbol:
            return apology("must provide symbol", 400)

        # 2. Validation: Is 'shares' a positive integer?
        try:
            shares_to_sell = int(shares_to_sell)
            if shares_to_sell <= 0:
                return apology("shares must be a positive integer", 400)
        except ValueError:
            return apology("shares must be a number", 400)

        # 3. Check if user owns enough shares
        # We use "or 0" because SUM() returns None if no rows match
        rows = db.execute("SELECT SUM(shares) AS total FROM transactions WHERE user_id = ? AND symbol = ?",
                          user_id, symbol)
        user_shares = rows[0]["total"] or 0

        if shares_to_sell > user_shares:
            return apology("too many shares", 400)

        # 4. Get current price and calculate profit
        stock = lookup(symbol)
        if not stock:
            return apology("invalid symbol", 400)

        price = stock["price"]
        transaction_value = price * shares_to_sell

        # 5. Update Database
        # Add cash to user's account
        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?", transaction_value, user_id)

        # Record the sale (inserting NEGATIVE shares so SUM(shares) remains accurate)
        db.execute("INSERT INTO transactions (user_id, symbol, shares, price, type) VALUES (?, ?, ?, ?, ?)",
                   user_id, symbol, -shares_to_sell, price, 'sell')

        flash("Sold!")
        return redirect("/")

    else:
        # GET: Get symbols for the dropdown menu (only stocks they currently own)
        symbols = db.execute("SELECT symbol FROM transactions WHERE user_id = ? GROUP BY symbol HAVING SUM(shares) > 0", user_id)
        return render_template("sell.html", symbols=symbols)
