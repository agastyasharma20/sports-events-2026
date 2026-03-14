from flask import Flask, request, jsonify, send_from_directory, session, Response
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
from functools import wraps
import os, csv, io, re

app = Flask(__name__, static_folder='static')
app.secret_key = 'piemr_sports2026_secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sports_registrations.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app, supports_credentials=True)
db = SQLAlchemy(app)

ADMIN_PASSWORD = 'piemr2026'
MAX_SPORTS_PER_STUDENT = 2
ROLL_PATTERN = re.compile(r'^0863[A-Za-z]{2,3}\d{5,6}$', re.IGNORECASE)

# ── MODEL ──────────────────────────────────────────────────────────────────────
class Registration(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100), nullable=False)
    enrolment     = db.Column(db.String(50),  nullable=False)
    mobile        = db.Column(db.String(15),  nullable=False)
    branch        = db.Column(db.String(80),  nullable=False)
    year          = db.Column(db.String(20),  nullable=False)
    event         = db.Column(db.String(50),  nullable=False)
    tshirt_size   = db.Column(db.String(10),  nullable=False)
    registered_at = db.Column(db.DateTime,    default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':           self.id,
            'name':         self.name,
            'enrolment':    self.enrolment,
            'mobile':       self.mobile,
            'branch':       self.branch,
            'year':         self.year,
            'event':        self.event,
            'tshirt_size':  self.tshirt_size,
            'registered_at': self.registered_at.strftime('%d %b %Y, %I:%M %p')
        }

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# ── CHECK ENROLMENT ────────────────────────────────────────────────────────────
@app.route('/api/check-enrolment', methods=['POST'])
def check_enrolment():
    data = request.get_json()
    enrolment = data.get('enrolment', '').strip().upper()
    if not enrolment:
        return jsonify({'valid': False, 'message': 'Enrolment number required.'}), 400
    if not ROLL_PATTERN.match(enrolment):
        return jsonify({
            'valid': False, 'format_error': True,
            'message': 'Wrong roll number format. Must be like 0863CS21001 — starts with 0863, then branch code (CS/IT/EC etc.), then digits.'
        }), 400
    existing = Registration.query.filter_by(enrolment=enrolment).all()
    count = len(existing)
    events_registered = [r.event for r in existing]
    if count >= MAX_SPORTS_PER_STUDENT:
        return jsonify({
            'valid': False, 'limit_reached': True, 'count': count,
            'events': events_registered,
            'message': f'This enrolment has already registered for {count} sport(s): {", ".join(events_registered)}. Maximum {MAX_SPORTS_PER_STUDENT} sports allowed. Please contact the Sports Department.'
        }), 409
    return jsonify({
        'valid': True, 'count': count, 'events': events_registered,
        'remaining': MAX_SPORTS_PER_STUDENT - count,
        'message': f'Valid. Registered for {count} sport(s). {MAX_SPORTS_PER_STUDENT - count} slot(s) remaining.'
    })

# ── REGISTER ──────────────────────────────────────────────────────────────────
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    required = ['name', 'enrolment', 'mobile', 'branch', 'year', 'event', 'tshirt_size']
    for field in required:
        if not str(data.get(field, '')).strip():
            return jsonify({'success': False, 'message': f'Field "{field}" is required.'}), 400

    enrolment = data['enrolment'].strip().upper()
    mobile    = data['mobile'].strip()
    event     = data['event'].strip()

    if not ROLL_PATTERN.match(enrolment):
        return jsonify({'success': False, 'message': 'Invalid roll number. Must start with 0863 + branch code + digits (e.g. 0863CS21001).'}), 400
    if not re.match(r'^\d{10}$', mobile):
        return jsonify({'success': False, 'message': 'Mobile number must be exactly 10 digits.'}), 400

    existing = Registration.query.filter_by(enrolment=enrolment).all()
    if len(existing) >= MAX_SPORTS_PER_STUDENT:
        events_done = [r.event for r in existing]
        return jsonify({
            'success': False, 'limit_reached': True,
            'message': f'Maximum {MAX_SPORTS_PER_STUDENT} sports reached. Already registered: {", ".join(events_done)}. Contact Sports Department.'
        }), 409
    for r in existing:
        if r.event.lower() == event.lower():
            return jsonify({'success': False, 'message': f'Already registered for {event}. Choose a different sport.'}), 409

    reg = Registration(
        name=data['name'].strip().title(), enrolment=enrolment,
        mobile=mobile, branch=data['branch'].strip(),
        year=data['year'].strip(), event=event,
        tshirt_size=data['tshirt_size'].strip()
    )
    db.session.add(reg)
    db.session.commit()
    return jsonify({
        'success': True, 'message': 'Registration successful!',
        'data': reg.to_dict(),
        'registrations_count': len(existing) + 1,
        'can_register_more': (len(existing) + 1) < MAX_SPORTS_PER_STUDENT
    }), 201

