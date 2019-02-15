from flask import Flask
from flask import Flask,request,render_template

app = Flask(__name__)


@app.route('/')
def home():
    return render_template("index.html",title="Homepage")


if __name__ == '__main__':
    app.run()
