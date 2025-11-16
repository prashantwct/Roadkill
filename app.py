# Production-ready Flask app with factory pattern and SQLAlchemy

import os
import uuid
import qrcode
import csv
import random
import string
from io import StringIO, BytesIO
from datetime import datetime, timedelta

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, send_file, current_app
)
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import (
    LoginManager, UserMixin, login_user,
    login_required, logout_user, current_user
)
from werkzeug.utils import secure_filename

# ========================
# EXTENSIONS
# ========================

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = "login"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ========================
# HELPERS
# ========================

def ist_now():
    return datetime.utcnow() + timedelta(hours=5, minutes=30)

# ========================
# MODELS
# ========================

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    pw_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(120))
    email = db.Column(db.String(120))
    role = db.Column(db.String(50), default='collector')
    is_approved = db.Column(db.Boolean, default=False)

class Site(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    code = db.Column(db.String(20), nullable=False, unique=True)
    description = db.Column(db.Text)

class Carcass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(4), unique=True, nullable=False)

    site_id = db.Column(db.Integer, db.ForeignKey('site.id'))
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    species = db.Column(db.String(140))
    datetime_found = db.Column(db.DateTime, default=ist_now)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    notes = db.Column(db.Text)

    site = db.relationship('Site')
    reporter = db.relationship('User')
    samples = db.relationship('Sample', backref='carcass', lazy=True)

class Sample(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    carcass_id = db.Column(db.Integer, db.ForeignKey('carcass.id'))
    uuid = db.Column(db.String(36), nullable=False, unique=True)
    label = db.Column(db.String(120), nullable=False, unique=True)
    sample_type = db.Column(db.String(60))
    collected_by = db.Column(db.String(120))
    collected_at = db.Column(db.DateTime, default=ist_now)
    storage = db.Column(db.String(120))
    notes = db.Column(db.Text)
    qr_path = db.Column(db.String(300))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ========================
# DB INIT
# ========================

def init_db():
    if not User.query.filter_by(username="admin").first():
        hashed = bcrypt.generate_password_hash("admin").decode("utf-8")
        admin = User(
            username="admin",
            pw_hash=hashed,
            full_name="Administrator",
            role="admin",
            is_approved=True
        )
        db.session.add(admin)
        db.session.commit()

def setup_database(app):
    with app.app_context():
        db.create_all()
        init_db()

# ========================
# HELPERS FOR LABELS
# ========================

def generate_unique_carcass_code():
    chars = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choices(chars, k=4))
        if not Carcass.query.filter_by(code=code).first():
            return code

def next_sequence_for_site_date(site_code, date_str):
    like_prefix = f"{site_code}-{date_str}-%"
    count = Sample.query.filter(Sample.label.like(like_prefix)).count()
    return count + 1

def make_label(site_code, dt, seq, sample_type):
    date_str = dt.strftime('%Y%m%d')
    seq_str = str(seq).zfill(3)
    type_code = ''.join([c for c in (sample_type or 'UNK').upper() if c.isalpha()])[:3]
    rand = uuid.uuid4().hex[:4].upper()
    return f"{site_code}-{date_str}-{seq_str}-{type_code}-{rand}"

def generate_qr_for_label(label):
    img = qrcode.make(label)
    fname = secure_filename(f"{label}.png")
    path = os.path.join(current_app.config["LABEL_DIR"], fname)
    img.save(path)
    return path

# ========================
# APPLICATION FACTORY
# ========================

def create_app():
    app = Flask(__name__)

    from datetime import datetime as dt
    app.jinja_env.globals['datetime'] = dt

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'replace-this')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    label_dir = os.path.join(BASE_DIR, 'static', 'labels')
    os.makedirs(label_dir, exist_ok=True)
    app.config['LABEL_DIR'] = label_dir

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    register_routes(app)
    setup_database(app)

    return app

# ========================
# ROUTES
# ========================

def is_admin():
    return current_user.is_authenticated and current_user.role == "admin"

