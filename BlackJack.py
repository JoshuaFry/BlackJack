from flask import Flask, request, render_template
import uuid, functools, os, random
import pyrebase
import time
from flask_socketio import SocketIO

src = "https://www.gstatic.com/firebasejs/5.8.3/firebase.js"

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


@app.route('/', methods=['GET'])
def home():
    # create_all_tables()
    return render_template("index.html", title="Homepage", user=is_user())


@app.route('/login_register', methods=['GET', 'POST'])
def login_register():
    return render_template("Login_Register.html", title="Login", user=is_user())


@app.route('/find_game', methods=['GET', 'POST'])
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
    try:
        user = auth.sign_in_with_email_and_password(email,password)
        auth.refresh(user['refreshToken'])
        user_data = get_user_data()
    except:
        message= "invalid credentials"
        return render_template("Login_Register.html",message=message)
    return render_template("Profile.html", name=user_data['userName'], balance=user_data['balance'], user=is_user())


@app.route('/logout', methods=['GET'])
def logout_user():
    auth.current_user = None
    return render_template("Index.html")



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


# Stream json changes from Firebase Real-Time DB path
def begin_data_stream(path):
    db.child(path).stream(stream_handler)
    return


# Method triggers on json changes - initialized from 'begin_data_stream(path)'
def stream_handler(message):
    with app.app_context():
        if message['event'] == 'patch':
            # return stream_patch(message)
            return stream_put(message)
        else:
            return stream_put(message)


# Retrieves json changes from Firebase to Game_table page via Flask-SocketIO
def stream_put(message):
    print(message)
    path = str(message["path"][1:]).split('/')
    if path[0] == 'seats':
        if path[2] == 'name':
            data = {'seat': path[1], 'name': message['data']}
            socketio.emit('seat_changed', data, broadcast=False, json=True)
        elif path[2] == 'bet':
            data = {'seat': path[1], 'bet': message['data']}
            socketio.emit('bet_update', data, broadcast=False, json=True)
        elif path[2] == 'balance':
            data = {'seat': path[1], 'balance': message['data']}
            socketio.emit('balance_update', data, broadcast=False, json=True)
        elif path[2] == 'hand':
            data = {'seat': path[1], 'hand': message['data']}
            socketio.emit('hand_update', data, broadcast=False, json=True)
    if path[0] == 'state':
        socketio.emit('state_changed', message['data'], broadcast=False)
    if path[0] == 'dealer':
        data = {'seat': 7, 'hand': message['data']}
        socketio.emit('hand_update',  data, broadcast=False, json=True)


# TODO: test if this case fires with two users if not remove function
# Sends json changes to Game_table page via Flask-SocketIO
def stream_patch(message):
    print(message)
    path = str(message["path"][1:]).split('/')
    if path[0] == 'seats':
        print("Seat Patch currently commented out")
         # handle_seat_data_change(message['data'])
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
        socketio.emit('hand_update', data, broadcast=False, json=True)
        return
    else:
        print("Player joined or left table")
        data = {'seat': int(seatId), 'name': data[seatId]['name']}
        socketio.emit('seat_changed', data, broadcast=False, json=True)


# Returns the current seat data for a given table_id in the DB
@socketio.on('get_seat_data')
def get_seat_data(table_id):
    seat_data = db.child("tables").child(table_id).child("seats").get(auth.current_user['idToken']).val()[1:]
    seat_names = []
    print(seat_data)
    print(seat_names)
    socketio.emit('seat_data_acquired', seat_data, broadcast=False)


@socketio.on('update_balance')
def update_user_balance(amt):
    user_data = get_user_data()
    balance = user_data['balance']
    seat_id = user_data['seatId']
    balance += amt
    user_id = auth.current_user['localId']
    db.child("users").child(user_id).child("bet").set(0)
    db.child("users").child(user_id).child("balance").set(balance)
    db.child("tables").child(user_id).child("seats").child(seat_id).child("bet").set(0)
    db.child("tables").child(user_id).child("seats").child(seat_id).child("balance").set(balance)
    return


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
    seat_id = get_user_data()['seatId']
    hand = get_current_hand(seat_id,table_id)
    if len(hand) == 0:
        return
    card = hit()
    hand.update(card)
    db.child("tables").child(table_id).child("seats").child(seat_id).child("hand").set(hand)


@socketio.on('get_hand')
def write_hand_to_database(table_id):
    hand = first_hand()
    seat_id = get_user_data()['seatId']
    db.child("tables").child(table_id).child("seats").child(seat_id).child("hand").set(hand)


@socketio.on('begin_betting')
def begin_betting(data):
    db.child("tables").child(data['table_id']).child("endBettingBy").set(data['end_bet_by'])
    db.child("tables").child(data['table_id']).child("state").set(-1)
    # socketio.emit('trigger_betting_timer', data['end_bet_by'], broadcast=False)


def dealer_begin_betting_round(table_id):
    FORTY_FIVE_SECONDS = (1000 * 45)
    end = int(round(time.time() * 1000)) + FORTY_FIVE_SECONDS
    print("No players ready")
    db.child("tables").child(table_id).child("endBettingBy").set(end)
    db.child("tables").child(table_id).child("state").set(-1)


@socketio.on('verify_game_state')
def verify_game_state(table_id):
    state = db.child("tables").child(table_id).child("state").get().val()
    if state == -1:
        end = db.child("tables").child(table_id).child("endBettingBy").get().val()
        socketio.emit('trigger_betting_timer', end, broadcast=False)
        print("trigger_betting_timer")
    else:
        socketio.emit('state_changed', state)


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


