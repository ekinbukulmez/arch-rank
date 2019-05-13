from flask import render_template
from app import app, db
from app.forms import Login, SignUp, CitizenReport
from flask_login import current_user, login_user, logout_user, login_required
from app.models import Citizen, Report
from flask import redirect, url_for, flash, request
from sqlalchemy import func
import string, random

def gen_report_id():
    chars = string.digits
    return int(''.join(random.choice(chars) for _ in range(0, 6)))

def get_links():
    return [
        {
            'text': 'About',
            'path': url_for('about')
        },
        {
            'text': 'Rank',
            'path': url_for('rank')
        },
        {
            'text': 'Login',
            'path': url_for('login')
        }
    ]

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Welcome', links=get_links())

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('feed'))
    form = SignUp()
    if form.validate_on_submit():
        try:
            citizen = Citizen(citizen_id=form.citizen_id.data, name=form.citizen_id.data, score=0)  
            citizen.set_password(form.password.data)
            db.session.add(citizen)
            db.session.commit()
            return redirect(url_for('login'))
        except Exception as e:
            print('There was an error creating new user.' + str(e))
    return render_template('signup.html', title='Join Arch', form=form)

@app.route('/feed', methods=['GET', 'POST'])
@login_required
def feed():
    invalid_citizen = False
    submit_error = False

    form = CitizenReport(reporter=current_user.citizen_id)
    if form.validate_on_submit():
        reported = Citizen.query.filter_by(citizen_id=form.traitor.data).first()
        if reported is None:
            invalid_citizen = True
            return redirect(url_for('feed'))
        else:
            try:
                reported.score = reported.score + float(form.category.data)
                db.session.commit()
                new_report = Report(reporter_id=current_user.citizen_id, reported_id=reported.citizen_id, report_id=gen_report_id(), body=form.body.data)
                db.session.add(new_report)
                db.session.commit()
                print('Successful report submission')
            except Exception as score_error:
                print('Report submission error: ' + str(score_error))
    else:
        print('Form validation error')
        print(form.errors)
    reports = Report.query.all()
    return render_template('feed.html', title='Feed', form=form, reports=reports)

@app.route('/profile/<citizen_id>')
@login_required
def profile(citizen_id):
    citizen = Citizen.query.filter_by(citizen_id=citizen_id).first_or_404()
    return render_template('profile.html', title='My Profile', links=get_links())

@app.route('/rank')
def rank():
    page = request.args.get('page', 1, type=int)
    citizens = Citizen.query.order_by(Citizen.score.desc()).paginate(page, 10, False)
    next_citizens = url_for('rank', page=citizens.next_num) \
        if citizens.has_next else None
    prev_citizens = url_for('rank', page=citizens.prev_num) \
        if citizens.has_prev else None
    top_citizens = Citizen.query.filter(Citizen.score >= 5000).order_by(func.random()).limit(3)
    return render_template('rank.html', citizens=citizens.items, tops=top_citizens, next=next_citizens, prev=prev_citizens)

@app.route('/login',  methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('feed'))
    form = Login()
    if not form.validate_on_submit():
        print('Form did not validate ')
    if form.validate_on_submit():
        citizen = Citizen.query.filter_by(citizen_id=form.citizen_id.data).first()
        if citizen is None or not citizen.check_password(form.password.data):
            print('Bad login attempt')
            return redirect(url_for('login'))
        login_user(citizen)
        flash('Good login')
        return redirect(url_for('feed'))
    return render_template('login.html', form=form, links=get_links(), title="Login")

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/about')
def about():
    return 'This is about'