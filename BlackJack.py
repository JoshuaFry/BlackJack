from flask import Flask
from flask import Flask,request,render_template
import uuid, functools, os, json
import pyrebase
# https://getbootstrap.com/docs/4.3/getting-started/introduction/

src = "https://www.gstatic.com/firebasejs/5.8.3/firebase.js"

# TODO: Store config into environment variables
config = {
    "apiKey": "AIzaSyAEGhM6e4oYckUrj-25itp6IbFgYfffkH8",
    "authDomain": "blackjack-22b3a.firebaseapp.com",
    "databaseURL": "https://blackjack-22b3a.firebaseio.com",
    "projectId": "blackjack-22b3a",
    "storageBucket": "blackjack-22b3a.appspot.com",
    "messagingSenderId": "509859351763"
}

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()

app = Flask(__name__)


def login_required(func):
    @functools.wraps(func)
    def verify_login(*args, **kwargs):
        if auth.current_user is not None:
            return func(*args, **kwargs)
        else:
            print("login_required: No User Found")
            return render_template("Account_Page.html", title="Homepage")
    return verify_login


@app.route('/')
def home():
    return render_template("index.html", title="Homepage")


@app.route('/account')
def account_page():
    return render_template("Account_Page.html", title="Login")


@app.route('/about')
def about_page():
    return render_template("Game_Search.html", table_data=get_tables())


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
        return render_template("User_info.html", name=userData['userName'], balance=balance)

    new_balance = int(request.form['amount']) + balance
    results = db.child("users/" + userId).update({"balance": new_balance})  # TODO: Error check
    return render_template("User_info.html", name=userData['userName'], balance=new_balance)


@app.route('/signin', methods=['POST'])
def signin_user():
    email = request.form['email']
    password = request.form['password']
    user = auth.sign_in_with_email_and_password(email,password)
    auth.refresh(user['refreshToken'])

    userData = dict(db.child("users/" + user['localId']).get(auth.current_user['idToken']).val())  # TODO: Error check

    return render_template("User_info.html", name=userData['userName'], balance=userData['balance'])


def create_base_user_data(userName):
    user = auth.current_user

    data = {
        "userName": userName,
        "balance": 1000,
        "inGame": False
         }

    results = db.child("users/" + user['localId']).set(data, user['idToken'])  # TODO: Error check results
    return render_template("User_info.html", name=auth.current_user['displayName'], balance=1000)


def get_tables():
    table_data = dict(db.child("tables/").get().val())  # TODO: Error Check
    for table in table_data.values():
        available_seats = 0
        for seat in table['seats']:
            if seat == 'empty':
                available_seats = available_seats + 1
        table['seats'] = available_seats
    return table_data


@app.route('/join_table', methods=['GET', 'POST'])
def join_table():
    userId = auth.current_user['localId']
    print("join_table: userId: " + userId)
    return render_template("Game_Table.html")


if __name__ == '__main__':
    app.run()