@socketio.on('pass_turn')
def pass_turn(data):
    current = data['seat']
    if current == 7:
        # return db.child("tables").child(data['table_id']).child("state").set(-2)
        return

    ready_players = get_ready_players(data['table_id'])
    next_turn = get_next_turn(ready_players, current)
    if next_turn == 7:
        print("Dealer's Turn")
        dealers_turn(data['table_id'])
    else:
        db.child("tables").child(data['table_id']).child("state").set(next_turn)


def get_next_turn(ready_players, current):
    next_turn = -2
    for i in range(len(ready_players)):
        if ready_players[i] == current:
            if i + 1 == len(ready_players):
                next_turn = 7
            else:
                next_turn = ready_players[i + 1]
    return next_turn


@socketio.on('check_win')
def check_win(table_id):
    user_data = get_user_data()
    hand = get_current_hand(user_data['seatId'], table_id)
    user_hand_value = get_hand_total(hand)
    if user_hand_value is None:
        return
    if user_hand_value == 21:
        win = user_data['bet'] * 3
        payout(win)
        info = "Black Jack Win $" + str(win) + "! Killer!"
        socketio.emit('info', info, broadcast=False)
    dealers_hand = dict(db.child("tables").child(table_id).child("dealer").child("hand").get().val())
    dealer_hand_value = get_hand_total(dealers_hand)
    if user_hand_value == dealer_hand_value:
        push = user_data['bet']
        payout(push)
        info = "Push $" + str(push) + ", it's a tie"
        socketio.emit('info', info, broadcast=False)
    elif user_hand_value > dealer_hand_value:
        win = user_data['bet'] * 2
        payout(win)
        info = "You Won $" + str(win) + "! Keep it up!"
        socketio.emit('info', info, broadcast=False)
    else:
        payout(0)
        info = "You lost $" + str(user_data['bet']) + ".... Sad"
        socketio.emit('info', info, broadcast=False)
    clear_user_hand_and_bet(table_id)


def payout(amt):
    userId = auth.current_user['localId']
    balance = get_user_data()['balance']
    balance += amt
    db.child("users").child(userId).child("bet").set(0)
    db.child("users").child(userId).child("balance").set(balance)


def clear_user_hand_and_bet(table_id):
    user_data = get_user_data()
    seat_id = user_data['seatId']
    db.child("tables").child(table_id).child("seats").child(seat_id).child("bet").set(0)
    db.child("tables").child(table_id).child("seats").child(seat_id).child("hand").set("empty")
    db.child("tables").child(table_id).child("seats").child(seat_id).child("balance").set(user_data['balance'])


def dealers_turn(table_id):
    hand = dict(db.child("tables").child(table_id).child("dealer").child("hand").get().val())
    card = hit()
    hand.update(card)
    while get_hand_total(hand) < 17:  # Make dealer hit until they are above 17
        card = hit()
        hand.update(card)
    db.child("tables").child(table_id).child("dealer").child("hand").set(hand)
    db.child("tables").child(table_id).child("state").set(-2)  # payout round
    dealer_begin_betting_round(table_id)


def get_hand_total(hand):
    total = 0
    aces = 0
    print("get_hand_total: Hand:" + str(hand))

    if isinstance(hand, str):
        return
    for k, v in hand.items():
        total += v
        if v == 11:
            aces += 1
    while total > 21 and aces > 0:  # Change value of Total if ace is present and value above 21
        total -= 10
        aces -= 1
        if aces == 0 & total > 21:
            return total
    return total


@socketio.on('deal_cards')
def deal_cards(table_id):
    ready_players = get_ready_players(table_id)
    non_ready_players = get_non_ready_players(table_id)
    seatId = get_user_data()['seatId']
    if len(ready_players) == 0:
        if non_ready_players[0] == seatId:
            print("No players Ready")
            dealer_begin_betting_round(table_id)
        return
    if get_user_data()['bet'] > 0:
        hand = first_hand()
        db.child("tables").child(table_id).child("seats").child(seatId).child("hand").set(hand)
    if ready_players[0] == get_user_data()['seatId']:
        one_card = hit()
        db.child("tables").child(table_id).child("dealer").child("hand").set(one_card)
        db.child("tables").child(table_id).child("state").set(ready_players[0])
    return


# Any player with a bet greater than 0
def get_ready_players(table_id):
    seat_data = db.child("tables").child(table_id).child("seats").get(auth.current_user['idToken']).val()[1:]
    ready_players = []
    for i in range(len(seat_data)):
        if seat_data[i]['bet'] > 0:
            print(seat_data[i])
            ready_players.append(i + 1)
    return ready_players


# Any player with a bet ==  0
def get_non_ready_players(table_id):
    seat_data = db.child("tables").child(table_id).child("seats").get(auth.current_user['idToken']).val()[1:]
    non_ready_players = []
    for i in range(len(seat_data)):
        if seat_data[i]['bet'] == 0:
            if seat_data[i]['name'] != 'empty':
                print(seat_data[i])
                non_ready_players.append(i + 1)
    return non_ready_players



def create_all_tables():
    for i in range(3):
        id = str(uuid.uuid4())
        data = {id: {"id": id,
                     "name": "blank",
                     "state": -2,
                     "endBettingBy": -1,
                     "dealer": {"hand": "empty"},
                     "seats": {1: {"hand": "empty", "name": "empty", "bet": 0, "balance": 0},
                        2: {"hand": "empty", "name": "empty", "bet": 0, "balance": 0},
                        3: {"hand": "empty", "name": "empty", "bet": 0, "balance": 0},
                        4: {"hand": "empty", "name": "empty", "bet": 0, "balance": 0},
                        5: {"hand": "empty", "name": "empty", "bet": 0, "balance": 0},
                        6: {"hand": "empty", "name": "empty", "bet": 0, "balance": 0}, }}}
        db.child("tables").update(data)


if __name__ == '__main__':
    socketio.run(app, debug=True)


