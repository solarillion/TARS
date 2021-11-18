import shlex


def handle_poll(app, db, key_fb_tars, event_data):
    try:
        text = event_data["text"]
        text = text.replace(u"\u201c", u"\u0022").replace(u"\u201d", u"\u0022")
        text = shlex.split(text)[2:]
        question = text[0]
        options = text[1:]
        emoji = ["one", "two", "three", "four", "five",
                 "six", "seven", "eight", "nine", "keycap_ten"]
        if len(options) > 10:
            raise Exception("Too many options!")
        question_block = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*" + question + "*"
            }
        }
        options_blocks = []
        for i in range(len(options)):
            options_blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": ":" + emoji[i] + ": " + options[i]
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": ":" + emoji[i] + ":"
                    },
                    "value": emoji[i] + "_poll"
                }
            })
        options_blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": ":white_check_mark: End Poll"
                    },
                    "value": "end_poll"
                }
            ]
        })
        options_blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": ":x: Delete Poll"
                    },
                    "value": "delete_poll"
                }
            ]
        })
        try:
            options_blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "Created by <@" + event_data["user"] + "> using TARS."
                    }
                ]
            })
        except:
            options_blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "Created using TARS."
                    }
                ]
            })
        poll = app.client.chat_postMessage(
            channel=event_data["channel"], text=question + " Poll", blocks=[question_block] + options_blocks)
        db.child(key_fb_tars).child("polls").child(poll.data["ts"].replace(".", "-")).update(
            {"user": event_data["user"], "question": question, "message": [question_block] + options_blocks})
        if question == "Mon-Thu TA Hours":
            db.child(key_fb_tars).child("tapoll").update(
                {"monthu": poll.data["ts"].replace(".", "-")})
        elif question == "Fri-Sun TA Hours":
            db.child(key_fb_tars).child("tapoll").update(
                {"frisun": poll.data["ts"].replace(".", "-")})
    except Exception as e:
        print(e)
        app.client.chat_postEphemeral(channel=event_data["channel"], user=event_data["user"],
                                      text="Syntax for polls is `@TARS poll \"Question\" \"Option 1\" \"Option 2\" ...` with a maximum of `10` options.")
