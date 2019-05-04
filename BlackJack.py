from gevent import monkey
monkey.patch_all()
import pyrebase
from flask import Flask, request, render_template
import uuid, functools, os, random
import time
from flask_socketio import SocketIO, join_room, leave_room, emit
import threading

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
auth = [firebase.auth() for i in range(36)]
db = firebase.database()
app = Flask(__name__)
socketio = SocketIO(app)
my_stream = None
all_streams = {}
stream_threads = {}

def login_required(func):
    @functools.wraps(func)
    def verify_login(*args, **kwargs):
        i = None
        for k, v in kwargs.items():
            if k == "i":
                i = int(v)
        if i is None:
            print("login_required: No User Found")
            return render_template("Login_Register.html", title="Homepage", user=is_user(i))
        if auth[i].current_user is not None:
            return func(*args, **kwargs)
        else:
            print("login_required: No User Found")
            return render_template("Login_Register.html", title="Homepage", user=is_user(i))
    return verify_login


def get_empty_client_index():
    for i in range(len(auth)):
        if auth[int(i)].current_user is None:
            return i
    # TODO: show that the server is full


@app.route('/', methods=['GET'])
def home():
    return render_template("index.html", title="Homepage", user=False)


@app.route('/login_register', methods=['GET', 'POST'])
def login_register():
    i = get_empty_client_index()
    return render_template("Login_Register.html", title="Login", user=is_user(i), auth=i)


@app.route('/find_game/<i>', methods=['GET', 'POST'])
def find_game(i):
    return render_template("Game_Search.html", table_data=get_tables(), user=is_user(i), auth=i)


@app.route('/register/<i>', methods=['POST'])
def register_user(i):
    email = request.form['email']
    password = request.form['password']
    userName = request.form['Username']
    auth[int(i)].create_user_with_email_and_password(email, password)
    user = auth[int(i)].sign_in_with_email_and_password(email, password)
    auth[int(i)].refresh(user['refreshToken'])

    return create_base_user_data(i, userName)


@app.route('/updateBalance/<i>', methods=['GET', 'POST'])
@login_required
def update_balance(i):
    userId = auth[int(i)].current_user['localId']
    balance = db.child("users").child(userId).child("balance").get().val()  # TODO: Error check
    userData = dict(db.child("users").child(userId).get(auth[int(i)].current_user['idToken']).val())  # TODO: Error check
    admin = False
    if 'admin' in userData:
        admin = True
    if request.form['amount'] == '':
        return render_template("Profile.html", name=userData['userName'], balance=balance, user=is_user(i), admin=admin, auth=i)

    new_balance = int(request.form['amount']) + balance
    db.child("users").child(userId).child("balance").set(new_balance)  # TODO: Error check
    return render_template("Profile.html", name=userData['userName'], balance=new_balance, user=is_user(i), admin=admin, auth=i)


@app.route('/profile/<i>', methods=['GET'])
@login_required
def view_profile(i):
    user_data = get_user_data(i)
    admin = False
    if 'admin' in user_data:
        admin = True
    return render_template("Profile.html", name=user_data['userName'], balance=user_data['balance'], user=is_user(i), admin=admin, auth=i)


@app.route('/refresh-data-streams/<i>', methods=['POST'])
@login_required
def refresh_data_streams(i):
    user_data = get_user_data(i)
    admin = False
    if 'admin' in user_data:
        admin = True
        refresh_data_streams()
    return render_template("Profile.html", name=user_data['userName'], balance=user_data['balance'], user=is_user(i), admin=admin, auth=i)


@app.route('/create-all-streams/<i>', methods=['POST'])
@login_required
def create_all_streams(i):
    create_streams()
    user_data = get_user_data(i)
    admin = False
    if 'admin' in user_data:
        admin = True
    return render_template("Profile.html", name=user_data['userName'], balance=user_data['balance'], user=is_user(i), admin=admin, auth=i)


