import itertools

from flask import Flask, jsonify
from flask import Flask,request,render_template, Response, redirect
import uuid, functools, os, json, random
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
    # return render_template("Index.html", title="Homepage", user=is_user())
    return render_template("index.html", title="Homepage", user=is_user())


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
    balance = db.child("users").child(userId).child("balance").get().val()  # TODO: Error check
    userData = dict(db.child("users").child(userId).get(auth.current_user['idToken']).val())  # TODO: Error check

    if request.form['amount'] == '':
        return render_template("Profile.html", name=userData['userName'], balance=balance, user=is_user())

    new_balance = int(request.form['amount']) + balance
    db.child("users").child(userId).child("balance").set(new_balance)  # TODO: Error check
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
        "seatId": -1,
        "bet": 0
         }

    # TODO: Error check results
    results = db.child("users").child(user['localId']).set(data, user['idToken'])
    return render_template("Profile.html", name=auth.current_user['displayName'], balance=1000, user=is_user())


def get_user_data():
    # TODO: Error check
    user_data = dict(db.child("users/" + auth.current_user['localId']).get(auth.current_user['idToken']).val())
    return user_data


def get_tables():
    table_data = dict(db.child("tables/").get().val())  # TODO: Error Check
    for table in table_data.values():
        available_seats = 0
        for seat in table['seats'][1:]:
            if seat['name'] == 'empty':
                available_seats = available_seats + 1
        table['seats'] = available_seats
    return table_data


@app.route('/join_table/<table_id>', methods=['GET', 'POST'])
@login_required
def join_table(table_id):
    seat_id = get_available_seatid(table_id)
    print(seat_id)
    if seat_id == -1:
        return render_template("Game_Search.html", table_data=get_tables(), user=is_user())

    write_user_to_seat(table_id, seat_id)
    begin_data_stream("tables/" + table_id)
    return render_template("Game_Table.html", table_id=table_id, seat_id=seat_id, user_name=get_user_data()['userName'], user=is_user())


@login_required  # TODO: Error check
def write_user_to_seat(table_id, seat_id):
    userId = auth.current_user['localId']
    user_data = get_user_data()
    userName = user_data['userName']
    balance = user_data['balance']
    db.child("tables").child(table_id).child("seats").child(seat_id).child("name").set(userName)
    db.child("tables").child(table_id).child("seats").child(seat_id).child("balance").set(balance)
    db.child("users").child(userId).child("seatId").set(seat_id)
    return


def get_available_seatid(table_id):
    seats = db.child("tables/" + table_id + "/seats").get().val()[1:]  # TODO: Error check
    for i in range(len(seats)):
        if seats[i]['name'] == 'empty':
            return i + 1
    return -1


@app.route('/leave_table/<table_id>', methods=['GET', 'POST'])
@login_required
def leave_table(table_id):
    seat_id = get_user_data()['seatId']
    db.child("tables").child(table_id).child("seats").child(seat_id).child("name").set("empty")
    db.child("tables").child(table_id).child("seats").child(seat_id).child("balance").set(0)
    db.child("tables").child(table_id).child("seats").child(seat_id).child("bet").set(0)
    db.child("tables").child(table_id).child("seats").child(seat_id).child("hand").set("empty")
    return render_template("Game_Search.html", table_data=get_tables(), user=is_user())


def is_user():
    if auth.current_user is not None:
        return True
    else:
        return False


# Stream RESTful json changes from Firebase Real-Time DB path
def begin_data_stream(path):
    db.child(path).stream(stream_handler)
    return


# Method triggers on json changes - initialized from 'begin_data_stream(path)'
def stream_handler(message):
    with app.app_context():
        if message['event'] == 'patch':
            return stream_patch(message)
        else:
            return stream_put(message)


# Sends the json changes from Firebase to Game_table page via Flask-SocketIO
def stream_put(message):
    print(message)
    path = str(message["path"][1:]).split('/')
    if path[0] == 'seats':
        if path[2] == 'name':
            data = {'seat': path[1], 'name': message['data']}
            socketio.emit('seat_changed', data, broadcast=True, json=True)
        elif path[2] == 'bet':
            data = {'seat': path[1], 'bet': message['data']}
            socketio.emit('bet_update', data, broadcast=True, json=True)
        elif path[2] == 'balance':
            data = {'seat': path[1], 'balance': message['data']}
            socketio.emit('balance_update', data, broadcast=True, json=True)
        elif path[2] == 'hand':
            data = {'seat': path[1], 'hand': message['data']}
            socketio.emit('hand_update', data, broadcast=True, json=True)
    if path[0] == 'state':
        print(path)
        # socketio.emit('status_changed', message['data'], broadcast=True)


# Sends json changes to Game_table page via Flask-SocketIO
def stream_patch(message):
    print(message)
    path = str(message["path"][1:]).split('/')
    if path[0] == 'seats':
        handle_seat_data_change(message['data'])
    if path[0] == 'status':
        print('Need to handle patch status')


