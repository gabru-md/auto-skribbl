from flask import Flask, render_template, url_for, redirect, request
from skribbl import SkribblBot
from functools import wraps
import urllib
import pymongo
import logging
import uuid
import os
from db import db

logger_format = '%(asctime)-15s: %(message)s'
logging.basicConfig(format=logger_format)
logger = logging.getLogger('Server Logger')

app = Flask(__name__)

def new_room_id():
    return str(uuid.uuid4())

def increment_usage():
    usage = db.usage
    if usage.find_one({'author': 'admin'}) == None:
        usage.insert_one({
            'author': 'admin',
            'usage': 1
        })
        return
    usage.update({'author':'admin'}, {
        '$inc': {
            'usage': 1
        }
    }, upsert=False)

    logger.warning('Updated usage by 1')

def room_exists(func):
    @wraps(func)
    def check_room_exists(*args, **kwargs):
        if 'room_id' not in kwargs:
            return redirect(url_for('homepage'))
        room_id = kwargs['room_id']
        rooms = db.rooms
        if rooms.find_one({'room_id': room_id}) == None:
            return redirect(url_for('homepage'))
        return func(*args, **kwargs)
    return check_room_exists


@app.route('/', methods=['GET'])
def homepage():
    logger.warning('lol')
    increment_usage()
    return render_template('index.html')

@app.route('/r', methods=['GET'])
def create_room():
    return render_template('create_room.html')

@app.route('/r/create', methods=['POST'])
def init_room():
    data = request.form
    if 'players' in data and 'rounds' in data and 'draw_time' in data:
        try:
            players = int(data.get('players'))
            rounds = int(data.get('players'))
            draw_time = int(data.get('draw_time'))
            if players < 1:
                players = 2
            if rounds < 2 or rounds > 10:
                rounds = 5
            if draw_time < 30 or draw_time > 180:
                draw_time = 80
            
            draw_time = draw_time//10*10

            return redirect(url_for('create_room_with_players', players=players, rounds=rounds, draw_time=draw_time))
        except Exception:
            return redirect(url_for('homepage'))

@app.route('/r/p/<players>/<rounds>/<draw_time>', methods=['GET'])
def create_room_with_players(players, rounds, draw_time):
    room_id = new_room_id()
    rooms = db.rooms
    rooms.insert_one({
        'room_id': room_id,
        'players': int(players),
        'rounds': int(rounds),
        'draw_time': int(draw_time),
        'game_link': '',
        'words': []
    })
    return redirect(url_for('room_page', room_id=room_id))

@app.route('/r/words/<room_id>', methods=['POST'])
@room_exists
def add_words_to_room(room_id):
    data = request.form
    if 'words' not in data:
        return redirect(url_for('homepage'))
    words = data.get('words')
    try:
        words_list = [word.strip() for word in words.split(',')]
        rooms = db.rooms
        rooms.update({'room_id': room_id}, {
            '$push': {
                'words': {
                    '$each': words_list
                }
            }
        }, upsert=True)
    except Exception:
        return redirect(url_for('homepage'))

    return redirect(url_for('room_page', room_id=room_id))

@app.route('/r/<room_id>', methods=['GET'])
@room_exists
def room_page(room_id):
    return render_template('room.html', room_id=room_id)

@app.route('/r/a/<room_id>', methods=['GET'])
@room_exists
def room_with_id(room_id):
    return render_template('add_words.html', room_id=room_id)

@app.route('/r/start/<room_id>', methods=['GET'])
@room_exists
def start_game_for_room(room_id):
    room_details = db.rooms.find_one({'room_id': room_id})
    players = room_details['players']
    rounds = room_details['rounds']
    draw_time = room_details['draw_time']
    words = room_details['words']

    skribbl_bot = SkribblBot(rounds, draw_time, players, words, room_id)
    skribbl_bot.start_game()
    # game_link = skribbl_bot.get_game_link()

    return render_template('join_room.html', room_id=room_id)


@app.route('/s/<room_id>', methods=['GET'])
@room_exists
def show_game_link(room_id):
    rooms = db.rooms
    my_room = rooms.find_one({'room_id': room_id})
    my_game_link = my_room['game_link']
    if my_game_link == "":
        return render_template('game_link.html', ready=False)
    return render_template('game_link.html', game_link=my_game_link, ready=True)

if __name__ == '__main__':
    app.run(debug=True)