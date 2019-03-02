from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from zombieweb.auth import login_required
from zombieweb.db import get_db, init_db
import paho.mqtt.publish as publish

bp = Blueprint('status', __name__)

@bp.route('/')
def index():
    db = get_db()
    parts = db.execute(
        'SELECT id, name, status'
        ' FROM bodyparts'
        ' ORDER BY name'
    ).fetchall()
    lockstatus = db.execute(
        'SELECT id, name, status'
        ' FROM lockstatus'
    ).fetchone()
    
    return render_template('status/index.html', parts=parts, lockstatus=lockstatus)

@bp.route('/unlock', methods=('POST',))
def unlock():
    # send a msg to the zombie
    publish.single(topic="zombie", payload="unlock", hostname="localhost")
    return redirect(url_for('index'))

@bp.route('/reset', methods=('POST',))
def reset():
    # send a msg to the zombie
    publish.single(topic="zombie", payload="reset", hostname="localhost")
    return redirect(url_for('index'))

    
@bp.route('/insert', methods=('POST',))
def insert():
    name = request.form['name']
    status = request.form['status']
    
    db = get_db()
    db.execute(
        'REPLACE INTO bodyparts (name, status)'
        ' VALUES (?, ?)',
        (name, status)
    )
    db.commit()
    return 'OK'

@bp.route('/update', methods=('POST',))
def update():
    name = request.form['name']
    status = request.form['status']
        
    db = get_db()
    db.execute(
        'UPDATE bodyparts SET status = ?'
        ' WHERE name = ?',
        (status, name)
    )
    db.commit()
    return 'OK'

@bp.route('/initlock', methods=('POST',))
def initlock():
    name = request.form['lockname']
    status = request.form['status']
    
    db = get_db()
    db.execute(
        'REPLACE INTO lockstatus (name, status)'
        ' VALUES (?, ?)',
        (name, status)
    )
    db.commit()
    return 'OK'
    
@bp.route('/updatelock', methods=('POST',))
def updatelock():
    name = request.form['lockname']
    status = request.form['status']
    
    db = get_db()
    db.execute(
        'UPDATE lockstatus SET status = ?'
        ' WHERE name = ?',
        (status, name)
    )
    db.commit()
    return 'OK'
    
@bp.route('/init', methods=('GET', 'POST'))
def init():
    init_db()
    
    return 'OK'