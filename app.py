from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
import os, uuid, qrcode, csv
from io import StringIO, BytesIO

# -------------------- Setup --------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'roadkill.db')
LABEL_DIR = os.path.join(BASE_DIR, 'static', 'labels')
os.makedirs(LABEL_DIR, exist_ok=True)

# ---- Fixed IST timestamp ----
def ist_now():
    """Return current time in IST (UTC+5:30) as naive datetime."""
    utc_now = datetime.utcnow()
    ist_time = utc_now + timedelta(hours=5, minutes=30)
    return ist_time.replace(tzinfo=None)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'replace-this-with-a-secure-random-string')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(postgresql://neondb_owner:npg_JkOv8tRzqmp0@ep-crimson-night-a48lvwz1-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_ENABLED'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# -------------------- Models --------------------
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

# -------------------- Helpers --------------------
def init_db():
    """Create database and default admin user"""
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            pw = bcrypt.generate_password_hash('admin').decode('utf-8')
            admin = User(username='admin', pw_hash=pw, full_name='Administrator',
                         role='admin', is_approved=True)
            db.session.add(admin)
            db.session.commit()

def is_admin():
    return current_user.is_authenticated and current_user.role == 'admin'

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
    path = os.path.join(LABEL_DIR, fname)
    img.save(path)
    return path

# -------------------- Routes --------------------
@app.route('/')
def index():
    sites = Site.query.all()
    return render_template('index.html', sites=sites)

# --- Authentication ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        pw = request.form['password']
        user = User.query.filter_by(username=u).first()

        if not user:
            flash('Invalid username or password')
            return redirect(url_for('login'))

        if not user.is_approved:
            flash('Your account is pending admin approval.')
            return redirect(url_for('login'))

        if user and bcrypt.check_password_hash(user.pw_hash, pw):
            login_user(user)
            flash('Logged in successfully')
            return redirect(url_for('index'))

        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u = request.form['username']
        pw = request.form['password']
        if User.query.filter_by(username=u).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        ph = bcrypt.generate_password_hash(pw).decode('utf-8')
        user = User(
            username=u,
            pw_hash=ph,
            full_name=request.form.get('full_name'),
            is_approved=False
        )
        db.session.add(user)
        db.session.commit()
        flash('Registration submitted. Wait for admin approval.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out')
    return redirect(url_for('index'))

# --- Change Password ---
@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_pw = request.form.get('current_password')
        new_pw = request.form.get('new_password')
        confirm_pw = request.form.get('confirm_password')

        # Validate current password
        if not bcrypt.check_password_hash(current_user.pw_hash, current_pw):
            flash('Current password is incorrect.')
            return redirect(url_for('change_password'))

        # Validate new passwords match
        if new_pw != confirm_pw:
            flash('New passwords do not match.')
            return redirect(url_for('change_password'))

        # Update password
        hashed_pw = bcrypt.generate_password_hash(new_pw).decode('utf-8')
        current_user.pw_hash = hashed_pw
        db.session.commit()

        flash('Password changed successfully!')
        return redirect(url_for('index'))

    return render_template('change_password.html')


# --- Admin Dashboard ---
@app.route('/admin')
@login_required
def admin_dashboard():
    if not is_admin():
        flash("Admin access required.")
        return redirect(url_for('index'))

    total_users = User.query.count()
    pending_users = User.query.filter_by(is_approved=False).count()
    total_sites = Site.query.count()
    total_carcasses = Carcass.query.count()
    total_samples = Sample.query.count()

    return render_template(
        'admin_dashboard.html',
        total_users=total_users,
        pending_users=pending_users,
        total_sites=total_sites,
        total_carcasses=total_carcasses,
        total_samples=total_samples
    )

# --- ADMIN: Manage users ---
@app.route('/admin/users')
@login_required
def manage_users():
    if not is_admin():
        flash("Admin access required.")
        return redirect(url_for('index'))
    users = User.query.all()
    return render_template('admin_users.html', users=users)

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

@app.route('/admin/user/<int:user_id>/delete')
@login_required
def delete_user(user_id):
    if not is_admin():
        flash("Admin access required.")
        return redirect(url_for('index'))
    u = User.query.get_or_404(user_id)
    if u.username == 'admin':
        flash("Cannot delete the admin account.")
        return redirect(url_for('manage_users'))
    db.session.delete(u)
    db.session.commit()
    flash(f"User {u.username} deleted.")
    return redirect(url_for('manage_users'))

# --- Admin Reset User Password ---
@app.route('/admin/user/<int:user_id>/reset_password', methods=['POST'])
@login_required
def reset_user_password(user_id):
    if not is_admin():
        flash("Admin access required.")
        return redirect(url_for('index'))
    
    u = User.query.get_or_404(user_id)
    new_pw = request.form.get('new_password')

    if not new_pw:
        flash("Password cannot be empty.")
        return redirect(url_for('manage_users'))
    
    u.pw_hash = bcrypt.generate_password_hash(new_pw).decode('utf-8')
    db.session.commit()
    flash(f"Password for {u.username} has been reset successfully.")
    return redirect(url_for('manage_users'))



# --- Site management ---
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
            flash('Site code already exists')
            return redirect(url_for('new_site'))
        site = Site(name=name, code=code, description=request.form.get('description'))
        db.session.add(site)
        db.session.commit()
        flash('Site added successfully')
        return redirect(url_for('index'))
    return render_template('new_site.html')

# --- View Single Site ---
@app.route('/site/<int:site_id>')
@login_required
def view_site(site_id):
    site = Site.query.get_or_404(site_id)
    carcasses = Carcass.query.filter_by(site_id=site_id).all()
    return render_template('view_site.html', site=site, carcasses=carcasses)


@app.route('/carcass/new', methods=['GET', 'POST'])
@login_required
def new_carcass():
    site_id = request.args.get('site_id', type=int)
    if request.method == 'POST':
        site_id = int(request.form['site_id'])
        species = request.form.get('species')
        dt = request.form.get('datetime')
        dt_obj = datetime.fromisoformat(dt) + timedelta(hours=5, minutes=30) if dt else ist_now()

        c = Carcass(site_id=site_id, reporter_id=current_user.id,
                    species=species, datetime_found=dt_obj,
                    latitude=request.form.get('latitude'),
                    longitude=request.form.get('longitude'),
                    notes=request.form.get('notes'))
        db.session.add(c)
        db.session.commit()
        flash('Carcass recorded')
        return redirect(url_for('view_carcass', carcass_id=c.id))

    sites = Site.query.all()
    return render_template('new_carcass.html', sites=sites, site_id=site_id)

@app.route('/carcass/<int:carcass_id>')
def view_carcass(carcass_id):
    c = Carcass.query.get_or_404(carcass_id)
    return render_template('carcass.html', c=c)

# --- Sample management ---
@app.route('/carcass/<int:carcass_id>/sample/new', methods=['GET', 'POST'])
@login_required
def new_sample(carcass_id):
    c = Carcass.query.get_or_404(carcass_id)
    if request.method == 'POST':
        sample_type = request.form.get('sample_type')
        collected_at_str = request.form.get('collected_at')
        collected_at = datetime.fromisoformat(collected_at_str) + timedelta(hours=5, minutes=30) if collected_at_str else ist_now()

        seq = next_sequence_for_site_date(c.site.code, collected_at.strftime('%Y%m%d'))
        label = make_label(c.site.code, collected_at, seq, sample_type)
        suid = str(uuid.uuid4())
        qr_path = generate_qr_for_label(label)

        s = Sample(carcass_id=carcass_id, uuid=suid, label=label,
                   sample_type=sample_type, collected_by=current_user.username,
                   collected_at=collected_at, storage=request.form.get('storage'),
                   notes=request.form.get('notes'), qr_path=qr_path)
        db.session.add(s)
        db.session.commit()
        flash(f'Sample {label} created successfully')
        return redirect(url_for('view_sample', sample_id=s.id))

    return render_template('new_sample.html', c=c)

@app.route('/sample/<int:sample_id>')
def view_sample(sample_id):
    s = Sample.query.get_or_404(sample_id)
    return render_template('sample.html', s=s)

# --- Export samples as CSV ---
@app.route('/samples/export')
@login_required
def export_samples():
    samples = Sample.query.all()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['label','uuid','sample_type','collected_by','collected_at_IST','storage','notes','carcass_id','site_code','species'])
    for s in samples:
        cw.writerow([
            s.label, s.uuid, s.sample_type, s.collected_by,
            s.collected_at.strftime('%Y-%m-%d %H:%M:%S') + " IST",
            s.storage, s.notes, s.carcass_id,
            s.carcass.site.code, s.carcass.species
        ])
    output = BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    si.close()
    filename = f"samples_{ist_now().strftime('%Y%m%d_%H%M')}.csv"
    return send_file(output, mimetype='text/csv', as_attachment=True, download_name=filename)

# -------------------- Run --------------------
with app.app_context():
    print("\n=== Registered Routes ===")
    print(app.url_map)
    print("=========================\n")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
