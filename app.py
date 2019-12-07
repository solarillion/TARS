# Authors: Nanda H Krishna (https://github.com/nandahkrishna), Abhijith Ragav (https://github.com/abhijithragav)

import os
from datetime import *
from dateutil.relativedelta import *
from dateutil.rrule import *
import json
import requests
import threading
from flask import Flask, jsonify, render_template, request
import slack
from slackeventsapi import SlackEventAdapter
import pyrebase

app = Flask(__name__)
app.debug = True

tars_admin = os.environ.get("TARS_ADMIN")
tars_token = os.environ.get("TARS_TOKEN")
tars_secret = os.environ.get("TARS_SECRET")
tars_bot_id = os.environ.get("TARS_BOT_ID")
general_id = os.environ.get("GENERAL_ID")
orientation_id = os.environ.get("ORIENTATION_ID")
vineethv_id = os.environ.get("VINEETHV_ID")
firebase_api_key = os.environ.get("FIREBASE_API_KEY")
tars_fb_ad = os.environ.get("TARS_FB_AD")
tars_fb_url = os.environ.get("TARS_FB_URL")
tars_fb_sb = os.environ.get("TARS_FB_SB")
hyouka_fb_key = os.environ.get("HYOUKA_FB_KEY")
hyouka_fb_ad = os.environ.get("HYOUKA_FB_AD")
hyouka_fb_url = os.environ.get("HYOUKA_FB_URL")
hyouka_fb_sb = os.environ.get("HYOUKA_FB_SB")
github_secret = os.environ.get("GITHUB_SECRET")

tars = slack.WebClient(token=tars_token)
slack_events_adapter = SlackEventAdapter(tars_secret, "/event", app)

vineethv_im_request = tars.im_open(user=vineethv_id)
vineethv_im_channel = vineethv_im_request.data["channel"]["id"]

config = {
  "apiKey": firebase_api_key,
  "authDomain": tars_fb_ad,
  "databaseURL": tars_fb_url,
  "storageBucket": tars_fb_sb
}
firebase = pyrebase.initialize_app(config)
db = firebase.database()

hyouka_config = {
  "apiKey": hyouka_fb_key,
  "authDomain": hyouka_fb_ad,
  "databaseURL": hyouka_fb_url,
  "storageBucket": hyouka_fb_sb
}
hyouka_firebase = pyrebase.initialize_app(hyouka_config)
hyouka_db = hyouka_firebase.database()

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@slack_events_adapter.on("message")
def message(event_data):
    thread = threading.Thread(target=im_event_handler, args=(event_data,))
    thread.start()
    return "OK", 200