@app.route('/signin', methods=['POST'])
def signin_user():
    email = request.form['email']
    password = request.form['password']
    i = get_empty_client_index()
    try:
        user = auth[int(i)].sign_in_with_email_and_password(email, password)
        auth[int(i)].refresh(user['refreshToken'])
        user_data = get_user_data(i)
    except:
        message = "invalid credentials"
        return render_template("Login_Register.html", message=message)
    admin = False
    if 'admin' in user_data:
        admin = True
    return render_template("Profile.html", name=user_data['userName'], balance=user_data['balance'], user=is_user(i),
                           admin=admin, auth=i)


@app.route('/logout/<i>', methods=['GET'])
def logout_user(i):
    auth[int(i)].current_user = None
    return render_template("index.html")


def create_base_user_data(i, userName):
    user = auth[int(i)].current_user

    data = {
        "userName": userName,
        "balance": 1000,
        "seatId": -1,
        "bet": 0
         }

    # TODO: Error check results
    results = db.child("users").child(user['localId']).set(data, user['idToken'])
    return render_template("Profile.html", name=auth[int(i)].current_user['displayName'], balance=1000, user=is_user(i), auth=i)


def get_user_data(i):
    # TODO: Error check
    user_data = dict(db.child("users/" + auth[int(i)].current_user['localId']).get(auth[int(i)].current_user['idToken']).val())
    return user_data


def get_tables():
    table_data = dict(db.child("tables/").get().val())
    for table in table_data.values():
        available_seats = 0
        for seat in table['seats'][1:]:
            if seat['name'] == 'empty':
                available_seats = available_seats + 1
        table['seats'] = available_seats
    return table_data


@app.route('/join_table/<i>/<table_id>', methods=['GET', 'POST'])
@login_required
def join_table(i, table_id):
    seat_id = get_available_seatid(table_id)
    table_name = db.child("tables").child(table_id).child("name").get().val()
    print(seat_id)
    if seat_id == -1:
        return render_template("Game_Search.html", table_data=get_tables(), user=is_user(i), auth=i)

    write_user_to_seat(i, table_id, seat_id)
    # begin_data_stream("tables/" + table_id)  #TODO: Refresh Stream When First User Joins a table
    return render_template("Game_Table.html",
                           table_id=table_id, seat_id=seat_id, user_name=get_user_data(i)['userName'],
                           table_name=table_name, user=is_user(i), auth=i)


def write_user_to_seat(i, table_id, seat_id):
    print("writing user to seat")
    userId = auth[int(i)].current_user['localId']
    user_data = get_user_data(i)
    userName = user_data['userName']
    balance = user_data['balance']
    db.child("tables").child(table_id).child("seats").child(seat_id).child("name").set(userName)
    db.child("tables").child(table_id).child("seats").child(seat_id).child("balance").set(balance)
    db.child("users").child(userId).child("seatId").set(seat_id)
    db.child("users").child(userId).child("tableId").set(table_id)
    return


def get_available_seatid(table_id):
    seats = db.child("tables/" + table_id + "/seats").get().val()[1:]  # TODO: Error check
    for i in range(len(seats)):
        if seats[i]['name'] == 'empty':
            return i + 1
    return -1


@socketio.on('leave_table')
def leave_table(data):
    i = data['auth']
    table_id = data['table_id']
    seat_id = get_user_data(i)['seatId']
    db.child("tables").child(table_id).child("seats").child(seat_id).child("name").set("empty")
    db.child("tables").child(table_id).child("seats").child(seat_id).child("balance").set(0)
    db.child("tables").child(table_id).child("seats").child(seat_id).child("bet").set(0)
    db.child("tables").child(table_id).child("seats").child(seat_id).child("hand").set("empty")
    on_leave(data)
    return render_template("Game_Search.html", table_data=get_tables(), user=is_user(i), auth=i)


@app.route('/leave_table/<i>/<table_id>')
def leave_table(i, table_id):
    seat_id = get_user_data(i)['seatId']
    db.child("tables").child(table_id).child("seats").child(seat_id).child("name").set("empty")
    db.child("tables").child(table_id).child("seats").child(seat_id).child("balance").set(0)
    db.child("tables").child(table_id).child("seats").child(seat_id).child("bet").set(0)
    db.child("tables").child(table_id).child("seats").child(seat_id).child("hand").set("empty")
    # close_data_stream("tables/" + table_id)
    return render_template("Game_Search.html", table_data=get_tables(), user=is_user(i), auth=i)


