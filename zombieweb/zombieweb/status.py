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
    boxstatus = db.execute(
        'SELECT id, name, status'
        ' FROM lockstatus'
        ' WHERE name = "Box"'
    ).fetchone()
    casketstatus = db.execute(
        'SELECT id, name, status'
        ' FROM lockstatus'
        ' WHERE name = "Casket"'
    ).fetchone()
    candles = db.execute(
        'SELECT id, name, color, status'
        ' FROM candles'
        ' ORDER BY name'
    ).fetchall()
        
    
    return render_template('status/index.html', parts=parts, boxstatus=boxstatus,
                           casketstatus=casketstatus, candles=candles)

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

@bp.route('/insertcandle', methods=('POST',))
def insertcandle():
    name = request.form['name']
    status = request.form['status']
    color = request.form['color']
    
    db = get_db()
    db.execute(
        'REPLACE INTO candles (name, color, status)'
        ' VALUES (?, ?, ?)',
        (name, color, status)
    )
    db.commit()
    return 'OK'

@bp.route('/updatecandle', methods=('POST',))
def updatecandle():
    name = request.form['name']
    status = request.form['status']
    color = request.form['color']
        
    db = get_db()
    db.execute(
        'UPDATE candles SET color = ?, status = ?'
        ' WHERE name = ?',
        (color, status, name)
    )
    db.commit()
    return 'OK'

@bp.route('/closecasket', methods=('POST',))
def closecasket():
    # send a msg to the casket
    publish.single(topic="/casket/command", payload="close", hostname="localhost")
    return redirect(url_for('index'))

@bp.route('/opencasket', methods=('POST',))
def opencasket():
    # send a msg to the casket
    publish.single(topic="/casket/command", payload="open", hostname="localhost")
    return redirect(url_for('index'))

@bp.route('/closecasketdelay', methods=('POST',))
def opencasketdelay():
    # send a msg to the casket
    publish.single(topic="/casket/command", payload="closedelay", hostname="localhost")
    return redirect(url_for('index'))


@bp.route('/init', methods=('GET', 'POST'))
def init():
    init_db()
    
    return 'OK'