def handle_seat_data_change(data):
    seatId = next(iter(data))
    if 'hand' in data[seatId]:
        print(data[seatId]['hand'])
        if type(data[seatId]['hand']) == list:
            data = {'seat': int(seatId), 'hand': data[seatId]['hand'][1:][0]}
        else:
            data = {'seat': int(seatId), 'hand': data[seatId]['hand']}
        socketio.emit('hand_update', data, broadcast=True, json=True)
        return
    else:
        print("Player joined or left table")
        data = {'seat': int(seatId), 'name': data[seatId]['name']}
        socketio.emit('seat_changed', data, broadcast=True, json=True)


# TODO: Alter this function and returning socket.emit to handles JSON seat data for 'balance' 'bet' 'name'
# Returns the current seat data for a given table_id in the DB
@socketio.on('get_seat_data')
def get_seat_data(table_id):
    seat_data = db.child("tables/" + table_id + "/seats").get(auth.current_user['idToken']).val()[1:]
    seat_names = []
    print(seat_data)
    [seat_names.append(i['name']) for i in seat_data]
    print(seat_names)
    socketio.emit('seat_data_acquired', seat_names, broadcast=True)


@socketio.on('update_balance')
def update_user_balance(amt):

    return
# update firebase user table balance
# call emit to refresh the balance shown on users page


def get_deck():
    deck = dict(db.child("deck/").get(auth.current_user['idToken']).val())
    return deck


def first_hand():
    deck = get_deck()
    x = random.choice(list(deck.items()))
    y = random.choice(list(deck.items()))
    print(x + y)
    return {x[0]: x[1], y[0]: y[1]}


def get_current_hand(seat_id, table_id):
    return db.child("tables").child(table_id).child("seats").child(seat_id).child("hand").get().val()


def hit():
    deck = get_deck()
    z = random.choice(list(deck.items()))
    return {z[0]: z[1]}


@socketio.on('hit')
def write_hand_to_database(table_id):
    card = hit()
    seat_id = get_user_data()['seatId']
    hand = get_current_hand(seat_id,table_id)
    hand.update(card)
    print("new hand:",hand)
    db.child("tables").child(table_id).child("seats").child(seat_id).child("hand").set(hand)


@socketio.on('get_hand')
def write_hand_to_database(table_id):
    hand = first_hand()
    seat_id = get_user_data()['seatId']
    db.child("tables").child(table_id).child("seats").child(seat_id).child("hand").set(hand)


@socketio.on('begin_betting')
def begin_betting(data):
    db.child("tables/" + data['table_id'] + "/endBettingBy").set(data['end_bet_by'])
    db.child("tables/" + data['table_id'] + "/state").set(-2)
    socketio.emit('trigger_betting_timer', data['end_bet_by'], broadcast=True)


@socketio.on('place_bet')
def place_bet(data):
    bet = int(data['bet'])
    table_id = data['table_id']
    user_data = get_user_data()
    balance = user_data['balance']
    seat_id = user_data['seatId']
    userId = auth.current_user['localId']
    balance -= bet
    db.child("users").child(userId).child("bet").set(bet)
    db.child("users").child(userId).child("balance").set(balance)
    db.child("tables").child(table_id).child("seats").child(seat_id).child("bet").set(bet)
    db.child("tables").child(table_id).child("seats").child(seat_id).child("balance").set(balance)
    print(data)

@socketio.on('deal_cards')
def deal_cards(table_id):
    seat_data = db.child("tables/" + table_id + "/seats").get(auth.current_user['idToken']).val()[1:]
    seat_names = []
    #proper format to access bet is seat_data[1]['bet']
    if seat_data[1]['bet'] > 0:
        [seat_names.append(i['name'])for i in seat_data]
    print(seat_names)

    return


# TODO: Grab all seat Id's who's bets are > 0
def get_ready_players(table_id):
    seat_data = db.child("tables/" + table_id + "/seats").get(auth.current_user['idToken']).val()[1:]
    seat_names = []
    print(seat_data)
    [seat_names.append(i['name']) for i in seat_data ]
    print(seat_names)


def create_all_tables():
    for i in range(3):
        id = str(uuid.uuid4())
        data = {id: {"id": id,
                     "name": "blank",
                     "state": -2,
                     "endBettingBy": -1,
                     "seats": {1: {"hand": "empty", "name": "empty", "bet": 0, "balance": 0},
                        2: {"hand": "empty", "name": "empty", "bet": 0, "balance": 0},
                        3: {"hand": "empty", "name": "empty", "bet": 0, "balance": 0},
                        4: {"hand": "empty", "name": "empty", "bet": 0, "balance": 0},
                        5: {"hand": "empty", "name": "empty", "bet": 0, "balance": 0},
                        6: {"hand": "empty", "name": "empty", "bet": 0, "balance": 0}, }}}
        db.child("tables").update(data)


if __name__ == '__main__':
    socketio.run(app, debug=True)


