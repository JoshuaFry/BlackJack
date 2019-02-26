from flask import Flask
from flask import Flask,request,render_template
import uuid
import pyrebase

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

app = Flask(__name__)

@app.route('/')
def hello_world():
    return render_template("index.html")


def test_data():
    table = uuid.uuid4()

    name = "testName"
    table = {
        "name" : name,
        "seats" : {
            1 : "empty",
            2 : "empty",
            3: "empty",
            4: "empty",
            5: "empty",
            6: "empty"
            }
         }
    return table


if __name__ == '__main__':
    auth = firebase.auth()
    db = firebase.database()
    user = auth.sign_in_with_email_and_password("joshua.fry@western.edu", "pass2019")
    user = auth.refresh(user['refreshToken'])

    # results = db.child("table").push(test_data(), user['idToken'])

    app.run()

