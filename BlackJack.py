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


@app.route('/profile', methods=['GET'])
@login_required
def view_profile():
    user_data = get_user_data()
    return render_template("Profile.html", name=user_data['userName'], balance=user_data['balance'], user=is_user())


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
        "seatId": -1
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
    seat_id = get_available_seatid(table_id)
    if seat_id == -1:
        return render_template("Game_Search.html", table_data=get_tables(), user=is_user())

    write_user_to_seat(table_id, seat_id)
    begin_data_stream("tables/" + table_id)
    return render_template("Game_Table.html", table_id=table_id, seat_id=seat_id, user_name=get_user_data()['userName'], user=is_user())


@login_required  # TODO: Error check
def write_user_to_seat(table_id, seat_id):
    userId = auth.current_user['localId']
    userName = get_user_data()['userName']
    table_results = db.child("tables/" + table_id + "/seats").update({seat_id: userName})
    user_results = db.child("users/" + userId).update({"seatId": seat_id})
    return


def get_available_seatid(table_id):
    seat_id = -1
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


def begin_data_stream(path):
    db.child(path).stream(stream_handler)
    return


def stream_handler(message):
    with app.app_context():
        if message['event'] == 'patch':
            return stream_patch(message)

        path = str(message["path"][1:]).split('/')
        if path[0] == 'seats':
            data = {'seat': path[1], 'name': message['data']}
            socketio.emit('seat_changed', data, broadcast=True, json=True)

        if path[0] == 'status':
            socketio.emit('status_changed', message['data'], broadcast=True)


def stream_patch(message):
    path = str(message["path"][1:]).split('/')
    if path[0] == 'seats':
        seatId = next(iter(message['data']))
        data = {'seat': int(seatId), 'name': message['data'][seatId]}
        socketio.emit('seat_changed', data, broadcast=True, json=True)
    if path[0] == 'status':
        print('Need to handle patch status')

@socketio.on('get_seat_data')
def get_seat_data(table_id):
    seat_data = db.child("tables/" + table_id + "/seats").get(auth.current_user['idToken']).val()
    print(seat_data)
    socketio.emit('seat_data_acquired', seat_data, broadcast=True)


@socketio.on('update_balance')
def update_user_balance(amt):
    return
# update firebase user table balance
# call emit to refresh the balance shown on users page


if __name__ == '__main__':
    socketio.run(app, debug=True)