def im_event_handler(event_data):
    text = event_data["event"]["text"].lower()
    if "request office hours" in text:
        tars.chat_postMessage(channel=vineethv_im_channel, text="Sir, please fill your office hours in this form: https://forms.gle/eMoayTXg5KJCata68")
    if "remind office hours" in text:
        tars.chat_postMessage(channel=vineethv_im_channel, text="Sir, if you haven't filled your office hours yet, please do so by 9 pm tonight. Here's the link to the form: https://forms.gle/eMoayTXg5KJCata68")
    if "post office hours" in text:
        data = db.child("officehours").get().val()
        message = "Sir's office hours for the week:\n"
        for item in data[1:]:
            item["start"] = reformat_time(item["start"])
            item["end"] = reformat_time(item["end"])
            message += item["days"] + ": " + item["start"] + " - " + item["end"] + "\n"    
        tars.chat_postMessage(channel=general_id, text=message)
    if "add orientee" in text:
        ta = list(db.child("ta").get().val())
        if event_data["event"]["user"] not in ta:
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="You're not allowed to do this!")
            return
        words = text.split()[2:]
        slack_id = words[0].replace("@", "").upper()
        slack_id = slack_id.replace("<", "")
        slack_id = slack_id.replace(">", "")
        name = tars.users_info(user=slack_id).data["user"]["profile"]["real_name"]
        join = str(date.today())
        github = words[1]
        group = words[2].upper()
        if "O" in group:
            group = "IoT"
        db.child("orientee").child(slack_id).update({ "name": name, "join": join, "github": github, "group": group, "progress": "py1", "py_fin": "None", "g_fin": "None", "p_fin": "None"})
        hyouka_db = hyouka_firebase.database()
        hyouka_db.child(github).update({"name": name, "group": group, "progress": "py1", "slack": slack_id})
        tars.chat_postMessage(channel=event_data["event"]["channel"], text="Added orientee!")
    if "remove orientee" in text:
        ta = list(db.child("ta").get().val())
        if event_data["event"]["user"] not in ta:
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="You're not allowed to do this!")
            return
        slack_id = text.split()[2].replace("@", "").upper()
        slack_id = slack_id.replace("<", "")
        slack_id = slack_id.replace(">", "")
        github = db.child("orientee").child(slack_id).get().val()["github"]
        db.child("orientee").child(slack_id).remove()
        hyouka_db.child(github).remove()
        tars.chat_postMessage(channel=event_data["event"]["channel"], text="Removed from database. Also remove them from any orientee channels, and add them to research channels if required.")
    if "show orientee" in text:
        ta = list(db.child("ta").get().val())
        if event_data["event"]["user"] not in ta:
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="You're not allowed to do this!")
            return
        slack_id = text.split()[2].replace("@", "").upper()
        slack_id = slack_id.replace("<", "")
        slack_id = slack_id.replace(">", "")
        data = db.child("orientee").child(slack_id).get().val()
        message = "Progress of " + data["name"] + ":\nJoined: " + data["join"] + "\nGroup: " + data["group"] + "\nStatus: " + data["progress"]
        if data["py_fin"] != "None":
            message += "\nPython end: " + data["py_fin"]
        if data["g_fin"] != "None":
            message += "\nGroup end: " + data["g_fin"]
        if data["p_fin"] != "None":
            message += "\nProject end: " + data["p_fin"] + "\nAfter the project review, don't forget to remove orientee."
        tars.chat_postMessage(channel=event_data["event"]["channel"], text=message)
    if "verify orientee" in text:
        ta = list(db.child("ta").get().val())
        if event_data["event"]["user"] not in ta:
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="You're not allowed to do this!")
            return
        slack_id = text.split()[2].replace("@", "").upper()
        slack_id = slack_id.replace("<", "")
        slack_id = slack_id.replace(">", "")
        data = db.child("orientee").child(slack_id).get().val()
        status = data["progress"]
        github = data["github"]
        message = "Current status: " + status
        tars.chat_postMessage(channel=event_data["event"]["channel"], text=message)
        new_status = {"py2": "py3", "py3": data["group"].lower() + "1", "ml1": "ml2", "ml2": "ml3", "ml3": "mlp", "iot1": "iot2", "iot2": "iot3", "iot3": "iotp", "mg1": "mg2", "mg2": "mg3", "mg3": "mgp"}
        if status == "py1":
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="Verification for py1 will be done through Hyouka.")
        elif status == "py2" or status == "py3":
            hyouka_status = hyouka_db.child(github).get().val()["progress"]
            if hyouka_status == new_status[status]:
                db.child("orientee").child(slack_id).update({"progress": new_status[status]})
                tars.chat_postMessage(channel=event_data["event"]["channel"], text="Verified " + status + "!")
                if status == "py3":
                    db.child("orientee").child(slack_id).update({"py_fin": str(date.today())})
                    tars.chat_postMessage(channel=event_data["event"]["channel"], text="Move on to the " + group + "assignments now.")
            else:
                tars.chat_postMessage(channel=event_data["event"]["channel"], text="Not yet evaluated on Hyouka!")
        elif "p" != status[-1]:
            db.child("orientee").child(slack_id).update({"progress": new_status[status]})
            hyouka_db.child(github).update({"progress": new_status[status]})
            if "p" in new_status[status]:
                db.child("orientee").child(slack_id).update({"g_fin":str( date.today())})
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="Verified" + status + "!")
        else:
            db.child("orientee").child(slack_id).update({"progress": "done"})
            db.child("orientee").child(slack_id).update({"p_fin": str(date.today())})
            hyouka_db.child(github).update({"progress": "done"})
            tars.chat_postMessage(channel=event_data["event"]["channel"], text="Verified! Project complete, book a review and remove orientee from database after this.")
    if "book meeting" in text:
        tars.chat_postMessage(channel=event_data["event"]["channel"], text="Almost ready.")

def reformat_time(ts):
    hour = int(ts.split(":")[0][-2:]) + 5
    min = int(ts.split(":")[1][:2]) + 22
    if min >= 60:
        min -= 60
        hour += 1
    time = ""
    if len(str(min)) == 1:
        min = "0" + str(min)
    if hour >= 12:
        if hour != 12:
            hour -= 12
        time = str(hour) + ":" + str(min) + " PM"
    else:
        time = str(hour) + ":" + str(min) + " AM"
    return time

@slack_events_adapter.on("team_join")
def team_join(event_data):
    thread = threading.Thread(target=team_join_event_handler, args=(event_data,))
    thread.start()
    return "OK", 200