def is_user(i):
    if i is None:
        return False
    if auth[int(i)].current_user is not None:
        return True
    else:
        return False


# Stream json changes from Firebase Real-Time DB path
def begin_data_stream(path):
    global my_stream
    global all_streams
    global stream_threads
    if path in all_streams:
        close_data_stream(path)

    my_stream = db.child(path).stream(stream_put)
    t_id = path.split('/')[1:][0]
    thread = {t_id: my_stream.thread.name}
    stream_threads.update(thread)
    stream = {path: my_stream}
    all_streams.update(stream)
    return


def close_data_stream(path):
    global my_stream
    global all_streams
    my_stream = all_streams[path]
    my_stream.close()
    return


def refresh_data_streams():
    global all_streams
    for k, v in all_streams.items():
        begin_data_stream(k)


def get_table_by_thread(thread):
    global stream_threads
    print(thread)
    print
    for k in stream_threads:
        if stream_threads[k] == thread:
            return k
    print("get_table_by_thread: something went wrong")


# Retrieves json changes from Firebase to Game_table page via Flask-SocketIO
def stream_put(message):
    # table_id = get_user_data()['tableId']
    table_id = get_table_by_thread(threading.current_thread().name)
    print(table_id)
    with app.app_context():
        print(message)
        path = str(message["path"][1:]).split('/')
        if path[0] == 'seats':
            if path[2] == 'name':
                data = {'seat': path[1], 'name': message['data']}
                socketio.emit('seat_changed', data, room=table_id, broadcast=True, json=True)
            elif path[2] == 'bet':
                data = {'seat': path[1], 'bet': message['data']}
                socketio.emit('bet_update', data, room=table_id, broadcast=True, json=True)
            elif path[2] == 'balance':
                data = {'seat': path[1], 'balance': message['data']}
                socketio.emit('balance_update', data, room=table_id, broadcast=True, json=True)
            elif path[2] == 'hand':
                data = {'seat': path[1], 'hand': message['data']}
                socketio.emit('hand_update', data, room=table_id, broadcast=True, json=True)
            elif path[2] == 'split':
                data = {'seat': path[1], 'hand': message['data']}
                socketio.emit('split_hand_update', data, room=table_id, broadcast=True, json=True)
            elif path[2] == 'sbet':
                data = {'seat': path[1], 'bet': message['data']}
                socketio.emit('sbet_update', data, room=table_id, broadcast=True, json=True)
        if path[0] == 'state':
            socketio.emit('state_changed', message['data'], room=table_id)
        if path[0] == 'dealer':
            data = {'seat': 7, 'hand': message['data']}
            socketio.emit('hand_update', data, room=table_id, broadcast=True, json=True)


# Returns the current seat data for a given table_id in the DB
@socketio.on('get_seat_data')
def get_seat_data(data):
    i = data['auth']
    table_id = data['table_id']
    seat_data = db.child("tables").child(table_id).child("seats").get(auth[int(i)].current_user['idToken']).val()[1:]
    emit('seat_data_acquired', seat_data)  # broadcast=False) #  room=table_id)


@socketio.on('update_balance')
def update_user_balance(data):
    i = data['auth']
    amt = data['amt']
    user_data = get_user_data(i)
    balance = user_data['balance']
    seat_id = user_data['seatId']
    balance += amt
    user_id = auth[int(i)].current_user['localId']
    db.child("users").child(user_id).child("bet").set(0)
    db.child("users").child(user_id).child("balance").set(balance)
    db.child("tables").child(user_id).child("seats").child(seat_id).child("bet").set(0)
    db.child("tables").child(user_id).child("seats").child(seat_id).child("balance").set(balance)
    return


def get_deck():
    deck = dict(db.child("deck/").get().val())
    return deck


def first_hand():
    deck = get_deck()
    x = random.choice(list(deck.items()))
    y = random.choice(list(deck.items()))
    print(x + y)
    return {x[0]: x[1], y[0]: y[1]}


def get_current_hand(seat_id, table_id):
    return db.child("tables").child(table_id).child("seats").child(seat_id).child("hand").get().val()

