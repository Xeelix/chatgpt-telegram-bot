# This is a Python script that extracts messages from a telegram file result.json.
import datetime
import json


def load_json(filename):
    with open(filename, 'r', encoding="utf8") as f:
        return json.load(f)


def extract_messages(json_data: dict):
    """
    Output data as a dict example:
     "date": "2021-05-20T15:14:59",
     "from": "Steve",
     "from_id": "user12312"
     "text": "Hi"
    """
    messages = []
    for message in json_data["messages"]:
        # if text in null - skip
        if len(message["text"]) <= 0:
            continue

        # if message type not 'message' - skip
        if message["type"] != "message":
            continue

        # if from 'Telegpt' or 'Shmalala' - skip
        if message["from"] in ["Telegpt", "Shmalala"]:
            continue

        # convert from_id to only ids:
        message["from_id"] = message["from_id"].replace("user", "")

        # if message.text contains object with "type": "mention_name" - skip
        # text with type 'mention_name' example:
        # "text": [
        #     {
        #      "type": "mention_name",
        #      "text": "Steve",
        #      "user_id": 123412
        #     },
        #     ""
        #    ],

        text = message.get('text', '')

        if isinstance(text, list):
            if not any(isinstance(item, dict) and item.get('type') == 'mention_name' for item in text):
                text_contained = ''
                for item in text:
                    if isinstance(item, str):
                        text_contained += item
                    elif isinstance(item, dict):
                        if item.get('text') and item.get('type') == 'link':
                            text_contained += item.get('text')

                text = text_contained
            else:
                # Пропускаем сообщение с 'mention_name'
                continue

        messages.append({
            "date": message["date"],
            "from": message["from"],
            "from_id": message["from_id"],
            "text": text
        })
    return messages


def sessionize_messages(messages):
    """
    sessionizing the messages into “conversation” blocks, with a 4-hour drop-off threshold.

    :param messages:
    :return: sessionized messages
    """
    sessionized_messages = []
    session_messages = []
    session_number = 0
    message_number = 0
    # converting message from string to date format
    date_object = datetime.datetime.strptime(messages[0]["date"], "%Y-%m-%dT%H:%M:%S")
    # date without seconds
    date_object = date_object.replace(second=0, microsecond=0)

    last_message_date = date_object
    for message in messages:
        message_date = datetime.datetime.strptime(message["date"], "%Y-%m-%dT%H:%M:%S")
        message_date = message_date.replace(second=0, microsecond=0)

        if message_date - last_message_date > datetime.timedelta(hours=4):
            sessionized_messages.append(session_messages)
            session_messages = []
            session_number += 1
            message_number = 0

        message["session_number"] = session_number
        message["message_number"] = message_number
        session_messages.append(message)
        last_message_date = message_date

        message_number += 1

    sessionized_messages.append(session_messages)
    return sessionized_messages


def get_sessionized_message():
    json_data = load_json("result.json")
    extracted_messages = extract_messages(json_data)
    sessinonized_messages = sessionize_messages(extracted_messages)

    return sessinonized_messages

if __name__ == "__main__":
    get_sessionized_message()