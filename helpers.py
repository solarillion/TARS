from datetime import *
from poll import handle_poll

def reformat_time(ts):
    t = datetime.strptime(ts[11:19], "%H:%M:%S").time()
    t = datetime.combine(date.today(), t) + timedelta(hours=5, minutes=21, seconds=10)
    return t.strftime("%I:%M %p")

def app_mention_event_handler(app, db, key_fb_tars, event_data):
    text = event_data["text"]
    if "ping" in text.lower():
        app.client.chat_postMessage(channel=event_data["user"], text="hello")
    elif "poll" in text.lower():
        handle_poll(app, db, key_fb_tars, event_data)

def interact_handler(app, db, key_fb_tars, payload):
    user = payload["user"]["id"]
    channel = payload["container"]["channel_id"]
    ts = payload["message"]["ts"]
    value = payload["actions"][0]["value"]
    question = db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("question").get().val()
    if value == "delete_poll":
        if db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("user").get().val() == user:
            app.client.chat_update(channel=channel, ts=ts, text="Poll " + question + " deleted!", blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",       
                        "text": "Poll " + question + " deleted!"
                    }
                }
            ])
            db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).remove()
        else:
            app.client.chat_postEphemeral(channel=channel, user=user, text="You can only delete polls that you create.")
    elif value == "end_poll":
        if db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("user").get().val() == user:
            app.client.chat_update(channel=channel, ts=ts, text="Poll " + question + " closed!", blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Poll " + question + " closed!"
                    }
                }
            ])
            poll = db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).get().val()
            db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).remove()
            app.client.chat_postMessage(channel=channel, text="*Poll Results*")
            for block in poll["message"][1:-3]:
                text = block["text"]["text"]
                app.client.chat_postMessage(channel=channel, text=text)
        else:
            app.client.chat_postEphemeral(channel=channel, user=user, text="You can only close polls that you create.")
    elif "_poll" in value:
        emoji = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "keycap_ten"]
        value = value.split("_")[0]
        index = emoji.index(value) + 1
        poll = db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).get().val()
        votes = db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("votes").child(str(index)).get().val()
        if votes is None:
            db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("votes").child(str(index)).update({0: user})
            current = db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("message").child(str(index)).child("text").child("text").get().val()
            db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("message").child(str(index)).child("text").update({"text": current.strip() + " `1` ~ <@" + user + ">"})
        else:
            current = db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("message").child(str(index)).child("text").child("text").get().val()
            if user not in current:
                i = len(votes)
                db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("votes").child(str(index)).update({i: user})
                db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("message").child(str(index)).child("text").update({"text": current.split("`")[0] + "`" + str(i + 1) + "` ~ <@" + user + ">" + current.split("~")[1]})
            else:
                for i in votes:
                    if i == user:
                        votes.remove(i)
                db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("votes").child(str(index)).remove()
                j = 0
                for i in votes:
                    db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("votes").child(str(index)).update({j: i})
                    j += 1
                current = db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("message").child(str(index)).child("text").child("text").get().val()
                if j == 0:
                    db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("message").child(str(index)).child("text").update({"text": current.split("`")[0]})
                else:
                    db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).child("message").child(str(index)).child("text").update({"text": current.split("`")[0] + "`" + str(j) + "` ~ " + current.split("~")[1].replace("<@" + user + ">", "").strip()})
        blocks = dict(db.child(key_fb_tars).child("polls").child(ts.replace(".", "-")).get().val())["message"]
        app.client.chat_update(channel=channel, ts=ts, blocks=blocks)