def get_split_hand(seat_id, table_id):
    return db.child("tables").child(table_id).child("seats").child(seat_id).child("split").get().val()

def hit():
    deck = get_deck()
    z = random.choice(list(deck.items()))
    return {z[0]: z[1]}


@socketio.on('hit')
def write_hand_to_database(data):
    i = data['auth']
    table_id = data['table_id']
    seat_id = get_user_data(i)['seatId']
    hand = get_current_hand(seat_id, table_id)
    if len(hand) == 0:
        return
    if get_hand_total(hand) >= 21:
        emit('info', "You can not Hit")
        return
    card = hit()
    hand.update(card)
    db.child("tables").child(table_id).child("seats").child(seat_id).child("hand").set(hand)


@socketio.on('split_hit')
def split_hit(data):
    i = data['auth']
    table_id = data['table_id']
    seat_id = get_user_data(i)['seatId']
    hand = get_split_hand(seat_id, table_id)
    if len(hand) == 0:
        return
    if get_hand_total(hand) >= 21:
        emit('split_info', "You can not Hit")
        return
    card = hit()
    hand.update(card)
    db.child("tables").child(table_id).child("seats").child(seat_id).child("split").set(hand)


@socketio.on('get_hand')
def write_hand_to_database(data):
    i = data['auth']
    table_id = data['table_id']
    hand = first_hand()
    seat_id = get_user_data(i)['seatId']
    db.child("tables").child(table_id).child("seats").child(seat_id).child("hand").set(hand)


@socketio.on('begin_betting')
def begin_betting(data):
    db.child("tables").child(data['table_id']).child("endBettingBy").set(data['end_bet_by'])
    db.child("tables").child(data['table_id']).child("state").set(-9)
    db.child("tables").child(data['table_id']).child("state").set(-1)
    print("Begin Betting, -1")


def dealer_begin_betting_round(table_id):
    FORTY_FIVE_SECONDS = (1000 * 45)
    end = int(round(time.time() * 1000)) + FORTY_FIVE_SECONDS
    db.child("tables").child(table_id).child("endBettingBy").set(end)
    db.child("tables").child(table_id).child("state").set(-9)
    db.child("tables").child(table_id).child("state").set(-1)
    print("Dealer Began Betting, -1")


@socketio.on('verify_game_state')
def verify_game_state(table_id):
    state = db.child("tables").child(table_id).child("state").get().val()
    if state == -1:
        end = db.child("tables").child(table_id).child("endBettingBy").get().val()
        emit('trigger_betting_timer', end)  #  room=table_id, broadcast=False)
        print("trigger_betting_timer")
    else:
        emit('state_changed', state)  #  room=table_id, broadcast=False)


@socketio.on('place_bet')
def place_bet(data):
    i = data['auth']
    bet = int(data['bet'])
    table_id = data['table_id']
    user_data = get_user_data(i)
    balance = user_data['balance']
    seat_id = user_data['seatId']
    userId = auth[int(i)].current_user['localId']
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
    elif next_turn == 0:
        print("no players found")
        dealers_turn(data['table_id'])
    else:
        db.child("tables").child(data['table_id']).child("state").set(next_turn)


def get_next_turn(ready_players, current):
    next_turn = 0
    for i in range(len(ready_players)):
        if ready_players[i] == current:
            if i + 1 == len(ready_players):
                next_turn = 7
            else:
                next_turn = ready_players[i + 1]
    return next_turn


def check_split_win(user_hand_value, data):
    i = data['auth']
    table_id = data['table_id']
    user_data = get_user_data(i)
    if user_hand_value is None:
        return
    if user_hand_value == 21:
        win = user_data['sbet'] * 3
        payout(i, win)
        return "Top Hand: Black Jack Win $" + str(win) + "! Killer!"
    dealers_hand = dict(db.child("tables").child(table_id).child("dealer").child("hand").get().val())
    dealer_hand_value = get_hand_total(dealers_hand)
    if user_hand_value == dealer_hand_value:
        push = user_data['sbet']
        payout(i, push)
        return "Top Hand: Push $" + str(push) + ", it's a tie"
    elif dealer_hand_value < user_hand_value <= 21:
        win = user_data['sbet'] * 2
        payout(i, win)
        return "Top Hand: You Won $" + str(win) + "! Keep it up!"
    elif dealer_hand_value > 21 >= user_hand_value:
        win = user_data['sbet'] * 2
        payout(i, win)
        return "Top Hand: You Won $" + str(win) + "! Keep it up!"
    else:
        payout(i, 0)
        return "Top Hand: You lost $" + str(user_data['sbet']) + ".... Sad"


