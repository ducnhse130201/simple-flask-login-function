from flask import Flask, flash, redirect, render_template, request, session, abort
import os
from sqlalchemy.orm import sessionmaker
from tabledef import *
from hashlib import *
import threading
import json
import datetime
from mail import send_mail
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
# anti bruteforce
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
limiter = Limiter(
    app,
    key_func=get_remote_address,
)


def send_async_email(toaddr, subject, body):
    with app.app_context():
        threading.Thread(target=send_mail, args=(toaddr, subject, body)).start()

def log(path,to_log):
	log_lock = threading.RLock()
	with log_lock:
		with open(path, 'a') as logfile:
			logfile.write(to_log + '\n')

def init():
	engine = create_engine('sqlite:///users.db', echo=True)
	app.config['SECRET_KEY'] = 'sampleflaskappdc123'
	app.run(host='0.0.0.0',port=8080,debug=True)


@app.route("/")
def home():
	return render_template('index.html')


@app.route('/form_login',methods=['GET'])
def form_login():
	return render_template('login.html')

@app.route('/form_register', methods=['GET'])
def form_register():
	return render_template('register.html')

@app.route('/form_reset', methods=['GET'])
def form_reset():
	return render_template('reset.html')

@app.route('/login',methods=['POST'])
@limiter.limit("60 per minute",error_message="No No !!! Please don't brute force us :< ")
def login():
	POST_USERNAME = str(request.form['username'])
	POST_PASSWORD = str(request.form['password'])
	hash_password = sha256(POST_PASSWORD).hexdigest()

	Session = sessionmaker(bind=engine)
	s = Session()
	query = s.query(User).filter(User.username.in_([POST_USERNAME]), User.password.in_([hash_password]))
	result = query.first()

	# logging
	data = {}
	data['username'] = POST_USERNAME
	data['time'] = str(datetime.datetime.now()).split('.')[0]
	if result:
		data['type'] = True
		path = app.root_path + '/log/log_success.txt'
	else:
		data['type'] = False
		path = app.root_path + '/log/log_fail.txt'
	data = json.dumps(data)
	log(path, data)

	if result:
		session['logged_in'] = True
		return render_template('login.html',user=result.username)
	else:
		flash('Error: Wrong credentails')
		session['logged_in'] = False
		return render_template('login.html')

@app.route('/register',methods=['POST'])
@limiter.limit("60 per minute",error_message="No No !!! Please don't brute force us :< ")
def register():
	POST_USERNAME = str(request.form['username'])
	POST_PASSWORD = str(request.form['password'])
	POST_MAIL = str(request.form['mail'])

	Session = sessionmaker(bind=engine)
	s = Session()

	query = s.query(User).filter(User.username.in_([POST_USERNAME]))
	result = query.first()

	query2 = s.query(User).filter(User.mail.in_([POST_MAIL]))
	result2 = query2.first()

	if result:
		flash("Error: This user is already exist")
		return render_template('register.html')
	elif result2:
		flash("Error: This email is already exist")
		return render_template('register.html')
	else:
		# logging
		data = {}
		data['username'] = POST_USERNAME
		data['time'] = str(datetime.datetime.now()).split('.')[0]
		path = app.root_path + '/log/log_register.txt'
		data = json.dumps(data)
		log(path, 'Created user: ' + data)

		user = User(POST_USERNAME,POST_PASSWORD,POST_MAIL)
		s.add(user)
		s.commit()
		flash("You have registered successfully")
		return render_template('register.html')

@app.route('/reset', methods=['POST'])
@limiter.limit("10 per minute",error_message="No No !!! Please don't brute force us :< ")
def reset_password():
	POST_MAIL = str(request.form['reset_mail'])

	Session = sessionmaker(bind=engine)
	s = Session()
	query = s.query(User).filter(User.mail.in_([POST_MAIL]))
	result = query.first()

	# gen token
	if result:
		gen = Serializer(app.config['SECRET_KEY'], 100)
		token = gen.dumps({'username': result.username}).decode('utf-8')
		new_password_url = request.base_url + '/' + token
		msg = open('email/reset_password.txt','r').read().format(username=result.username,new_password_url = new_password_url)
		subject = "FlaskApp Reset Password"
		send_async_email(result.mail, subject, msg)

	flash("Please check your email, if you don't recieve please try again")
	return render_template('reset.html')

@app.route('/reset/<token>', methods=['GET'])
@limiter.limit("60 per minute",error_message="No No !!! Please don't brute force us :< ")
def verify_token(token):
	gen = Serializer(app.config['SECRET_KEY'], 100)
	try:
		data = gen.loads(token)
	except:
		session['is_verified'] = False
		flash("Error: Wrong reset token")
		return render_template('index.html')
	username = data.get('username')
	if username:
		session['is_verified'] = True
		session['user'] = username
		return render_template('new_password.html')
	else:
		session['is_verified'] = False
		return render_template('index.html')

@app.route('/new_password', methods= ['POST'])
@limiter.limit("10 per minute",error_message="No No !!! Please don't brute force us :< ")
def new_password():
	POST_PASSWORD = str(request.form['password'])
	POST_REPASSWORD = str(request.form['re_password'])

	if POST_PASSWORD != POST_REPASSWORD:
		flash("Error: Password and Re-Password must be identical")
		return render_template('new_password.html')
	else:
		Session = sessionmaker(bind=engine)
		s = Session()

		username = session['user']
		query = s.query(User).filter(User.username.in_([username]))
		result = query.first()

		if result:
			result.password = sha256(POST_PASSWORD).hexdigest()
			s.add(result)
			s.commit()
			session['is_verified'] = False
			session.pop("user")

			# logging
			data = {}
			data['username'] = username
			data['time'] = str(datetime.datetime.now()).split('.')[0]
			path = app.root_path + '/log/log_reset_password.txt'
			data = json.dumps(data)
			log(path, 'Reset password: ' + data)

			flash("You have successfully change password")
			return render_template('login.html')
		else:
			flash("Error: Something wrong, try again !!!")
			return render_template('reset.html')


@app.route("/logout")
def logout():
	session['logged_in'] = False
	return home()

if __name__ == "__main__":
	init()