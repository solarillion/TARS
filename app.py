from concurrent.futures import thread
import bcrypt
import flask_login
import logging
import os
import pyrebase
import threading

from dotenv import load_dotenv
from helpers import *
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, jsonify, redirect, request, render_template, redirect, url_for

load_dotenv()


tars_token = os.environ.get("TARS_TOKEN")  # bot user OAuth
tars_user_token = os.environ.get("TARS_USER_TOKEN")  # user OAuth
tars_admin = os.environ.get("TARS_ADMIN")  # channel for testing
tars_secret = os.environ.get("TARS_SECRET")  # signing secret

firebase_api_key = os.environ.get("FIREBASE_API_KEY")  # firebase API key
tars_fb_ad = os.environ.get("TARS_FB_AD")  # firebase auth domain
tars_fb_url = os.environ.get("TARS_FB_URL")  # firebase db url
tars_fb_sb = os.environ.get("TARS_FB_SB")  # storage bucket
key_fb_tars = os.environ.get("KEY_FB_TARS")  # SHA used to access child

vineethv_id = os.environ.get("VINEETHV_ID")  # Sir's user id
general = os.environ.get("GENERAL_ID")  # general channel id

username = os.environ.get("USERNAME")  # webpage login
password = os.environ.get("PASSWORD").encode()  # webpage password
secret = os.environ.get("SECRET")  # dont change

office_hours_form_url = os.environ.get(
    "OFFICE_HOURS_FORM"
)  # google form for office hours

config = {
    "apiKey": firebase_api_key,
    "authDomain": tars_fb_ad,
    "databaseURL": tars_fb_url,
    "storageBucket": tars_fb_sb,
}
firebase = pyrebase.initialize_app(config)
db = firebase.database()

app = App(
    token=tars_token,
    signing_secret=tars_secret,
)

flask_app = Flask(__name__)
flask_app.secret_key = secret
handler = SlackRequestHandler(app)

login_manager = flask_login.LoginManager()
login_manager.init_app(flask_app)
login_manager.login_view = "login"


class User(flask_login.UserMixin):
    pass


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


@login_manager.user_loader
def load_user(id):
    if id != username:
        return
    user = User()
    user.id = id
    return user


@flask_app.route("/", methods=["GET"])
def index():
    return redirect("https://solarillionfoundation.org/")


@flask_app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        data1 = {}
        data1["status"] = "Enter credentials."
        return render_template("login.html", data=data1)
    if request.method == "POST":
        username_form = request.form.get("username")
        password_form = request.form.get("password").encode()
        print("Password: %s\tPass Form: %s" % (password, password_form))
        if username_form == username and bcrypt.checkpw(password_form, password):
            user = User()
            user.id = username
            flask_login.login_user(user)
            data1 = {}
            data1["status"] = "Enter the details and submit."
            print("Validated user")
            return redirect(request.args.get("next") or url_for("index"))
        else:
            data1 = {}
            data1["status"] = "Incorrect credentials."
            print("Invalid user")
            return render_template("login.html", data=data1)


@flask_app.route("/logout")
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return redirect(url_for("login"))


@app.event("app_mention")
def message_hello(event, say):
    if "ping" in event["text"]:
        say("pong")


@app.message("request office hours")
def request_office_hours(message, say):
    admin = list(db.child(key_fb_tars).child("admin").get().val())
    if message["user"] not in admin:
        say("You're not allowed to do this!")
        return
    msg = "Sir, please fill your office hours in this form: " + office_hours_form_url
    app.client.chat_postMessage(channel=vineethv_id, text=msg)
    logging.info("Sent request to sir")


@app.message("remind office hours")
def remind_office_hours(message, say):
    admin = list(db.child(key_fb_tars).child("admin").get().val())

    if message["user"] not in admin:
        say("You're not allowed to do this!")
        return

    msg = (
        "Sir, if you haven't filled your office hours yet, please do so by 9 pm tonight. Here's the link to the form: "
        + office_hours_form_url
    )

    app.client.chat_postMessage(channel=vineethv_id, text=msg)
    logging.info("Sent reminder to sir")


@app.message("post office hours")
def post_office_hours(message, say):
    admin = list(db.child(key_fb_tars).child("admin").get().val())
    if message["user"] not in admin:
        say("You're not allowed to do this!")
        return
    data = db.child(key_fb_tars).child("officehours").get().val()
    message = "Sir's office hours for the week:\n"
    for item in data[1:]:
        item["start"] = reformat_time(item["start"])
        item["end"] = reformat_time(item["end"])
        message += item["days"] + ": " + item["start"] + " - " + item["end"] + "\n"
    app.client.chat_postMessage(channel=general, text=message)


@app.event("message")
def handle_message_events(body):
    logging.info(body)


if __name__ == "__main__":
    flask_app.run(port=5000)