def register_routes(app):

    # ---------------- HOME ----------------
    @app.route('/')
    def index():
        sites = Site.query.all()
        return render_template('index.html', sites=sites)

    # ---------------- RESET ADMIN PW ----------------
    @app.route('/reset_admin_pw')
    def reset_admin_pw():
        admin = User.query.filter_by(username="admin").first()
        if not admin:
            return "Admin user not found."

        new_pw = "admin123"
        admin.pw_hash = bcrypt.generate_password_hash(new_pw).decode("utf-8")
        db.session.commit()
        return "Admin password reset to: admin123"

    # ---------------- LOGIN ----------------
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            u = request.form['username']
            pw = request.form['password']
            user = User.query.filter_by(username=u).first()

            if not user:
                flash("Invalid username or password")
                return redirect(url_for('login'))

            if not user.is_approved:
                flash("Your account is pending admin approval.")
                return redirect(url_for('login'))

            if bcrypt.check_password_hash(user.pw_hash, pw):
                login_user(user)
                return redirect(url_for('index'))

            flash("Invalid username or password")

        return render_template('login.html')

    # ---------------- REGISTER ----------------
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            u = request.form['username']
            pw = request.form['password']

            if User.query.filter_by(username=u).first():
                flash("Username already exists")
                return redirect(url_for('register'))

            hashed = bcrypt.generate_password_hash(pw).decode("utf-8")
            user = User(
                username=u,
                pw_hash=hashed,
                full_name=request.form.get('full_name'),
                is_approved=False
            )
            db.session.add(user)
            db.session.commit()

            flash("Registration submitted — wait for admin approval.")
            return redirect(url_for('login'))

        return render_template('register.html')

    # ---------------- LOGOUT ----------------
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash("Logged out")
        return redirect(url_for('index'))

    # ---------------- CHANGE PASSWORD ----------------
    @app.route('/change_password', methods=['GET', 'POST'])
    @login_required
    def change_password():
        if request.method == 'POST':
            cur = request.form.get('current_password')
            new = request.form.get('new_password')
            conf = request.form.get('confirm_password')

            if not bcrypt.check_password_hash(current_user.pw_hash, cur):
                flash("Current password incorrect.")
                return redirect(url_for('change_password'))

            if new != conf:
                flash("New passwords do not match.")
                return redirect(url_for('change_password'))

            current_user.pw_hash = bcrypt.generate_password_hash(new).decode("utf-8")
            db.session.commit()

            flash("Password updated.")
            return redirect(url_for('index'))

        return render_template('change_password.html')

    # ---------------- ADMIN ----------------
    @app.route('/admin')
    @login_required
    def admin_dashboard():
        if not is_admin():
            flash("Admin access required.")
            return redirect(url_for('index'))

        return render_template(
            'admin_dashboard.html',
            total_users=User.query.count(),
            pending_users=User.query.filter_by(is_approved=False).count(),
            total_sites=Site.query.count(),
            total_carcasses=Carcass.query.count(),
            total_samples=Sample.query.count(),
            recent_carcasses=Carcass.query.order_by(Carcass.datetime_found.desc()).limit(5).all(),
            recent_samples=Sample.query.order_by(Sample.collected_at.desc()).limit(5).all()
        )

    # ---------------- MANAGE USERS ----------------
    @app.route('/admin/users')
    @login_required
    def manage_users():
        if not is_admin():
            flash("Admin access required.")
            return redirect(url_for('index'))

        return render_template('admin_users.html', users=User.query.all())

    @app.route('/admin/user/<int:user_id>/approve')
    @login_required
    def approve_user(user_id):
        if not is_admin():
            flash("Admin access required.")
            return redirect(url_for('index'))

        u = User.query.get_or_404(user_id)
        u.is_approved = True
        db.session.commit()

        flash(f"User {u.username} approved.")
        return redirect(url_for('manage_users'))

    # ---------------- SITES ----------------
    @app.route('/sites/new', methods=['GET', 'POST'])
    @login_required
    def new_site():
        if not is_admin():
            flash("Admin access required.")
            return redirect(url_for('index'))

        if request.method == 'POST':
            name = request.form['name']
            code = request.form['code'].upper()

            if Site.query.filter_by(code=code).first():
                flash("Site code exists already.")
                return redirect(url_for('new_site'))

            site = Site(name=name, code=code, description=request.form.get('description'))
            db.session.add(site)
            db.session.commit()

            flash("Site added.")
            return redirect(url_for('index'))

        return render_template('new_site.html')

    # ---------------- VIEW SITE ----------------
    @app.route('/site/<int:site_id>')
    @login_required
    def view_site(site_id):
        site = Site.query.get_or_404(site_id)
        carcasses = Carcass.query.filter_by(site_id=site_id).all()
        return render_template('view_site.html', site=site, carcasses=carcasses)

    # ---------------- NEW CARCASS ----------------
    @app.route('/carcass/new', methods=['GET', 'POST'])
    @login_required
    def new_carcass():
        site_id = request.args.get('site_id', type=int)

        if request.method == 'POST':
            site_id = int(request.form['site_id'])
            species = request.form.get('species')

            dt = request.form.get('datetime')
            dt_obj = datetime.fromisoformat(dt) + timedelta(hours=5, minutes=30) if dt else ist_now()

            carcass = Carcass(
                code=generate_unique_carcass_code(),
                site_id=site_id,
                reporter_id=current_user.id,
                species=species,
                datetime_found=dt_obj,
                latitude=request.form.get('latitude'),
                longitude=request.form.get('longitude'),
                notes=request.form.get('notes')
            )
            db.session.add(carcass)
            db.session.commit()

            flash("Carcass recorded.")
            return redirect(url_for('view_carcass', carcass_id=carcass.id))

        return render_template('new_carcass.html', sites=Site.query.all(), site_id=site_id)

    # ---------------- VIEW CARCASS ----------------
    @app.route('/carcass/<int:carcass_id>')
    def view_carcass(carcass_id):
        carcass = Carcass.query.get_or_404(carcass_id)
        return render_template('carcass.html', c=carcass)

    # ---------------- NEW SAMPLE ----------------
    @app.route('/carcass/<int:carcass_id>/sample/new', methods=['GET', 'POST'])
    @login_required
    def new_sample(carcass_id):
        c = Carcass.query.get_or_404(carcass_id)

        if request.method == 'POST':
            sample_type = request.form.get('sample_type')
            collected_at_str = request.form.get('collected_at')

            collected_at = (
                datetime.fromisoformat(collected_at_str) + timedelta(hours=5, minutes=30)
                if collected_at_str else ist_now()
            )

            seq = next_sequence_for_site_date(c.site.code, collected_at.strftime('%Y%m%d'))
            label = make_label(c.site.code, collected_at, seq, sample_type)
            suid = str(uuid.uuid4())
            qr_path = generate_qr_for_label(label)

            sample = Sample(
                carcass_id=carcass_id,
                uuid=suid,
                label=label,
                sample_type=sample_type,
                collected_by=current_user.username,
                collected_at=collected_at,
                storage=request.form.get('storage'),
                notes=request.form.get('notes'),
                qr_path=qr_path
            )
            db.session.add(sample)
            db.session.commit()

            flash(f"Sample {label} created.")

            # Which button was pressed?
            if request.form.get("action") == "add_another":
                return redirect(url_for('new_sample', carcass_id=carcass_id))

            return redirect(url_for('view_carcass', carcass_id=carcass_id))

        return render_template('new_sample.html', c=c)

    # ---------------- EXPORT ----------------
    @app.route('/samples/export')
    @login_required
    def export_samples():
        samples = Sample.query.all()

        si = StringIO()
        cw = csv.writer(si)

        cw.writerow([
            'label', 'uuid', 'sample_type', 'collected_by', 'collected_at_IST',
            'storage', 'notes', 'carcass_id', 'carcass_code', 'site_code', 'species'
        ])

        for s in samples:
            cw.writerow([
                s.label,
                s.uuid,
                s.sample_type,
                s.collected_by,
                s.collected_at.strftime('%Y-%m-%d %H:%M:%S') + ' IST',
                s.storage,
                s.notes,
                s.carcass_id,
                s.carcass.code if s.carcass else '',
                s.carcass.site.code if s.carcass and s.carcass.site else '',
                s.carcass.species if s.carcass else ''
            ])

        output = BytesIO(si.getvalue().encode('utf-8'))
        output.seek(0)

        filename = f"samples_{ist_now().strftime('%Y%m%d_%H%M')}.csv"
        return send_file(output, mimetype='text/csv', as_attachment=True, download_name=filename)

# ========================
# GUNICORN ENTRYPOINT
# ========================

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