@socketio.on('check_win')
def check_win(data):
    i = data['auth']
    table_id = data['table_id']
    user_data = get_user_data(i)
    hand = get_current_hand(user_data['seatId'], table_id)
    isSplit = False
    if has_split_hand(user_data['seatId'], table_id):
        split_hand = get_split_hand(user_data['seatId'], table_id)
        split_value = get_hand_total(split_hand)
        split_win_info = check_split_win(split_value, data)
        emit('split_info', split_win_info)
        clear_user_hand_and_bet_split(i, table_id)
        isSplit = True
    user_hand_value = get_hand_total(hand)
    if user_hand_value is None:
        return
    if user_hand_value == 21:
        win = user_data['bet'] * 3
        payout(i, win)
        info = "Black Jack Win $" + str(win) + "! Killer!"
        emit('info', info)
    dealers_hand = dict(db.child("tables").child(table_id).child("dealer").child("hand").get().val())
    dealer_hand_value = get_hand_total(dealers_hand)
    if user_hand_value == dealer_hand_value:
        push = user_data['bet']
        payout(i, push)
        info = "Push $" + str(push) + ", it's a tie"
        emit('info', info)  # ,   room=table_id, broadcast=False)
    elif dealer_hand_value < user_hand_value <= 21:
        win = user_data['bet'] * 2
        payout(i, win)
        info = "You Won $" + str(win) + "! Keep it up!"
        emit('info', info)  # ,   room=table_id, broadcast=False)
    elif dealer_hand_value > 21 >= user_hand_value:
        win = user_data['bet'] * 2
        payout(i, win)
        info = "You Won $" + str(win) + "! Keep it up!"
        emit('info', info)  # ,   room=table_id, broadcast=False)
    else:
        payout(i, 0)
        info = "You lost $" + str(user_data['bet']) + ".... Sad"
        emit('info', info)  # ,    room=table_id, broadcast=False)
    clear_user_hand_and_bet(i, table_id)


def payout(i, amt):
    userId = auth[int(i)].current_user['localId']
    balance = get_user_data(i)['balance']
    balance += amt
    db.child("users").child(userId).child("bet").set(0)
    db.child("users").child(userId).child("balance").set(balance)


def clear_user_hand_and_bet(i, table_id):
    user_data = get_user_data(i)
    seat_id = user_data['seatId']
    db.child("tables").child(table_id).child("seats").child(seat_id).child("bet").set(0)
    db.child("tables").child(table_id).child("seats").child(seat_id).child("hand").set("empty")
    db.child("tables").child(table_id).child("seats").child(seat_id).child("balance").set(user_data['balance'])


def clear_user_hand_and_bet_split(i, table_id):
    user_data = get_user_data(i)
    seat_id = user_data['seatId']
    db.child("tables").child(table_id).child("seats").child(seat_id).child("sbet").set(0)
    db.child("tables").child(table_id).child("seats").child(seat_id).child("split").set("empty")


def dealers_turn(table_id):
    print("Its the dealer turn")
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
def deal_cards(data):
    i = data['auth']
    table_id = data['table_id']
    ready_players = get_ready_players(table_id)
    non_ready_players = get_non_ready_players(table_id)
    seatId = get_user_data(i)['seatId']
    if len(ready_players) == 0:
        if len(non_ready_players) > 0:
            if non_ready_players[0] == seatId:
                print("No players Ready")
                dealer_begin_betting_round(table_id)
            return
    if get_user_data(i)['bet'] > 0:
        hand = first_hand()
        db.child("tables").child(table_id).child("seats").child(seatId).child("hand").set(hand)
    if ready_players[0] == get_user_data(i)['seatId']:
        one_card = hit()
        db.child("tables").child(table_id).child("dealer").child("hand").set(one_card)
        db.child("tables").child(table_id).child("state").set(ready_players[0])
    return


