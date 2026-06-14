from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pymysql
import os
pymysql.install_as_MySQLdb()

app = Flask(__name__)
CORS(app)

# ✅ Reads from Railway environment variable
db_url = os.environ.get('DATABASE_URL', '')
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'event_bridge_secret'

db = SQLAlchemy(app)


# ─────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────

class User(db.Model):
    __tablename__ = 'users'
    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name       = db.Column(db.String(255), nullable=False)
    email      = db.Column(db.String(255), unique=True, nullable=False)
    phone      = db.Column(db.String(50),  nullable=True)
    password   = db.Column(db.String(255), nullable=False)
    role       = db.Column(db.String(20),  nullable=False)
    dept       = db.Column(db.String(150), nullable=True)
    reg_no     = db.Column(db.String(50),  nullable=True)
    is_blocked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ActiveSession(db.Model):
    __tablename__ = 'active_sessions'
    id       = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email    = db.Column(db.String(255), nullable=False)
    login_at = db.Column(db.DateTime, default=datetime.utcnow)

class Event(db.Model):
    __tablename__ = 'events'
    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name         = db.Column(db.String(255), nullable=False)
    description  = db.Column(db.Text, nullable=True)
    venue        = db.Column(db.String(255), nullable=False)
    category     = db.Column(db.String(100), nullable=False)
    event_date   = db.Column(db.DateTime, nullable=False)
    team_size    = db.Column(db.Integer, default=1)
    entry_fee    = db.Column(db.Numeric(10, 2), default=0.00)
    total_seats  = db.Column(db.Integer, nullable=False)
    status       = db.Column(db.String(20), default='Upcoming')
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

class Registration(db.Model):
    __tablename__ = 'registrations'
    id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_id       = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    team_name      = db.Column(db.String(150), nullable=True)
    status         = db.Column(db.String(20), default='Pending')
    payment_status = db.Column(db.String(20), default='Pending')
    attended       = db.Column(db.Boolean, default=False)
    registered_at  = db.Column(db.DateTime, default=datetime.utcnow)

class ODRequest(db.Model):
    __tablename__ = 'od_requests'
    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_id     = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    faculty_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reason       = db.Column(db.String(500), nullable=True)
    status       = db.Column(db.String(20), default='Pending')
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    decided_at   = db.Column(db.DateTime, nullable=True)

