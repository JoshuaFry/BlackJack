from flask import Flask
from flask import Flask,request,render_template
import uuid, functools
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
    return render_template("index.html",title="Homepage")


@app.route('/account')
def account_page():
    return render_template("Account_Page.html",title="Account")


@app.route('/about')
@login_required
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

    return create_base_user_data(userName)


@app.route('/updateBalance/', methods = ['GET', 'POST'])
@login_required
def update_balance():
    userId = auth.current_user['localId']
    db = firebase.database()
    balance = db.child("users/" + userId + "/balance").get().val()  # TODO: Error check results
    amount = int(request.form['amount']) + balance
    print(balance)
    results = db.child("users/" + userId).update({"balance": amount})  # TODO: Error check results

    return render_template("User_info.html", name=auth.current_user['displayName'], balance=amount)


@app.route('/signin', methods = ['POST'])
def signin_user():
    email = request.form['email']
    password = request.form['password']
    user = auth.sign_in_with_email_and_password(email,password)
    #print(user)
    auth.refresh(user['refreshToken'])
    db = firebase.database()

    #print(auth.current_user['localId'])
    userData = dict(db.child("users/" + user['localId']).get(auth.current_user['idToken']).val()) # TODO: Error check results
    #print(userData)
    # print(auth.current_user)
    # print(auth.current_user)

    return render_template("User_info.html",name=userData['userName'], balance=userData['balance'])


def create_base_user_data(userName):
    user = auth.current_user
    userId = user['localId']
    db = firebase.database()

    data = {
        "userName": userName,
        "balance": 1000,
        "inGame": False
         }

    #print(userId)
    results = db.child("users/" + userId).set(data,user['idToken']) # TODO: Error check results
    return render_template("User_info.html", name = auth.current_user['displayName'], balance= 1000)


if __name__ == '__main__':
    # auth = firebase.auth()
    # db = firebase.database()
    # user = auth.sign_in_with_email_and_password("joshua.fry@western.edu", "pass2019")
    # user = auth.refresh(user['refreshToken'])

    # results = db.child("table").push(test_data(), user['idToken'])

    app.run()