# ── ADMIN ─────────────────────────────────────────────────────────────────────
def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return jsonify({'success': False, 'message': 'Unauthorized.'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    if data.get('password') == ADMIN_PASSWORD:
        session['admin'] = True
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Incorrect password.'}), 401

@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('admin', None)
    return jsonify({'success': True})

@app.route('/api/admin/check', methods=['GET'])
def admin_check():
    return jsonify({'logged_in': session.get('admin', False)})

@app.route('/api/admin/registrations', methods=['GET'])
@require_admin
def get_registrations():
    search  = request.args.get('search', '').lower().strip()
    ef      = request.args.get('event', '').strip()
    yf      = request.args.get('year', '').strip()
    bf      = request.args.get('branch', '').strip()
    query   = Registration.query
    if ef: query = query.filter_by(event=ef)
    if yf: query = query.filter_by(year=yf)
    if bf: query = query.filter_by(branch=bf)
    regs = query.order_by(Registration.registered_at.desc()).all()
    if search:
        regs = [r for r in regs if search in r.name.lower() or search in r.enrolment.lower() or search in r.mobile]
    return jsonify({'success': True, 'data': [r.to_dict() for r in regs], 'total': len(regs)})

@app.route('/api/admin/stats', methods=['GET'])
@require_admin
def get_stats():
    all_regs = Registration.query.all()
    total    = len(all_regs)
    events, branches, years, sizes = {}, {}, {}, {}
    unique_students = set()
    for r in all_regs:
        events[r.event]      = events.get(r.event, 0) + 1
        branches[r.branch]   = branches.get(r.branch, 0) + 1
        years[r.year]        = years.get(r.year, 0) + 1
        sizes[r.tshirt_size] = sizes.get(r.tshirt_size, 0) + 1
        unique_students.add(r.enrolment)
    top_event  = max(events,   key=events.get)   if events   else '—'
    top_branch = max(branches, key=branches.get) if branches else '—'
    recent = Registration.query.order_by(Registration.registered_at.desc()).limit(5).all()
    return jsonify({
        'success': True, 'total': total,
        'unique_students': len(unique_students),
        'events_count': len(events), 'events': events,
        'branches': branches, 'years': years, 'sizes': sizes,
        'branches_count': len(branches), 'top_event': top_event,
        'top_branch': top_branch, 'recent': [r.to_dict() for r in recent]
    })

@app.route('/api/admin/delete/<int:reg_id>', methods=['DELETE'])
@require_admin
def delete_registration(reg_id):
    reg = Registration.query.get_or_404(reg_id)
    db.session.delete(reg)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/admin/export', methods=['GET'])
@require_admin
def export_csv():
    regs = Registration.query.order_by(Registration.registered_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['#','Name','Enrolment','Mobile','Branch','Year','Event','T-Shirt Size','Registered At'])
    for i, r in enumerate(regs, 1):
        writer.writerow([i, r.name, r.enrolment, r.mobile, r.branch, r.year, r.event, r.tshirt_size,
                         r.registered_at.strftime('%d %b %Y %I:%M %p')])
    output.seek(0)
    return Response(output.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment;filename=sports_registrations_2026.csv'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅  Database ready.")
    print("🚀  Running at http://localhost:5000")
    app.run(debug=True, port=5000)