from flask import Flask, render_template, session, redirect, url_for
from flask_socketio import SocketIO, disconnect
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'fallback_development_key')
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

socketio = SocketIO(app, cors_allowed_origins=[])


@app.route('/')
def index():
    """Landing page with auth CTAs"""
    return render_template('index.html')


@app.route('/login')
def login():
    """Authentication gateway"""
    if 'user' in session:
        return redirect(url_for('vaults'))
    return render_template('login.html')


@app.route('/vaults')
def vaults():
    """Password vault interface"""
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('vaults.html')


@app.route('/logout')
def logout():
    """Secure session termination"""
    session.clear()
    return redirect(url_for('index'))


@socketio.on('connect')
def handle_connect():
    """Authenticate WebSocket connections"""
    if 'user' not in session:
        disconnect()
    else:
        print(f'Client {request.sid} connected')


@socketio.on('disconnect')
def handle_disconnect():
    """Clean up WebSocket resources"""
    print(f'Client {request.sid} disconnected')


if __name__ == '__main__':
    socketio.run(
        app,
        host=os.getenv('HOST', '0.0.0.0'),
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('DEBUG', 'false').lower() == 'true'
    )
