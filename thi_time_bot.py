from telegram import Bot
from icalendar import Calendar
import asyncio
import requests
from datetime import datetime, timedelta, timezone, time
import sqlite3

# Define the UTC+2 timezone
UTC_PLUS_2 = timezone(timedelta(hours=2))

# check_broadcast
conn = sqlite3.connect('broadcast.db')
cursor = conn.cursor()
cursor.execute("SELECT broadcast, message FROM broadcast")
broadcast_ = cursor.fetchall()
conn.commit()
conn.close()


def delete_data(chat_id, db='message_id.db'):
    """
    Delete rows with a specific chat_id in the table
    :param db: The SQLite database file
    :param chat_id: The chat_id of the rows to be deleted
    :return:
    """
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    if chat_id != 1234:
        sql = f'DELETE FROM message WHERE chat_id={chat_id}'
    else:
        sql = f'DELETE FROM broadcast'
    cur.execute(sql)
    conn.commit()
    conn.close()


def get_all_message():
    conn = sqlite3.connect('message_id.db')
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id, message_id FROM message")
    users = cursor.fetchall()
    conn.close()
    return users


def get_all_users():
    conn = sqlite3.connect('thi_bot_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id, ical_link FROM users")
    users = cursor.fetchall()
    conn.close()
    return users


def print_database(db_name):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Get the list of table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    # Iterate over each table
    for table_name in tables:
        print(f"Table: {table_name[0]}")

        # Query the table
        cursor.execute(f"SELECT * FROM {table_name[0]}")
        rows = cursor.fetchall()

        # Print each row
        for row in rows:
            print(row)

        print("\n")

    # Close the connection
    conn.close()


async def del_last(chat_id):
    bot = Bot(token='5840248741:AAH1LvXXM2GyS9dQhGVo3IJp5VWV01LjjCA')
    messages = get_all_message()
    if messages:
        for message in messages:
            if message[0] == chat_id:
                # print(chat_id)
                await bot.delete_message(chat_id=message[0], message_id=message[1])
        delete_data(chat_id=chat_id)


async def call_send(chat_id, message):
    # 5840248741:AAH1LvXXM2GyS9dQhGVo3IJp5VWV01LjjCA
    bot = Bot(token='5840248741:AAH1LvXXM2GyS9dQhGVo3IJp5VWV01LjjCA')
    message = await bot.send_message(chat_id=chat_id, text=message)
    conn = sqlite3.connect('message_id.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO message (chat_id, message_id) VALUES (?, ?)",
                   (chat_id, message.message_id))
    conn.commit()
    conn.close()


# Make a GET request to the URL


# def get_today(event_names, events_dict):
#     # Get today's date
#     today = datetime.now().date()
#
#     # Initialize the earliest event and its start time
#     earliest_event = None
#     earliest_start = None
#
#     # Loop through each event name
#     for event_name in event_names:
#         # Check if the event exists in the dictionary
#         if event_name in events_dict:
#             # Get the list of events with this name
#             events = events_dict[event_name]
#
#             # Loop through each event and check if it starts today
#             for i, event in enumerate(events):
#                 if event['dtstart'].date() == today:
#                     # If this is the first event today or it starts earlier than the current earliest, update the
#                     # earliest event and start time
#                     if earliest_event is None or event['dtstart'] < earliest_start:
#                         earliest_event = event
#                         earliest_start = event['dtstart']
#
#     return earliest_event
#

def broadcast_call(chat_id):
    global broadcast_
    if broadcast_:
        asyncio.run(call_send(chat_id, 'ADMIN BROADCAST:'))
        asyncio.run(call_send(chat_id, broadcast_[0][1]))
        delete_data(1234, 'broadcast.db')


def get_today_all(event_names, events_dict):
    # Get today's date
    today = datetime.now().date()
    time_now = datetime.now()
    if time_now.astimezone(UTC_PLUS_2).time() > time(13, 00):
        today = today + timedelta(days=1)
    # Initialize a list to store all events that start today
    today_events = []

    # Loop through each event name
    for event_name in event_names:
        # Check if the event exists in the dictionary
        if event_name in events_dict:
            # Get the list of events with this name
            events = events_dict[event_name]

            # Loop through each event and check if it starts today
            for event in events:
                if event['dtstart'].date() == today:
                    # Add the event to the list of today's events
                    today_events.append(event)

    return today_events

def get_nextweek(event_names, events_dict):
    # Get today's date
    today = datetime.now().date()
    time_now = datetime.now()
    if time_now.time() > time(13, 00):
        today = today + timedelta(days=3)


    # Initialize a list to store all events that start today
    today_events = []

    # Loop through each event name
    for event_name in event_names:
        # Check if the event exists in the dictionary
        if event_name in events_dict:
            # Get the list of events with this name
            events = events_dict[event_name]

            # Loop through each event and check if it starts today
            for event in events:
                if event['dtstart'].date() == today:
                    # Add the event to the list of today's events
                    today_events.append(event)

    return today_events


def schedule_send(chat_id, ical_link):
    asyncio.run(del_last(chat_id))
    broadcast_call(chat_id)

    # get the response
    response = requests.get(ical_link)

    # Use the content attribute of the response to get the data
    data = response.content

    # Create a Calendar object with the data
    cal = Calendar.from_ical(data)
    # Now you can access the events in the calendar
    # for event in cal.walk('vevent'):
    #     print(event.get('description').split('\n')[0])
    #     # print(event.get('dtstart').dt)
    #     # print(event.get('dtend').dt)
    #     # print(event.get('location'))
    events_dict = {}
    for event in cal.walk('vevent'):
        # Get the event name
        event_name = str(event.get('description').split('\n')[0])

        # If the event name is not in the dictionary, add it
        if event_name not in events_dict:
            events_dict[event_name] = []

        # Create a dictionary for this specific event
        event_dict = {
            'summary': event_name,
            'dtstart': event.get('dtstart').dt,
            'dtend': event.get('dtend').dt,
            'location': str(event.get('location'))
        }

        # Add this event to the list of events for this name
        events_dict[event_name].append(event_dict)

    # event = get_today(events_dict.keys(), events_dict)
    event_all = get_today_all(events_dict.keys(), events_dict)
    if event_all:
        time_now = datetime.now()
        if time_now.astimezone(UTC_PLUS_2).time() > time(13, 00):
            asyncio.run(call_send(chat_id, "Tomorrow's Schedule"))
        for event in event_all:
            location_list = event['location'].split(',')[:-1]
            location = ','.join(location_list)

            message = f"{event['summary']} @ {event['dtstart'].astimezone(UTC_PLUS_2).strftime('%H:%M')} -> {event['dtend'].astimezone(UTC_PLUS_2).strftime('%H:%M')} {location}"
            asyncio.run(call_send(chat_id, message))
            # print(f"End Date: {event['dtend']}")
            # if event['dtstart'].astimezone(UTC_PLUS_2).time() < time(8, 30):
            #     asyncio.run(call_send(chat_id, 'WAKE UP'))


try:
    for user in get_all_users():
        #delete_data(user[0])
        schedule_send(user[0], user[1])
except Exception as e:
    asyncio.run(call_send('545628653', f"Error: {e}"))
#print_database('thi_bot_database.db')
# 30 15 * * 0-4 python3.8 thi_time_bot.py && curl -X GET https://hc-ping.com/5b56337b-b381-4968-8f7b-10e96447aec0