# Any player with a bet greater than 0
def get_ready_players(table_id):
    seat_data = db.child("tables").child(table_id).child("seats").get().val()[1:]
    time.sleep(2)
    ready_players = []
    for i in range(len(seat_data)):
        if seat_data[i]['bet'] > 0:
            ready_players.append(i + 1)
    return ready_players


# Any player with a bet ==  0
def get_non_ready_players(table_id):
    seat_data = db.child("tables").child(table_id).child("seats").get().val()[1:]
    non_ready_players = []
    for i in range(len(seat_data)):
        if seat_data[i]['bet'] == 0:
            if seat_data[i]['name'] != 'empty':
                print(seat_data[i])
                non_ready_players.append(i + 1)
    return non_ready_players


@socketio.on('join')
def on_join(data):
    i = data['auth']
    table_id = data['table_id']
    username = get_user_data(i)['userName']
    join_room(table_id)
    print(username + ' has entered the room. ' + table_id)


def on_leave(data):
    i = data['auth']
    table_id = data['table_id']
    username = get_user_data(i)['userName']
    leave_room(table_id)
    print(username + ' has left the room. ' + table_id)


@socketio.on('split_hand')
def split_hand(data):
    i = data['auth']
    table_id = data['table_id']
    user_data = get_user_data(i)
    userId = auth[int(i)].current_user['localId']
    seat_id = user_data['seatId']
    bet = user_data['bet']
    balance = user_data['balance'] - bet
    hand1 = get_current_hand(seat_id, table_id)
    new_hand1 = {}
    new_hand2 = {}
    key, val = hand1.popitem()
    new_hand1.update({key: val})
    key, val = hand1.popitem()
    new_hand2.update({key: val})
    new_hand1.update(hit())
    new_hand2.update(hit())
    db.child("users").child(userId).child("sbet").set(bet)
    db.child("users").child(userId).child("balance").set(balance)
    db.child("tables").child(table_id).child("seats").child(seat_id).child("sbet").set(bet)
    db.child("tables").child(table_id).child("seats").child(seat_id).child("hand").set(new_hand1)
    db.child("tables").child(table_id).child("seats").child(seat_id).child("split").set(new_hand2)
    db.child("tables").child(table_id).child("seats").child(seat_id).child("balance").set(balance)
    emit('enable_split')


def has_split_hand(seat_id, table_id):
    hand = db.child("tables").child(table_id).child("seats").child(seat_id).child("split").get().val()
    if isinstance(hand, str):
        return False
    else:
        return True


def create_all_tables():
    names = ["Flamingo", "Caesar's Palace", "Back Alley Gamble",
             "Sketchy Basement In China Town", "Mafia Game Night", "Worst Pod in the Pin"]

    for i in range(6):
        id = str(uuid.uuid4())
        data = {id: {"id": id,
                     "name": names[i],
                     "state": -2,
                     "endBettingBy": -1,
                     "dealer": {"hand": "empty"},
                     "seats": {1: {"hand": "empty", "name": "empty", "bet": 0, "balance": 0},
                        2: {"hand": "empty", "sbet": 0, "split": "empty", "name": "empty", "bet": 0, "balance": 0},
                        3: {"hand": "empty", "sbet": 0, "split": "empty", "name": "empty", "bet": 0, "balance": 0},
                        4: {"hand": "empty", "sbet": 0, "split": "empty", "name": "empty", "bet": 0, "balance": 0},
                        5: {"hand": "empty", "sbet": 0, "split": "empty", "name": "empty", "bet": 0, "balance": 0},
                        6: {"hand": "empty", "sbet": 0, "split": "empty", "name": "empty", "bet": 0, "balance": 0}, }}}
        db.child("tables").update(data)


def create_streams():
    table_data = dict(db.child("tables/").get().val())
    for table in table_data:
        begin_data_stream("tables/" + table)


if __name__ == '__main__':
    socketio.run(app)
