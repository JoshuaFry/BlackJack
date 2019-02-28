from flask import Flask
from flask import Flask,request,render_template
import uuid
import pyrebase
#https://getbootstrap.com/docs/4.3/getting-started/introduction/

src = "https://www.gstatic.com/firebasejs/5.8.3/firebase.js"

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

app = Flask(__name__)

@app.route('/')
def home():

    return render_template("index.html",title="Homepage")


@app.route('/account')
def account_page():
    return render_template("Account_Page.html",title="Account")


@app.route('/about')
def about_page():
    return render_template("About_page.html",title="About")


@app.route('/register', methods = ['POST'])
def register_user():
    email = request.form['email']
    password = request.form['password']
    userName = request.form['Username']
    auth.create_user_with_email_and_password(email, password)
    user = auth.sign_in_with_email_and_password(email,password)
    auth.refresh(user['refreshToken'])

    create_base_user_data(userName)

    return render_template("index.html",title="Homepage")


@app.route('/updateBalance/', methods = ['POST'])
def update_balance():
    userId = auth.current_user['localId']
    amount = request.form['amount']
    db = firebase.database()
    results = db.child("users/" + userId).update({"balance:" + amount})

    return render_template("User_info.html", name = auth.current_user['displayName'], balance = 0)


@app.route('/signin', methods = ['POST'])
def signin_user():
    email = request.form['email']
    password = request.form['password']
    user = auth.sign_in_with_email_and_password(email,password)
    user = auth.refresh(user['refreshToken'])
    # print(auth.current_user)

    return render_template("index.html",title="Homepage")


def create_base_user_data(userName):
    userId = auth.current_user['localId']
    db = firebase.database()

    userId = {
        "userName": userName,
        "balance": 0,
        "inGame": False
         }

    results = db.child('users').push(userId,auth.current_user['idToken'])

    return render_template("User_info.html", name = auth.current_user['displayName'], balance = 0)


if __name__ == '__main__':
    # auth = firebase.auth()
    # db = firebase.database()
    # user = auth.sign_in_with_email_and_password("joshua.fry@western.edu", "pass2019")
    # user = auth.refresh(user['refreshToken'])

    # results = db.child("table").push(test_data(), user['idToken'])

    app.run()

