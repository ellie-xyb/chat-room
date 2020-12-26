import sqlite3 
from flask import Flask, flash,  redirect, render_template, request, session, current_app, g, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required
import time

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

# Make the home page, show user's chat groups
@app.route('/')
@login_required
def index():
    groups_list = {}
    user_id = session["user_id"]

    # Connect db
    #  63,64line, WHERE column_2 IN (1,2,3);
    db = get_db()
    c = db.cursor()
    try:
        groups = c.execute("""SELECT group_id, user_id FROM group_user WHERE group_id IN 
                           (SELECT group_id FROM group_user WHERE user_id=?)
                            AND (user_id IN (SELECT fone FROM friends_list WHERE ftwo=?) 
                            OR user_id IN (SELECT ftwo FROM friends_list WHERE fone=?))""", 
                            [user_id, user_id, user_id]).fetchall()
        for group in groups:
            names = c.execute("SELECT username FROM users WHERE id=?", [group["user_id"]]).fetchall()  
            # Make a dictionary (also called object), group_id is the key, friend's name is the value 
            groups_list[group["group_id"]] = names[0]["username"] 
    except Exception as e:
        print(e)
        return "failed to make groups' list"              
    return render_template("index.html", groups_list = groups_list) 


@app.route("/start_chat/<friend_id>")
@login_required
def startchat(friend_id):    
    db = get_db()
    c = db.cursor()
    # See "a slow way" solution part to understand how to check if group exist or not"
    try:
        rows = c.execute(""" SELECT group_id FROM group_user WHERE user_id = ? AND group_id IN
                      (SELECT group_id FROM group_user WHERE group_id IN
                      (SELECT group_id FROM group_user WHERE user_id = ?)
                      GROUP BY group_id
                      HAVING count(user_id) =2 )""", [friend_id, session["user_id"]]).fetchall()

        if len(rows) == 1:
            return redirect(f'/chat/{rows[0]["group_id"]}')
    except Exception as e:
        print(e)
        return "failed to check if group exists or not"    
  

    # A slow way help tp think of the sql query
    # Use a boolean to check if the group is already exist or not 
    #exist = False 
    # try:
    #     user_groups = c.execute("SELECT group_id FROM group_user WHERE user_id=?",[session["user_id"]]).fetchall()
    #     for the_user_group in user_groups:
    #         duplicate_groups = c.execute("SELECT group_id FROM group_user WHERE user_id=? AND group_id=?",
    #                                      [friend_id, the_user_group["group_id"]]).fetchall()
    #         for duplicate_group in duplicate_groups:
    #             rows = c.execute("SELECT user_id FROM group_user WHERE group_id=?", duplicate_group["group_id"]).fetchall()
    #             if len(rows) == 2:
    #                 exist = True
    #                 break 


    name = f'{session["user_id"]}:{friend_id}'       
    try:
        c.execute("INSERT INTO group_ids(group_name) VALUES(?)",[name])
        db.commit()
        the_group_id = c.lastrowid
        group_user_id = [(the_group_id, session["user_id"]), (the_group_id, friend_id)]
        c.executemany("INSERT INTO group_user(group_id, user_id) VALUES (?, ?)", group_user_id)
        db.commit()
    except Exception as e:
        print(e)
        return "failed to make a chat group Or not support to chat with yourself yet"

    return redirect(f'/chat/{the_group_id}')


@app.route("/chat/<group_id>")
@login_required
def chatroom(group_id):   
    user_id = session["user_id"]
    db = get_db()
    c = db.cursor()
    try:
        #  Get friend's id and name from db, and pass them to the html
        rows = c.execute("SELECT user_id FROM group_user WHERE group_id=? AND user_id<>?", 
                        [group_id, user_id]).fetchall()
        friend_id = rows[0]["user_id"]
        name_rows = c.execute("SELECT username FROM users WHERE id=?", [friend_id]).fetchall()
        friend_name = name_rows[0]["username"]
    except Exception as e: 
        print(e)
        return "failed to get friend's id and name" 

    return render_template("chatroom.html", user_id = user_id, group_id = group_id, friend_name = friend_name)        
  

@app.route("/chatget/<group_id>", methods=["GET"])
@login_required
def chat_get(group_id): 

    db = get_db()
    c = db.cursor()
    try:
        rows = c.execute("SELECT content, user_id FROM messages WHERE group_id=? ORDER BY time ASC", 
                [group_id]).fetchall()
        check_new = c.lastrowid        
    except Exception as e: 
        print(e)
        return "failed to get chat messages"        
    # Make a list of object to keep data
    output = []
    for row in rows:
        output.append({"content": row["content"], "user_id": row["user_id"]})
    # Make a json string to keep all the data and return(response to the request) 
    return jsonify(output)



@app.route("/chatsave/<group_id>", methods=["POST"])
@login_required
def save_chat(group_id): 

    # Connect db, save the chatroom to db
    db = get_db()
    c = db.cursor()
    content = request.json.get("value")

    # Check if the content has value or not
    if not content:
        return "", 200

    # python time.time() 返回当前时间的时间戳（1970纪元后经过的浮点秒数）
    message_time = int(time.time()) 

    try:
        c.execute ("INSERT INTO messages (time, content, user_id, group_id) VALUES (?, ?, ?, ?)",
                   [message_time, content, session["user_id"], group_id])
        db.commit()
    except Exception as e: 
            print(e)
            return "failed to save the message" 
  
    # Flask return status code only 200/201 (success/created)
    return "", 201
        

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
    # Create a dictionary use friends_ids as key to friends_names
    # Create 2 lists to keep user's friends names and ids
    friends = {}
    friends_ids = []

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
            friends[friend_id] = friends_rows[0]["username"]

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
                            senders = senders, friends = friends, 
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


@app.route("/friends/remove/<friend_id>")
@login_required
def friends_remove(friend_id):

    #  Delete each other from their friends list
    db = get_db()
    c = db.cursor()
    try:
        c.execute("DELETE FROM friends_list WHERE fone=? AND ftwo=?",
                      [friend_id, session["user_id"]])
        db.commit()
        c.execute("DELETE FROM friends_list WHERE fone=? AND ftwo=?",
                      [session["user_id"], friend_id])
        db.commit()
    except sqlite3.IntegrityError:
        pass     
    except Exception as e: 
        print(e)
        return "failed to remove friend"

    # Redirect user to friends page
    return redirect("/friends")          


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
    except sqlite3.IntegrityError:
        pass     
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


