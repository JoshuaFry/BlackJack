from flask import Flask, jsonify
from flask import Flask,request,render_template, Response, redirect
import uuid, functools, os, json
import pyrebase
from flask_socketio import SocketIO, emit, send
# https://getbootstrap.com/docs/4.3/getting-started/introduction/

src = "https://www.gstatic.com/firebasejs/5.8.3/firebase.js"

# TODO: Store config into environment variables
config = {
    "apiKey": os.environ['apiKey'],
    "authDomain": os.environ['authDomain'],
    "databaseURL": os.environ['databaseURL'],
    "projectId": os.environ['projectId'],
    "storageBucket": os.environ['bucket'],
    "messagingSenderId":  os.environ['messagingSenderId']
}

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()

app = Flask(__name__)
socketio = SocketIO(app)


def login_required(func):
    @functools.wraps(func)
    def verify_login(*args, **kwargs):
        if auth.current_user is not None:
            return func(*args, **kwargs)
        else:
            print("login_required: No User Found")
            return render_template("Login_Register.html", title="Homepage", user=is_user())
    return verify_login


@app.route('/')
def home():
    return render_template("Index.html", title="Homepage", user=is_user())


@app.route('/login_register')
def login_register():
    return render_template("Login_Register.html", title="Login", user=is_user())


@app.route('/find_game')
def find_game():
    return render_template("Game_Search.html", table_data=get_tables(), user=is_user())


@app.route('/register', methods=['POST'])
def register_user():
    email = request.form['email']
    password = request.form['password']
    userName = request.form['Username']
    auth.create_user_with_email_and_password(email, password)
    user = auth.sign_in_with_email_and_password(email, password)
    auth.refresh(user['refreshToken'])

    return create_base_user_data(userName)


@app.route('/updateBalance/', methods=['GET', 'POST'])
@login_required
def update_balance():
    userId = auth.current_user['localId']
    balance = db.child("users/" + userId + "/balance").get().val()  # TODO: Error check
    userData = dict(db.child("users/" + userId).get(auth.current_user['idToken']).val())  # TODO: Error check

    if request.form['amount'] == '':
        return render_template("Profile.html", name=userData['userName'], balance=balance, user=is_user())

    new_balance = int(request.form['amount']) + balance
    results = db.child("users/" + userId).update({"balance": new_balance})  # TODO: Error check
    return render_template("Profile.html", name=userData['userName'], balance=new_balance, user=is_user())


@app.route('/signin', methods=['POST'])
def signin_user():
    email = request.form['email']
    password = request.form['password']
    user = auth.sign_in_with_email_and_password(email,password)
    auth.refresh(user['refreshToken'])
    user_data = get_user_data()

    return render_template("Profile.html", name=user_data['userName'], balance=user_data['balance'], user=is_user())


def create_base_user_data(userName):
    user = auth.current_user

    data = {
        "userName": userName,
        "balance": 1000,
        "inGame": False
         }

    # TODO: Error check results
    results = db.child("users/" + user['localId']).set(data, user['idToken'])
    return render_template("Profile.html", name=auth.current_user['displayName'], balance=1000, user=is_user())


def get_user_data():
    # TODO: Error check
    user_data = dict(db.child("users/" + auth.current_user['localId']).get(auth.current_user['idToken']).val())
    return user_data


def get_tables():
    table_data = dict(db.child("tables/").get().val())  # TODO: Error Check
    for table in table_data.values():
        available_seats = 0
        for seat in table['seats']:
            if seat == 'empty':
                available_seats = available_seats + 1
        table['seats'] = available_seats
    return table_data


@app.route('/join_table/<table_id>', methods=['GET', 'POST'])
@login_required
def join_table(table_id):
    userId = auth.current_user['localId']
    seat_id = get_available_seatId(table_id)

    if seat_id == -1:
        return render_template("Game_Search.html", table_data=get_tables(), user=is_user())

    userName = get_user_data()['userName']
    table_results = db.child("tables/" + table_id + "/seats").update({seat_id: userName})  # TODO: Error check
    user_results = db.child("users/" + userId).update({"seatId": seat_id})

    stream = db.child("tables/" + table_id).stream(stream_handler)
    return render_template("Game_Table.html", table_id=table_id, user=is_user())


def get_available_seatId(table_id):
    seat_id = 0
    seats = db.child("tables/" + table_id + "/seats").get().val()  # TODO: Error check
    for i in range(len(seats)):
        if seats[i] == 'empty':
            return i
    return -1


@app.route('/leave_table/<table_id>', methods=['GET', 'POST'])
@login_required
def leave_table(table_id):
    user_seat_id = db.child("users/" + auth.current_user['localId'] + "/seatId").get().val()
    table_results = db.child("tables/" + table_id + "/seats").update({user_seat_id: "empty"})  # TODO: Error check
    return render_template("Game_Search.html", table_data=get_tables(), user=is_user())


def is_user():
    if auth.current_user is not None:
        return True
    else:
        return False


@socketio.on('my event')
def stream_handler(message):
    with app.app_context():
        print(message["event"])  # put
        print(message["path"])  # /-K7yGTTEp7O549EzTYtI
        print(message["data"])  # {'title': 'Pyrebase', "body": "etc..."}
        socketio.emit('data_changed', message, broadcast=True, json=True)


if __name__ == '__main__':
    socketio.run(app, debug=True)

