from flask import Flask
from flask import Flask,request,render_template

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


if __name__ == '__main__':
    app.run()