def team_join_event_handler(event_data):
    user = event_data["event"]["user"]["id"]
    im_request = tars.im_open(user=user)
    chat = im_request.data["channel"]["id"]
    tars.chat_postMessage(channel=chat, blocks=[
        {
            "type": "section",
            "text": {
                "type": "plain_text",
                "text": "Hello there! I'm TARS, and I help people at Solarillion do almost every task on Slack. You can visit the Home tab at any time to see what you need to tell me to get things done. I hope you enjoy your journey here. See you soon. *flashes cue light*­"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Oh, and one more thing. Carefully read the README file in the PythonBasics repository on GitHub (https://github.com/solarillion/PythonBasics) before you get started with your assignments. The Webhook URL is https://sf-hyouka.herokuapp.com/python and the Secret is `" + github_secret + "` (you'll need these later). Please do not share this anywhere else or with anyone else. Contact a TA if you have any other doubts. Bye for now!"
            }
        }
    ])
    tars.chat_postMessage(chat=orientation_id, text="The Python assignments are available at https://github.com/solarillion/PythonBasics along with instructions. Create a GitHub account if you don't have one and follow the instructions given to do your assignments. Don't hesitate to contact a TA if you have any doubts!")

@slack_events_adapter.on("app_home_opened")
def app_home_opened(event_data):
    thread = threading.Thread(target=app_home_opened_event_handler, args=(event_data,))
    thread.start()
    return "OK", 200
    
def app_home_opened_event_handler(event_data):
    user = event_data["event"]["user"]
    ta = list(db.child("ta").get().val())
    if user in ta:
        tars.views_publish(user_id=user, view={
                "type": "home",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Hi 👋 I'm TARS. I help people at SF do just about everything. Here are a few things that I do:"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "plain_text",
                                "text": "🤖 Sending notifications and information."
                            },
                            {
                                "type": "plain_text",
                                "text": "🤖 Scheduling and posting Sir's office hours and TA hours."
                            },
                            {
                                "type": "plain_text",
                                "text": "🤖 Updating JupyterHub and server SSH links."
                            },
                            {
                                "type": "plain_text",
                                "text": "🤖 Booking meetings."
                            },
                            {
                                "type": "plain_text",
                                "text": "🤖 Helping TAs do their job."
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "And a whole lot more."
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Office Hours*\nSir is sent the office hours request automatically every Saturday evening. They are posted every Sunday evening. If the server is down, the server admins take over and request or post the office hours."
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*TA Orientee Tracking*\nAll TAs and Sir can add or remove orientees from the SF orientee database, track their progress and verify assignments. The functions are:"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": ":point_right: `add orientee @SLACK_ID GITHUB GROUP`\nExample: `add orientee @FakeOrientee fake_orientee ML`"
                            },
                            {
                                "type": "mrkdwn",
                                "text": ":point_right: `remove orientee @SLACK_ID`\nExample: `remove orientee @FakeOrientee`"
                            },
                            {
                                "type": "mrkdwn",
                                "text": ":point_right: `show orientee @SLACK_ID`\nExample: `show orientee @FakeOrientee`"
                            },
                            {
                                "type": "mrkdwn",
                                "text": ":point_right: `verify orientee @SLACK_ID`\nExample: `verify orientee @FakeOrientee`"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "plain_text",
                            "text": "Well, that's it for now, but I'll be doing a lot more in the future. Use my services well. Oh, and contact the server team if you have any feature requests or need help. *flashes cue light*"
                        }
                    }
                ]
        })
    else:
        tars.views_publish(user_id=user, view={
                "type": "home",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Hi 👋 I'm TARS. I help people at SF do just about everything. Here are a few things that I do:"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "plain_text",
                                "text": "🤖 Sending notifications and information."
                            },
                            {
                                "type": "plain_text",
                                "text": "🤖 Scheduling and posting Sir's office hours and TA hours."
                            },
                            {
                                "type": "plain_text",
                                "text": "🤖 Updating JupyterHub and server SSH links."
                            },
                            {
                                "type": "plain_text",
                                "text": "🤖 Booking meetings."
                            },
                            {
                                "type": "plain_text",
                                "text": "🤖 Helping TAs do their job."
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "And a whole lot more."
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Office Hours*\nSir is sent the office hours request automatically every Saturday evening. They are posted every Sunday evening. If the server is down, the server admins take over and request or post the office hours."
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "plain_text",
                            "text": "Well, that's it for now, but I'll be doing a lot more in the future. Use my services well. Oh, and contact the server team if you have any feature requests or need help. *flashes cue light*­"
                        }
                    }
                ]
        })

if __name__ == "__main__":
    app.run(threaded=True)
