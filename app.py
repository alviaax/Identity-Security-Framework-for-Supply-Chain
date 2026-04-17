from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, User
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# ── Config ────────────────────────────────────────────
# IMPORTANT: Change SECRET_KEY to a long random string in production!
# Example: python -c "import secrets; print(secrets.token_hex(32))"
app.config['SECRET_KEY'] = 'change-this-to-a-random-secret-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'           # redirect here if @login_required fails
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))  # use db.session.get (not deprecated query.get)

# Create tables on first run
with app.app_context():
    db.create_all()


# ── Routes ────────────────────────────────────────────

@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name  = request.form.get('last_name', '').strip()
        email      = request.form.get('email', '').strip().lower()
        username   = request.form.get('username', '').strip()
        password   = request.form.get('password', '')
        role       = request.form.get('role', '')

        # Validation
        if not all([first_name, last_name, email, username, password, role]):
            flash('All fields are required.', 'error')
            return render_template('signup.html')

        if len(username) < 4:
            flash('Username must be at least 4 characters.', 'error')
            return render_template('signup.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('signup.html')

        if role not in ('admin', 'supplier', 'distributor'):
            flash('Invalid role selected.', 'error')
            return render_template('signup.html')

        if User.query.filter_by(username=username).first():
            flash('Username already exists! Please choose another.', 'error')
            return render_template('signup.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return render_template('signup.html')

        hashed_pw = generate_password_hash(password)
        new_user  = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            username=username,
            password=hashed_pw,
            role=role
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            # Redirect to the page the user originally tried to access
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin():
    if current_user.role != "admin":
        return "Access Denied"

    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    if current_user.role != "admin":
        return "Access Denied"

    user = User.query.get(id)

    if user and user.id == current_user.id:
        flash("You cannot delete yourself!", "error")
        return redirect('/admin')

    if user:
        db.session.delete(user)
        db.session.commit()
        flash("User deleted successfully!", "success")

    return redirect('/admin')

if __name__ == '__main__':
    app.run(debug=True)