class Announcement(db.Model):
    __tablename__ = 'announcements'
    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_id     = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=True)
    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title        = db.Column(db.String(255), nullable=False)
    body         = db.Column(db.String(1000), nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    __tablename__ = 'messages'
    id               = db.Column(db.Integer, primary_key=True, autoincrement=True)
    conversation_key = db.Column(db.String(40), nullable=False)
    sender_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    text             = db.Column(db.String(2000), nullable=False)
    is_read          = db.Column(db.Boolean, default=False)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    __tablename__ = 'notifications'
    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title      = db.Column(db.String(255), nullable=False)
    body       = db.Column(db.String(1000), nullable=False)
    icon       = db.Column(db.String(50), nullable=True)
    color      = db.Column(db.String(20), nullable=True)
    is_read    = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Feedback(db.Model):
    __tablename__ = 'feedback'
    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_id   = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating     = db.Column(db.Integer, nullable=False)
    comment    = db.Column(db.String(1000), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def conv_key(a, b):
    lo, hi = sorted([int(a), int(b)])
    return f'{lo}_{hi}'

def user_brief(u):
    return {
        'id': u.id, 'name': u.name, 'email': u.email, 'phone': u.phone,
        'role': u.role, 'dept': u.dept, 'reg_no': u.reg_no,
        'is_blocked': bool(u.is_blocked)
    }

def event_dict(e):
    registered = Registration.query.filter_by(event_id=e.id).filter(
        Registration.status != 'Rejected').count()
    organizer = User.query.get(e.organizer_id)
    return {
        'id': e.id, 'organizer_id': e.organizer_id,
        'organizer': organizer.name if organizer else '',
        'name': e.name, 'description': e.description,
        'venue': e.venue, 'category': e.category,
        'event_date': e.event_date.strftime('%Y-%m-%d %H:%M'),
        'date_label': e.event_date.strftime('%d %b %Y'),
        'time_label': e.event_date.strftime('%I:%M %p'),
        'team_size': e.team_size, 'entry_fee': float(e.entry_fee),
        'total_seats': e.total_seats, 'registered': registered,
        'available_seats': max(e.total_seats - registered, 0),
        'status': e.status,
    }


# ─────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────

@app.route('/signup', methods=['POST'])
def signup():
    try:
        data     = request.get_json()
        required = ['name', 'email', 'password', 'confirm_password', 'role']
        if not data or not all(k in data for k in required):
            return jsonify({'error': 'Missing required fields'}), 400
        if data['password'] != data['confirm_password']:
            return jsonify({'error': 'Passwords do not match'}), 400
        if data['role'] not in ('organizer', 'participant', 'faculty', 'admin'):
            return jsonify({'error': 'Invalid role'}), 400
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 409
        reg_no = data.get('reg_no')
        if data['role'] == 'participant' and not reg_no:
            return jsonify({'error': 'Registration number required for participants'}), 400
        new_user = User(
            name=data['name'], email=data['email'], phone=data.get('phone'),
            password=generate_password_hash(data['password']),
            role=data['role'], dept=data.get('dept'),
            reg_no=reg_no if data['role'] == 'participant' else None
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password required'}), 400
        user = User.query.filter_by(email=data['email']).first()
        if not user or not check_password_hash(user.password, data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        if user.is_blocked:
            return jsonify({'error': 'Your account has been blocked. Contact admin.'}), 403
        if data.get('role') and data['role'] != user.role:
            return jsonify({'error': f'This account is registered as {user.role}.'}), 403
        db.session.add(ActiveSession(email=user.email))
        db.session.commit()
        return jsonify({'message': 'Login successful', 'user': user_brief(user)}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/get_current_user', methods=['GET'])
def get_current_user():
    try:
        last = ActiveSession.query.order_by(ActiveSession.id.desc()).first()
        if not last:
            return jsonify({'error': 'No active user found'}), 404
        user = User.query.filter_by(email=last.email).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(user_brief(user)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/logout', methods=['POST'])
def logout():
    try:
        data  = request.get_json()
        email = data.get('email') if data else None
        if not email:
            return jsonify({'error': 'Email required'}), 400
        ActiveSession.query.filter_by(email=email).delete()
        db.session.commit()
        return jsonify({'message': 'Logged out successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/change_password/<int:user_id>', methods=['PUT'])
def change_password(user_id):
    try:
        data = request.get_json()
        if not data or 'old_password' not in data or 'new_password' not in data:
            return jsonify({'error': 'old_password and new_password required'}), 400
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        if not check_password_hash(user.password, data['old_password']):
            return jsonify({'error': 'Current password is incorrect'}), 401
        user.password = generate_password_hash(data['new_password'])
        db.session.commit()
        return jsonify({'message': 'Password changed successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────
# PROFILE
# ─────────────────────────────────────────

@app.route('/profile/<int:user_id>', methods=['GET'])
def get_profile(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        out = user_brief(user)
        out['created_at'] = user.created_at.strftime('%d %b %Y')
        return jsonify(out), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/profile/<int:user_id>', methods=['PUT'])
def update_profile(user_id):
    try:
        data = request.get_json()
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        user.name  = data.get('name',  user.name)
        user.phone = data.get('phone', user.phone)
        user.dept  = data.get('dept',  user.dept)
        if user.role == 'participant':
            user.reg_no = data.get('reg_no', user.reg_no)
        db.session.commit()
        return jsonify({'message': 'Profile updated'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────
# EVENTS
# ─────────────────────────────────────────

@app.route('/events', methods=['GET'])
def get_events():
    try:
        category     = request.args.get('category')
        status       = request.args.get('status')
        search       = request.args.get('search')
        organizer_id = request.args.get('organizer_id')
        query = Event.query
        if category and category.lower() != 'all':
            query = query.filter_by(category=category)
        if status:
            query = query.filter_by(status=status)
        if organizer_id:
            query = query.filter_by(organizer_id=int(organizer_id))
        if search:
            query = query.filter(Event.name.like(f'%{search}%'))
        events = query.order_by(Event.event_date.asc()).all()
        return jsonify([event_dict(e) for e in events]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    try:
        e = Event.query.get(event_id)
        if not e:
            return jsonify({'error': 'Event not found'}), 404
        return jsonify(event_dict(e)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/events', methods=['POST'])
def add_event():
    try:
        data     = request.get_json()
        required = ['organizer_id', 'name', 'venue', 'category', 'event_date', 'total_seats']
        if not data or not all(k in data for k in required):
            return jsonify({'error': 'Missing required fields'}), 400
        try:
            event_date = datetime.strptime(data['event_date'], '%Y-%m-%d %H:%M')
        except ValueError:
            event_date = datetime.strptime(data['event_date'], '%Y-%m-%d')
        e = Event(
            organizer_id=data['organizer_id'], name=data['name'],
            description=data.get('description', ''), venue=data['venue'],
            category=data['category'], event_date=event_date,
            team_size=data.get('team_size', 1), entry_fee=data.get('entry_fee', 0),
            total_seats=data['total_seats'], status=data.get('status', 'Upcoming')
        )
        db.session.add(e)
        db.session.commit()
        return jsonify({'message': 'Event created', 'id': e.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/events/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    try:
        data = request.get_json()
        e    = Event.query.get(event_id)
        if not e:
            return jsonify({'error': 'Event not found'}), 404
        e.name        = data.get('name',        e.name)
        e.description = data.get('description', e.description)
        e.venue       = data.get('venue',       e.venue)
        e.category    = data.get('category',    e.category)
        e.team_size   = data.get('team_size',   e.team_size)
        e.entry_fee   = data.get('entry_fee',   e.entry_fee)
        e.total_seats = data.get('total_seats', e.total_seats)
        e.status      = data.get('status',      e.status)
        if data.get('event_date'):
            try:
                e.event_date = datetime.strptime(data['event_date'], '%Y-%m-%d %H:%M')
            except ValueError:
                e.event_date = datetime.strptime(data['event_date'], '%Y-%m-%d')
        db.session.commit()
        return jsonify({'message': 'Event updated'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    try:
        e = Event.query.get(event_id)
        if not e:
            return jsonify({'error': 'Event not found'}), 404
        Registration.query.filter_by(event_id=event_id).delete()
        ODRequest.query.filter_by(event_id=event_id).delete()
        Announcement.query.filter_by(event_id=event_id).delete()
        Feedback.query.filter_by(event_id=event_id).delete()
        db.session.delete(e)
        db.session.commit()
        return jsonify({'message': 'Event deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────
# REGISTRATIONS
# ─────────────────────────────────────────

@app.route('/registrations', methods=['POST'])
def add_registration():
    try:
        data     = request.get_json()
        required = ['user_id', 'event_id']
        if not data or not all(k in data for k in required):
            return jsonify({'error': 'Missing required fields'}), 400
        event = Event.query.get(data['event_id'])
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        existing = Registration.query.filter_by(
            user_id=data['user_id'], event_id=data['event_id']).first()
        if existing:
            return jsonify({'error': 'Already registered for this event'}), 409
        pay = 'NotRequired' if float(event.entry_fee) == 0 else 'Pending'
        reg = Registration(
            event_id=data['event_id'], user_id=data['user_id'],
            team_name=data.get('team_name'), status='Pending', payment_status=pay
        )
        db.session.add(reg)
        db.session.commit()
        return jsonify({'message': 'Registered successfully', 'id': reg.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/registrations/event/<int:event_id>', methods=['GET'])
def get_event_participants(event_id):
    try:
        status = request.args.get('status')
        query  = Registration.query.filter_by(event_id=event_id)
        if status:
            query = query.filter_by(status=status)
        regs   = query.order_by(Registration.registered_at.asc()).all()
        result = []
        for r in regs:
            u = User.query.get(r.user_id)
            result.append({
                'id': r.id, 'user_id': r.user_id,
                'name': u.name if u else '', 'email': u.email if u else '',
                'dept': u.dept if u else '', 'reg_no': u.reg_no if u else '',
                'team_name': r.team_name, 'status': r.status,
                'payment_status': r.payment_status, 'attended': bool(r.attended)
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/registrations/user/<int:user_id>', methods=['GET'])
def get_user_registrations(user_id):
    try:
        regs   = Registration.query.filter_by(user_id=user_id).order_by(Registration.registered_at.desc()).all()
        result = []
        for r in regs:
            e = Event.query.get(r.event_id)
            if not e:
                continue
            ev = event_dict(e)
            ev['registration'] = {
                'id': r.id, 'status': r.status,
                'payment_status': r.payment_status, 'attended': bool(r.attended),
                'team_name': r.team_name
            }
            result.append(ev)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/registrations/<int:reg_id>/status', methods=['PUT'])
def update_registration_status(reg_id):
    try:
        data       = request.get_json()
        new_status = data.get('status')
        if new_status not in ('Approved', 'Rejected', 'Pending'):
            return jsonify({'error': 'Invalid status'}), 400
        reg = Registration.query.get(reg_id)
        if not reg:
            return jsonify({'error': 'Registration not found'}), 404
        reg.status = new_status
        db.session.commit()
        return jsonify({'message': f'Registration {new_status.lower()}'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/registrations/<int:reg_id>/attendance', methods=['PUT'])
def update_attendance(reg_id):
    try:
        data = request.get_json()
        reg  = Registration.query.get(reg_id)
        if not reg:
            return jsonify({'error': 'Registration not found'}), 404
        reg.attended = bool(data.get('attended', True))
        db.session.commit()
        return jsonify({'message': 'Attendance updated'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/registrations/<int:reg_id>/pay', methods=['PUT'])
def mark_paid(reg_id):
    try:
        reg = Registration.query.get(reg_id)
        if not reg:
            return jsonify({'error': 'Registration not found'}), 404
        reg.payment_status = 'Paid'
        db.session.commit()
        return jsonify({'message': 'Payment recorded'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────
# OD REQUESTS
# ─────────────────────────────────────────

def od_dict(o):
    student = User.query.get(o.user_id)
    event   = Event.query.get(o.event_id)
    return {
        'id': o.id, 'user_id': o.user_id,
        'student_name': student.name if student else '',
        'dept': student.dept if student else '',
        'reg_no': student.reg_no if student else '',
        'event_id': o.event_id,
        'event_name': event.name if event else '',
        'event_date': event.event_date.strftime('%d %b %Y') if event else '',
        'reason': o.reason, 'status': o.status,
        'requested_at': o.requested_at.strftime('%d %b %Y'),
    }


@app.route('/od', methods=['POST'])
def add_od():
    try:
        data     = request.get_json()
        required = ['user_id', 'event_id']
        if not data or not all(k in data for k in required):
            return jsonify({'error': 'Missing required fields'}), 400
        od = ODRequest(user_id=data['user_id'], event_id=data['event_id'],
                       reason=data.get('reason', ''))
        db.session.add(od)
        db.session.commit()
        return jsonify({'message': 'OD request submitted', 'id': od.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/od/user/<int:user_id>', methods=['GET'])
def get_user_od(user_id):
    try:
        ods = ODRequest.query.filter_by(user_id=user_id).order_by(ODRequest.requested_at.desc()).all()
        return jsonify([od_dict(o) for o in ods]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/od/faculty', methods=['GET'])
def get_faculty_od():
    try:
        status = request.args.get('status')
        query  = ODRequest.query
        if status:
            query = query.filter_by(status=status)
        ods = query.order_by(ODRequest.requested_at.desc()).all()
        return jsonify([od_dict(o) for o in ods]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/od/<int:od_id>/decision', methods=['PUT'])
def decide_od(od_id):
    try:
        data       = request.get_json()
        new_status = data.get('status')
        if new_status not in ('Approved', 'Rejected'):
            return jsonify({'error': "status must be 'Approved' or 'Rejected'"}), 400
        od = ODRequest.query.get(od_id)
        if not od:
            return jsonify({'error': 'OD request not found'}), 404
        od.status     = new_status
        od.faculty_id = data.get('faculty_id')
        od.decided_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'message': f'OD {new_status.lower()}'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────
# ANNOUNCEMENTS
# ─────────────────────────────────────────

@app.route('/announcements', methods=['GET'])
def get_announcements():
    try:
        event_id = request.args.get('event_id')
        query    = Announcement.query
        if event_id:
            query = query.filter_by(event_id=int(event_id))
        items  = query.order_by(Announcement.created_at.desc()).all()
        result = []
        for a in items:
            event = Event.query.get(a.event_id) if a.event_id else None
            result.append({
                'id': a.id, 'event_id': a.event_id,
                'event_name': event.name if event else None,
                'title': a.title, 'body': a.body,
                'created_at': a.created_at.strftime('%d %b %Y, %I:%M %p')
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/announcements', methods=['POST'])
def add_announcement():
    try:
        data     = request.get_json()
        required = ['organizer_id', 'title', 'body']
        if not data or not all(k in data for k in required):
            return jsonify({'error': 'Missing required fields'}), 400
        a = Announcement(
            organizer_id=data['organizer_id'], event_id=data.get('event_id'),
            title=data['title'], body=data['body']
        )
        db.session.add(a)
        db.session.commit()
        return jsonify({'message': 'Announcement posted', 'id': a.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────
# CHAT / MESSAGES
# ─────────────────────────────────────────

@app.route('/chats/<int:user_id>', methods=['GET'])
def get_chat_threads(user_id):
    try:
        msgs = Message.query.filter(
            db.or_(Message.sender_id == user_id, Message.receiver_id == user_id)
        ).order_by(Message.created_at.desc()).all()
        threads = {}
        for m in msgs:
            partner_id = m.receiver_id if m.sender_id == user_id else m.sender_id
            if partner_id not in threads:
                partner = User.query.get(partner_id)
                threads[partner_id] = {
                    'partner_id': partner_id,
                    'name': partner.name if partner else 'Unknown',
                    'role': partner.role if partner else '',
                    'last_message': m.text,
                    'time': m.created_at.strftime('%d %b, %I:%M %p'),
                    'unread': 0,
                }
            if m.receiver_id == user_id and not m.is_read:
                threads[partner_id]['unread'] += 1
        return jsonify(list(threads.values())), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/messages', methods=['GET'])
def get_messages():
    try:
        user_id  = request.args.get('user_id')
        other_id = request.args.get('other_id')
        if not user_id or not other_id:
            return jsonify({'error': 'user_id and other_id required'}), 400
        key  = conv_key(user_id, other_id)
        msgs = Message.query.filter_by(conversation_key=key).order_by(Message.created_at.asc()).all()
        for m in msgs:
            if m.receiver_id == int(user_id) and not m.is_read:
                m.is_read = True
        db.session.commit()
        return jsonify([{
            'id': m.id, 'sender_id': m.sender_id, 'receiver_id': m.receiver_id,
            'text': m.text, 'is_me': m.sender_id == int(user_id),
            'time': m.created_at.strftime('%I:%M %p'),
        } for m in msgs]), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/messages', methods=['POST'])
def send_message():
    try:
        data     = request.get_json()
        required = ['sender_id', 'receiver_id', 'text']
        if not data or not all(k in data for k in required):
            return jsonify({'error': 'Missing required fields'}), 400
        if int(data['sender_id']) == int(data['receiver_id']):
            return jsonify({'error': 'Cannot message yourself'}), 400
        m = Message(
            conversation_key=conv_key(data['sender_id'], data['receiver_id']),
            sender_id=data['sender_id'], receiver_id=data['receiver_id'],
            text=data['text']
        )
        db.session.add(m)
        db.session.commit()
        return jsonify({'message': 'Sent', 'id': m.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/contacts/<int:user_id>', methods=['GET'])
def get_contacts(user_id):
    try:
        role  = request.args.get('role')
        query = User.query.filter(User.id != user_id, User.is_blocked == False)
        if role:
            query = query.filter_by(role=role)
        users = query.order_by(User.name.asc()).all()
        return jsonify([{
            'id': u.id, 'name': u.name, 'role': u.role, 'dept': u.dept
        } for u in users]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────
# NOTIFICATIONS
# ─────────────────────────────────────────

@app.route('/notifications/<int:user_id>', methods=['GET'])
def get_notifications(user_id):
    try:
        items = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()
        return jsonify([{
            'id': n.id, 'title': n.title, 'body': n.body,
            'icon': n.icon, 'color': n.color, 'is_read': bool(n.is_read),
            'time': n.created_at.strftime('%d %b %Y, %I:%M %p')
        } for n in items]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/notifications', methods=['POST'])
def add_notification():
    try:
        data     = request.get_json()
        required = ['user_id', 'title', 'body']
        if not data or not all(k in data for k in required):
            return jsonify({'error': 'Missing required fields'}), 400
        n = Notification(
            user_id=data['user_id'], title=data['title'], body=data['body'],
            icon=data.get('icon'), color=data.get('color')
        )
        db.session.add(n)
        db.session.commit()
        return jsonify({'message': 'Notification created', 'id': n.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────
# FEEDBACK
# ─────────────────────────────────────────

@app.route('/feedback', methods=['POST'])
def add_feedback():
    try:
        data     = request.get_json()
        required = ['event_id', 'user_id', 'rating']
        if not data or not all(k in data for k in required):
            return jsonify({'error': 'Missing required fields'}), 400
        fb = Feedback(
            event_id=data['event_id'], user_id=data['user_id'],
            rating=int(data['rating']), comment=data.get('comment', '')
        )
        db.session.add(fb)
        db.session.commit()
        return jsonify({'message': 'Feedback submitted', 'id': fb.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/feedback/event/<int:event_id>', methods=['GET'])
def get_event_feedback(event_id):
    try:
        items = Feedback.query.filter_by(event_id=event_id).order_by(Feedback.created_at.desc()).all()
        avg   = round(sum(f.rating for f in items) / len(items), 1) if items else 0
        return jsonify({
            'average_rating': avg, 'count': len(items),
            'feedback': [{
                'id': f.id, 'rating': f.rating, 'comment': f.comment,
                'user': (User.query.get(f.user_id).name if User.query.get(f.user_id) else ''),
                'time': f.created_at.strftime('%d %b %Y')
            } for f in items]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────
# DASHBOARDS
# ─────────────────────────────────────────

@app.route('/dashboard/participant/<int:user_id>', methods=['GET'])
def participant_dashboard(user_id):
    try:
        regs      = Registration.query.filter_by(user_id=user_id).all()
        event_ids = [r.event_id for r in regs]
        registered = len(regs)
        upcoming  = Event.query.filter(Event.id.in_(event_ids), Event.status == 'Upcoming').count() if event_ids else 0
        completed = Event.query.filter(Event.id.in_(event_ids), Event.status == 'Completed').count() if event_ids else 0
        od_pending = ODRequest.query.filter_by(user_id=user_id, status='Pending').count()
        return jsonify({'registered': registered, 'upcoming': upcoming,
                        'completed': completed, 'od_pending': od_pending}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/dashboard/organizer/<int:user_id>', methods=['GET'])
def organizer_dashboard(user_id):
    try:
        events    = Event.query.filter_by(organizer_id=user_id).all()
        event_ids = [e.id for e in events]
        total_regs = Registration.query.filter(Registration.event_id.in_(event_ids)).count() if event_ids else 0
        pending   = Registration.query.filter(Registration.event_id.in_(event_ids),
                                              Registration.status == 'Pending').count() if event_ids else 0
        upcoming  = sum(1 for e in events if e.status == 'Upcoming')
        return jsonify({
            'total_events': len(events), 'upcoming_events': upcoming,
            'total_registrations': total_regs, 'pending_approvals': pending,
            'events': [event_dict(e) for e in events],
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/dashboard/faculty/<int:user_id>', methods=['GET'])
def faculty_dashboard(user_id):
    try:
        pending      = ODRequest.query.filter_by(status='Pending').count()
        approved     = ODRequest.query.filter_by(status='Approved').count()
        rejected     = ODRequest.query.filter_by(status='Rejected').count()
        total_events = Event.query.count()
        return jsonify({'pending_od': pending, 'approved_od': approved,
                        'rejected_od': rejected, 'total_events': total_events}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────
# ADMIN
# ─────────────────────────────────────────

@app.route('/admin/stats', methods=['GET'])
def admin_stats():
    try:
        return jsonify({
            'total_users': User.query.count(),
            'total_events': Event.query.count(),
            'total_registrations': Registration.query.count(),
            'active_sessions': ActiveSession.query.count(),
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/users', methods=['GET'])
def admin_users():
    try:
        role  = request.args.get('role')
        query = User.query
        if role and role.lower() != 'all':
            query = query.filter_by(role=role)
        users = query.order_by(User.created_at.desc()).all()
        return jsonify([user_brief(u) for u in users]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/users/<int:user_id>/block', methods=['PUT'])
def admin_block_user(user_id):
    try:
        data = request.get_json() or {}
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        user.is_blocked = bool(data['block']) if 'block' in data else (not user.is_blocked)
        db.session.commit()
        return jsonify({'message': 'User blocked' if user.is_blocked else 'User unblocked',
                        'is_blocked': bool(user.is_blocked)}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/admin/analytics', methods=['GET'])
def admin_analytics():
    try:
        cat_rows = db.session.execute(db.text("""
            SELECT e.category AS category, COUNT(r.id) AS total
            FROM events e LEFT JOIN registrations r ON r.event_id = e.id
            GROUP BY e.category ORDER BY total DESC
        """)).fetchall()
        top_rows = db.session.execute(db.text("""
            SELECT e.name AS name, COUNT(r.id) AS total
            FROM events e LEFT JOIN registrations r ON r.event_id = e.id
            GROUP BY e.id, e.name ORDER BY total DESC LIMIT 5
        """)).fetchall()
        role_rows = db.session.execute(db.text(
            "SELECT role, COUNT(id) AS total FROM users GROUP BY role"
        )).fetchall()
        return jsonify({
            'categories': [{'category': r[0], 'total': int(r[1])} for r in cat_rows],
            'top_events': [{'name': r[0], 'total': int(r[1])} for r in top_rows],
            'users_by_role': [{'role': r[0], 'total': int(r[1])} for r in role_rows],
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
