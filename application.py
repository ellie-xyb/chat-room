import sqlite3 
from flask import Flask, flash,  redirect, render_template, request, session, current_app, g
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required

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

# Connect with db (Define and Access the Database)
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect("chatroom.db",
            detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row

    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

# call the close_db function when finish each querry
app.teardown_appcontext(close_db)

@app.route('/')
@login_required
def index():
    return render_template("index.html") 


@app.route("/login", methods=["GET", "POST"])
def login():

    # Forget any user_id
    session.clear()

    # User reached route via POST 
    if request.method == "POST":

        # Ensure username and password was submitted
        if not request.form.get("username") or not request.form.get("password"):
            return "Must provide username and password"

        # Connect to db
        db = get_db()
        c = db.cursor()
        c.execute("SELECT * FROM users WHERE username = ?",[request.form.get("username")])
        rows = c.fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
           return "Invalid username and/or password"

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET 
    else:
        return render_template("login.html")


@app.route("/logout")
@login_required
def logout():

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():    

    # Forget any user_id
    #session.clear()

    # User reached route via POST 
    if request.method == "POST":

        # Ensure username and password was submitted
        if not request.form.get("username") or not request.form.get("password") or not request.form.get("confirmation"):
            return "Must provide and comfirm username and password"

        # Ensure the password was confirmed successfully
        elif request.form.get("password") != request.form.get("confirmation"):
            return "Please comfirm your password"

        db = get_db()
        c = db.cursor()
        # Query database for username
        rows = c.execute("SELECT * FROM users WHERE username=?",[request.form.get("username")]).fetchall()
    
        # Ensure the username didn't be taken already
        if len(rows) != 0:
            return "Name is already be used, must provide another username"

        nick_name = request.form.get("nickname")
        # If the user didn't give a nickname,then nickname = username
        if not nick_name:
            nick_name = request.form.get("username")    
        
        # Add the urser to the datebase
        c.execute("INSERT INTO users (username, nickname, hash) VALUES (?, ?, ?)",
                       [request.form.get("username"), nick_name, 
                       generate_password_hash(request.form.get("password"))])

        db.commit()
        id = c.lastrowid

        if id is None:
            return "Failed to add"

        # Remember which user has logged in
        session["user_id"] = id

        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("register.html")      


@app.route("/friends")
@login_required
def friends():

    # Connect to db and check if there are friend requests
    db = get_db()
    c = db.cursor() 
    rows = c.execute("SELECT from_id FROM friends_add WHERE to_id=?",[session["user_id"]]).fetchall() 

    # The way to make a list of dictionary(called object in js)
    # senders = []
    # sender = {}
    # sender["id"] = row["from_id"]
    # sender["name"] = new_rows[0]["username"]
    # senders.append(sender)


    #--------get all friend requests part----------
    # Create a dictionay
    senders = {} 

    # Skip if there is no new friend request
    if len(rows) <= 0:
        pass
    else:                              
        # Search db for the username of the request sender
        for row in rows:
            try:
                new_rows = c.execute("SELECT username FROM users WHERE id=?",[row["from_id"]]).fetchall()
                sender_id = row["from_id"]
                sender_name = new_rows[0]["username"]
                
                # Creat a dictionay of sender_id to sender_name 
                senders[sender_id] = sender_name   
            except:
                return "failed to get friend requesters"

    #--------get friends list part----------
    # Create 2 lists to keep user's friends names and ids
    friends_ids = []
    friends_names = []

    # Get all user's friends from friends_list table   
    try:
        rows_one = c.execute("SELECT fone FROM friends_list WHERE ftwo=?",[session["user_id"]]).fetchall()
        for row_one in rows_one:
            friends_ids.append(row_one["fone"])
        rows_two = c.execute("SELECT ftwo FROM friends_list WHERE fone=?", [session["user_id"]]).fetchall()
        for row_two in rows_two:
            friends_ids.append(row_two["ftwo"])
    except:
        return "failed to make friends' ids list"        

    # Get the friends names base on their ids, put names in 'friends_names' list    
    for friend_id in friends_ids:
        try:
            friends_rows = c.execute("SELECT username FROM users WHERE id=?", [friend_id]).fetchall()
            friends_names.append(friends_rows[0]["username"])
        # Can print db err in terminal
        except Exception as e: 
            print(e)
            return "failed to make friends' names"            

    #--------search friend part----------

    # Create a dictionary/(called object in js) with related_ids as key to related_names
    related_results = {}
    # Create a list to keep all the related ids
    related_ids = []
    # seperate the related ids and create 3 lists to keep them  
    are_friends = [] 
    not_yet = [] 
    userself = []

    # Get value of the search input when user try to search other users
    search_name = request.args.get("searchall")
        
    if search_name:
        search_name = '%' + search_name + '%'

    # Get all the related like usernames from db
    try:
        related_userrows = c.execute("SELECT username,id FROM users WHERE username LIKE ?",
                                    (search_name,)).fetchall()                           
        for result in related_userrows:
            # append the result to each list
            related_ids.append(result["id"])

            # add key and value into dictionary related_results
            related_results[result["id"]] = result["username"]

        # Seperate the related_results to 1-(friends) and 2-(not friends yet)

        # reuse friends_ids list to seperate the related_ids result
        for related_id in related_ids:
            if related_id == session["user_id"]:
                userself.append(related_id)
            elif related_id in friends_ids:
                are_friends.append(related_id)
            else:
                not_yet.append(related_id)
            
    except Exception as e:
        print(e)
        return "There is no result"    

        
    #--------show send friend request successfully part----------
    #add /friends?=add_success to show successfully add
    add_success = request.args.get("add_success") == "true"
    
    return render_template("friends.html", add_success = add_success, 
                            senders = senders, friends_names = friends_names, 
                            related_results = related_results, bool = bool,
                            are_friends = are_friends, not_yet = not_yet, 
                            search_name = search_name, userself = userself)    


@app.route("/friends/add", methods=["GET", "POST"])
@login_required
def friends_add():
    # User reached route via POST
    if request.method == "POST":

        # Check if provide friend's username
        if not request.form.get("add_username"):
            return "Must provide friend's username"

        # Cannot add user self 
        if request.form.get("add_username") == session["user_id"]:
            return "Sorry can't add yourself"    

        # Connect to db
        db = get_db()
        c = db.cursor()

        rows = c.execute("SELECT id, username FROM users WHERE username = ?",
                  [request.form.get("add_username")]).fetchall()

        # Check if there is a user under that username
        if len(rows) != 1:
            return "Check friend's username"    

        try:
            # Add the friends_add request to the db (table: friends_add)
            c.execute("INSERT INTO friends_add (from_id, to_id) VALUES (?, ?)",
                  [session["user_id"], rows[0]["id"]])  
            db.commit() 

            # Check if adding to the table successfully
            id = c.lastrowid 
            if id is None:
                return "Failed to add friends_add request"
            
        except sqlite3.IntegrityError:
            # Request already sent but won't add duplicate in the db also ignore err
            # (python do nothing when db error as unique on from_id and to_id)
            pass          

        # Redirect user to friends_add page
        return redirect("/friends?add_success=true")   
              
    else:        
        # User reached route via GET
        return render_template("friends_add.html")       


@app.route("/friends/sendfrequest/<the_to_id>")
@login_required
def friends_send_request(the_to_id):   

    # Sending friend request straightly without through '+' mark      
    db = get_db()
    c = db.cursor()
    try:
        c.execute("INSERT INTO friends_add (from_id, to_id) VALUES (?, ?)",
                   [session["user_id"], the_to_id])
        db.commit() 
    except sqlite3.IntegrityError:
        pass                     
    except Exception as e: 
        print(e)
        return "failed to send request"

    # Redirect user to friends_add page
    return redirect("/friends?add_success=true")                

@app.route("/friends/accept/<sender_id>")
@login_required
def friends_accept(sender_id):   

    # Add to friends_list when user press accept button of friend request
    # Connect to db and check if there are friend requests
    db = get_db()
    c = db.cursor()
    try:
        c.execute("INSERT INTO friends_list (fone, ftwo) VALUES (?, ?)",
                      [session["user_id"], sender_id])
        db.commit()                  
    except Exception as e: 
        print(e)
        return "failed to add to friends list(1)"    

    # After adding to friends list, delete the request line in friends_add table
    try:
        c.execute("DELETE FROM friends_add WHERE from_id=? AND to_id=?",
                      [sender_id, session["user_id"]])
        db.commit()
        c.execute("DELETE FROM friends_add WHERE from_id=? AND to_id=?",
                      [session["user_id"], sender_id])
        db.commit()
    except Exception as e: 
        print(e)
        return "failed to add to friends list(2)"    

    # Redirect user to friends page
    return redirect("/friends")   
        

@app.route("/friends/reject/<sender_id>")
@login_required
def friends_reject(sender_id):   
    
    # Delete the line in friends_add table if user reject the friend request
    # Connect to db and check if there are friend requests
    db = get_db()
    c = db.cursor()
    try:
        c.execute("DELETE FROM friends_add WHERE from_id=? AND to_id=?",
                      [sender_id, session["user_id"]])
        db.commit()
        c.execute("DELETE FROM friends_add WHERE from_id=? AND to_id=?",
                      [session["user_id"], sender_id])
        db.commit()
    except Exception as e: 
        print(e)
        return "failed to add to friends list(3)"

    # Redirect user to friends page
    return redirect("/friends")      


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return "Something is wrong"
 

# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)    


# Use a production WSGI server (use Waitress)
#if __name__ == "__main__":
#    from waitress import serve
#    serve(app, host="0.0.0.0", port=8080)


