import base64
import binascii
import datetime
import hashlib
import json
import os
import plistlib
import random
import re
import string
import time
import uuid
import xmltodict
from flask import Flask, request, jsonify, make_response, send_file, render_template, session, redirect, url_for, send_from_directory
import mysql.connector as mysql

# Extensions to Install:
# pip3 install Flask
# pip3 install xmltodict
# pip3 install mysql-connector-python

app = Flask(__name__)

#MySQL Connection Details
db = mysql.connect(
	host = 'localhost',
	user = 'root',
	passwd = 'your_mysql_password',
	database = 'ast_server'
)

cursor = db.cursor(buffered=True)
#cursor = db.cursor(buffered=True,dictionary=true)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'your secret key'

# Functions:

def find_text(text, sub1, sub2):
	pos1 = text.find(sub1) 
	pos2 = text.find(sub2) + len(sub2)
	return text[pos1:pos2]

def session_token_create(size=35, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))

def opcode_create(size=25, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))

def diagnostic_event_num_create(size=23, chars=string.digits):
	return ''.join(random.choice(chars) for _ in range(size))

def store_num_create(size=6, chars=string.digits):
	return ''.join(random.choice(chars) for _ in range(size))

def soap_date():
	date_now = datetime.datetime.now()
	date = date_now.strftime("%d-%b-%Y %H:%M:%S")
	return date

def string_date_to_unix_timestamp(diagnosticStartTimeStamp):
	converted = int(datetime.datetime.strptime(diagnosticStartTimeStamp, '%d-%b-%y %H:%M:%S').strftime("%s"))
	return converted

def unix_timestamp():
	ustamp = int(time.time())
	return ustamp

def hash_password(password):
    """Hash a password for storing."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')
 
def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512', provided_password.encode('utf-8'), salt.encode('ascii'), 100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password

def verify_credentials(email, accountID, password):
	cursor.execute('SELECT * FROM users_accounts WHERE user_email = %s AND user_account_id = %s', (email, accountID))
	fetched = cursor.fetchone()
	if fetched != None:
		user_uuid = fetched[1]
		stored_pass = fetched[7]
		verification = verify_password(stored_pass, password)
		if verification == True:
			return True, user_uuid
	else:
		return False, None

def verify_credentials_for_diagnostics(token):
	cursor.execute('SELECT * FROM users_tokens WHERE user_session_token = %(user_session_token)s', { 'user_session_token': token })
	fetched = cursor.fetchone()
	if fetched != None:
		user_uuid = fetched[1]
		existing_token = fetched[2]
		return True, user_uuid, existing_token
	else:
		return False, None, None

def verify_session_token(token):
	cursor.execute('SELECT user_session_token FROM users_tokens WHERE user_session_token = %(user_session_token)s', { 'user_session_token': token })
	fetched = cursor.fetchone()
	if fetched != None:
		existing_token = fetched[0]
		return True, existing_token
	else:
		return False, None

def verify_diagnosticEventNumber(diagnosticEventNumber):
	cursor.execute('SELECT diagnostic_event_number FROM users_diagnostics_headers WHERE diagnostic_event_number = %(diagnostic_event_number)s', { 'diagnostic_event_number': diagnosticEventNumber })
	fetched = cursor.fetchone()
	if fetched != None:
		existing_diag_num = fetched[0]
		return True, existing_diag_num
	else:
		return False, None

def generate_mysql_session_token(user_uuid):
	sess_token = session_token_create()
	created_at = unix_timestamp()
	expires_at = created_at + 1500 # - 25 min duration - this seems to be how often the AST Gateway Manager authenticates itself
	#expires_at = created_at + 3600 # - 1 hour duration
	#expires_at = created_at + 7200 # - 2 hour duration
	# create instance in users_tokens db, check if one exists, and expired if neither then create
	cursor.execute('INSERT INTO users_tokens VALUES (NULL, %s, %s, %s, %s, NULL)', (user_uuid, sess_token, expires_at, created_at))
	db.commit()
	return sess_token

def generate_ActivateResponse():
	response = {
		"soap:Envelope": {
			"@xmlns:soap": "http://schemas.xmlsoap.org/soap/envelope/", 
			"@xmlns:tns": "http://adr.apple.com/services/capture", 
			"@xmlns:wsu": "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd", 
			"@xmlns:global-rr": "http://adr.apple.com/types/global", 
			"@xmlns:cap-rr": "http://adr.apple.com/types/capture", 
			"@xmlns:basic": "http://adr.apple.com/types/basic", 
			"@xmlns:base": "http://adr.apple.com/types/base", 
				"soap:Body": {
					"cap-rr:ActivateUserResponse": {
						"@xmlns:cap-rr": "http://adr.apple.com/types/capture", 
						"opCode": opcode_create()}}}}
	soaped = xmltodict.unparse(response)
	return soaped

def generate_AuthenticateResponse(token):
	response = {
		"soap:Envelope": {
			"@xmlns:soap": "http://schemas.xmlsoap.org/soap/envelope/", 
			"@xmlns:tns": "http://adr.apple.com/services/capture", 
			"@xmlns:wsu": "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd", 
			"@xmlns:global-rr": "http://adr.apple.com/types/global", 
			"@xmlns:cap-rr": "http://adr.apple.com/types/capture", 
				"soap:Body": {
					"global-rr:AuthenticateResponse": {
					"@xmlns:global-rr": "http://adr.apple.com/types/global", 
						"userSessionToken": token, 
						"opCode": opcode_create()}}}}
	soaped = xmltodict.unparse(response)
	return soaped

def generate_DiagnosticHeartBeatResponse():
	response = {
		"soap:Envelope": {
			"@xmlns:soap": "http://schemas.xmlsoap.org/soap/envelope/", 
			"@xmlns:tns": "http://adr.apple.com/services/capture", 
			"@xmlns:wsu": "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd", 
			"@xmlns:global-rr": "http://adr.apple.com/types/global", 
			"@xmlns:cap-rr": "http://adr.apple.com/types/capture", 
				"soap:Body": {
					"cap-rr:DiagnosticHeartBeatResponse": {
						"@xmlns:cap-rr": "http://adr.apple.com/types/capture", 
						"timeStamp": soap_date(), 
						"opCode": "SUCCESS"}}}}
	soaped = xmltodict.unparse(response)
	return soaped

def generate_CreateDiagnosticHeaderResponse():
	diagnostic_event_number = diagnostic_event_num_create()
	response = {
		"soap:Envelope": {
			"@xmlns:soap": "http://schemas.xmlsoap.org/soap/envelope/", 
			"@xmlns:tns": "http://adr.apple.com/services/capture", 
			"@xmlns:wsu": "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd", 
			"@xmlns:global-rr": "http://adr.apple.com/types/global", 
			"@xmlns:cap-rr": "http://adr.apple.com/types/capture",
			"@xmlns:basic": "http://adr.apple.com/types/basic", 
			"@xmlns:base": "http://adr.apple.com/types/base", 
			 	"soap:Body": {
			 		"cap-rr:CreateDiagnosticHeaderResponse": {
			 			"@xmlns:cap-rr": "http://adr.apple.com/types/capture", 
			 			"diagnosticEventNumber": diagnostic_event_number, 
			 			"diagnosticEntryTimeStamp": soap_date(), #"NaN-undefined-NaN aN:aN:aN", 
			 			"opCode": opcode_create()}}}}
	soaped = xmltodict.unparse(response)
	return soaped, diagnostic_event_number

def generate_UploadDiagnosticTestLogResponse():
	response = {
		"soap:Envelope": {
			"@xmlns:soap": "http://schemas.xmlsoap.org/soap/envelope/", 
			"@xmlns:tns": "http://adr.apple.com/services/capture", 
			"@xmlns:wsu": "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd", 
			"@xmlns:global-rr": "http://adr.apple.com/types/global", 
			"@xmlns:cap-rr": "http://adr.apple.com/types/capture", 
			"@xmlns:basic": "http://adr.apple.com/types/basic", 
			"@xmlns:base": "http://adr.apple.com/types/base", 
				"soap:Body": {
					"cap-rr:UploadDiagnosticTestLogResponse": {
						"@xmlns:cap-rr": "http://adr.apple.com/types/capture", 
						"opCode": opcode_create()}}}}
	soaped = xmltodict.unparse(response)
	return soaped

def generate_UploadDiagnosticProfileResponse():
	response = {
		"soap:Envelope": {
			"@xmlns:soap": "http://schemas.xmlsoap.org/soap/envelope/", 
			"@xmlns:tns": "http://adr.apple.com/services/capture", 
			"@xmlns:wsu": "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd", 
			"@xmlns:global-rr": "http://adr.apple.com/types/global", 
			"@xmlns:cap-rr": "http://adr.apple.com/types/capture", 
			"@xmlns:basic": "http://adr.apple.com/types/basic", 
			"@xmlns:base": "http://adr.apple.com/types/base", 
				"soap:Body": {
					"cap-rr:UploadDiagnosticProfileResponse": {
						"@xmlns:cap-rr": "http://adr.apple.com/types/capture", 
						"opCode": opcode_create()}}}}
	soaped = xmltodict.unparse(response)
	return soaped

def generate_CreateDiagnosticTestResultResponse():
	response = {
		"soap:Envelope": {
			"@xmlns:soap": "http://schemas.xmlsoap.org/soap/envelope/", 
			"@xmlns:tns": "http://adr.apple.com/services/capture", 
			"@xmlns:wsu": "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd", 
			"@xmlns:global-rr": "http://adr.apple.com/types/global", 
			"@xmlns:cap-rr": "http://adr.apple.com/types/capture", 
			"@xmlns:basic": "http://adr.apple.com/types/basic", 
			"@xmlns:base": "http://adr.apple.com/types/base", 
				"soap:Body": {
					"cap-rr:CreateDiagnosticTestResultResponse": {
						"@xmlns:cap-rr": "http://adr.apple.com/types/capture", 
						"opCode": opcode_create()}}}}
	soaped = xmltodict.unparse(response)
	return soaped

def generate_SetDiagnosticEventEndIndicatorResponse():
	response = {
		"soap:Envelope": {
			"@xmlns:soap": "http://schemas.xmlsoap.org/soap/envelope/", 
			"@xmlns:tns": "http://adr.apple.com/services/capture", 
			"@xmlns:wsu": "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd", 
			"@xmlns:global-rr": "http://adr.apple.com/types/global", 
			"@xmlns:cap-rr": "http://adr.apple.com/types/capture", 
			"@xmlns:basic": "http://adr.apple.com/types/basic", 
			"@xmlns:base": "http://adr.apple.com/types/base", 
				"soap:Body": {
					"cap-rr:SetDiagnosticEventEndIndicatorResponse": {
						"@xmlns:cap-rr": "http://adr.apple.com/types/capture", 
						"opCode": opcode_create()}}}}
	soaped = xmltodict.unparse(response)
	return soaped

def generate_error_ADR20010():
	response = {
		"soap:Envelope": {
			"@xmlns:soap": "http://schemas.xmlsoap.org/soap/envelope/", 
			"@xmlns:tns": "http://adr.apple.com/services/capture", 
			"@xmlns:wsu": "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd", 
			"@xmlns:global-rr": "http://adr.apple.com/types/global", 
			"@xmlns:cap-rr": "http://adr.apple.com/types/capture", 
			"@xmlns:basic": "http://adr.apple.com/types/basic", 
			"@xmlns:base": "http://adr.apple.com/types/base", 
				"soap:Body": {
					"soap:Fault": {
						"faultcode": "ADR-20010", 
						"faultstring": "Invalid/Empty Session Token.", 
							"detail": {
								"operation-id": opcode_create()}}}}}
	soaped = xmltodict.unparse(response)
	return soaped

def generate_error_DS10001():
	response = {
		"soap:Envelope": {
			"@xmlns:soap": "http://schemas.xmlsoap.org/soap/envelope/", 
			"@xmlns:tns": "http://adr.apple.com/services/capture", 
			"@xmlns:wsu": "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd", 
			"@xmlns:global-rr": "http://adr.apple.com/types/global", 
			"@xmlns:cap-rr": "http://adr.apple.com/types/capture", 
			"@xmlns:basic": "http://adr.apple.com/types/basic", 
			"@xmlns:base": "http://adr.apple.com/types/base", 
				"soap:Body": {
					"soap:Fault": {
						"faultcode": "DS-10001", 
						"faultstring": "Invalid User ID/Password.", 
							"detail": {
								"operation-id": opcode_create()}}}}}
	soaped = xmltodict.unparse(response)
	return soaped

def generate_error_FUA10001():
	response = {
		"soap:Envelope": {
			"@xmlns:soap": "http://schemas.xmlsoap.org/soap/envelope/", 
			"@xmlns:tns": "http://adr.apple.com/services/capture", 
			"@xmlns:wsu": "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd", 
			"@xmlns:global-rr": "http://adr.apple.com/types/global", 
			"@xmlns:cap-rr": "http://adr.apple.com/types/capture", 
			"@xmlns:basic": "http://adr.apple.com/types/basic", 
			"@xmlns:base": "http://adr.apple.com/types/base", 
				"soap:Body": {
					"soap:Fault": {
						"faultcode": "FUA-10001", 
						"faultstring": "A server error occurred whilst authenticating. Please contact support.", 
							"detail": {
								"operation-id": opcode_create()}}}}}
	soaped = xmltodict.unparse(response)
	return soaped

def generate_error_FUA10002():
	response = {
		"soap:Envelope": {
			"@xmlns:soap": "http://schemas.xmlsoap.org/soap/envelope/", 
			"@xmlns:tns": "http://adr.apple.com/services/capture", 
			"@xmlns:wsu": "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd", 
			"@xmlns:global-rr": "http://adr.apple.com/types/global", 
			"@xmlns:cap-rr": "http://adr.apple.com/types/capture", 
			"@xmlns:basic": "http://adr.apple.com/types/basic", 
			"@xmlns:base": "http://adr.apple.com/types/base", 
				"soap:Body": {
					"soap:Fault": {
						"faultcode": "FUA-10002", 
						"faultstring": "A server error occurred. Please contact support.", 
							"detail": {
								"operation-id": opcode_create()}}}}}
	soaped = xmltodict.unparse(response)
	return soaped

# Routes:

# http://localhost:5000/ - this will be the login page, we need to use both GET and POST requests
@app.route('/', methods=['GET', 'POST'])
def login():
	# Output message if something goes wrong...
	msg = ''
	# Check if "email" and "password" POST requests exist (user submitted form)
	if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
		# Create variables for easy access
		email = request.form['email']
		password = request.form['password']
		# Check if account exists using MySQL
		# Fetch account and return result
		cursor.execute('SELECT * FROM users_accounts WHERE user_email = %(user_email)s', { 'user_email': email })
		account = cursor.fetchone()

		# Password verification
		stored_pass = account[7]
		verification = verify_password(stored_pass, password)
		# need to create verification for account id / store #

		
		# If account exists in accounts table in out database
		if account and verification == True:
			# Create session data, we can access this data in other routes
			session['loggedin'] = True
			session['id'] = account[1] #1 = user_uuid column
			session['email'] = account[4] #4 = user_email column
			# Redirect to home page
			return redirect(url_for('home'))
		else:
			# Account doesnt exist or email/password incorrect
			msg = 'Incorrect email/password!'
	# Show the login form with message (if any)
	return render_template('index.html', msg=msg)

# http://localhost:5000/logout - this will be the logout page
@app.route('/logout')
def logout():
	# Remove session data, this will log the user out
	session.pop('loggedin', None)
	session.pop('id', None)
	session.pop('email', None)
	# Redirect to login page
	return redirect(url_for('login'))

# http://localhost:5000/register - this will be the registration page, we need to use both GET and POST requests
@app.route('/register', methods=['GET', 'POST'])
def register():
	# Output message if something goes wrong...
	msg = ''
	# Check if "email", "password" and "email" POST requests exist (user submitted form)
	if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
		# Create variables for easy access
		email = request.form['email']
		#username = request.form['username']
		password = request.form['password']
		# Check if account exists using MySQL
		cursor.execute('SELECT * FROM users_accounts WHERE user_email = %(user_email)s', { 'user_email': email })
		account = cursor.fetchone()
		# If account exists show error and validation checks
		if account:
			msg = 'Account already exists!'
		elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
			msg = 'Invalid email address!'
		#elif not re.match(r'[A-Za-z0-9]+', username):
			#msg = 'Username must contain only characters and numbers!'
		elif not password or not email:
			msg = 'Please fill out the form!'
		else:
			# Create Account Variables
			user_uuid = str(uuid.uuid4())
			user_organizational_uuid = str(uuid.uuid4())
			store_num = store_num_create()
			unix_time = unix_timestamp()
			password_hash = hash_password(password)
			# Account doesnt exists and the form data is valid, now insert new account into accounts table
			cursor.execute('INSERT INTO users_accounts VALUES (NULL, %s, NULL, NULL, %s, NULL, NULL, %s, %s, %s, NULL, NULL, %s, NULL)', (user_uuid, email, password_hash, store_num, user_organizational_uuid, unix_time))
			db.commit()
			msg = 'You have successfully registered!'
	elif request.method == 'POST':
		# Form is empty... (no POST data)
		msg = 'Please fill out the form!'
	# Show registration form with message (if any)
	return render_template('register.html', msg=msg)

# http://localhost:5000/home - this will be the home page, only accessible for loggedin users
@app.route('/home')
def home():
	# Check if user is loggedin
	if 'loggedin' in session:
		cursor.execute('SELECT * FROM users_diagnostics_headers WHERE user_uuid = %s ORDER BY created_at DESC', [session['id']])
		account = cursor.fetchall()
		# User is loggedin show them the home page
		return render_template('home.html', email=session['email'], data=account)
	# User is not loggedin redirect to login page
	return redirect(url_for('login'))

# http://localhost:5000/<path:urlpath> - route to be able to view test results and log files
@app.route('/<path:urlpath>')
def viewlog(urlpath):
	location = urlpath
	file_type = location[-4:]
	
	# detect file types
	# detect if json
	if file_type == 'json':
		print('Accessing: '+location)
		page = 'plog.html'
		with open('templates/'+location,"r") as log:
			file = log.read()
			log.close()

		formatted = json.loads(file)

	# detect if text
	elif file_type == '.txt':
		print('Accessing: '+location)
		page = 'flog.html'
		with open('templates/'+location,"r") as log:
			file = log.read()
			log.close()

		formatted = file

	# detect if None
	elif file_type == 'None':
		print('Resource unavailable')
		page = 'unavailable.html'
		formatted = ''

	# detect if not file and looking for test results
	else:
		print('Accessing test results for diagnostic event number: '+location)
		page = 'details.html'
		cursor.execute('SELECT * FROM users_diagnostics_results WHERE diagnostic_event_number = %(diagnostic_event_number)s', { 'diagnostic_event_number': location })
		account = cursor.fetchall()
		formatted = account

	return render_template(page, urlpath = urlpath, file=formatted)

# http://localhost:5000/profile - this will be the profile page, only accessible for loggedin users
@app.route('/profile')
def profile():
	# Check if user is loggedin
	if 'loggedin' in session:
		# We need all the account info for the user so we can display it on the profile page
		cursor.execute('SELECT * FROM users_accounts WHERE user_uuid = %s', [session['id']])
		account = cursor.fetchone()
		# Show the profile page with account info
		return render_template('profile.html', account=account)
	# User is not loggedin redirect to login page
	return redirect(url_for('login'))

@app.route('/ast-version.txt', methods=['GET', 'POST'])
def parse_request_ast_ver():
	print('Sending AST Version')
	return render_template('ast-version.txt')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/services/ws/capture', methods=['GET', 'POST'])
def parse_request_services():
	data = request.data
	parsed = xmltodict.parse(data)

	key0 = 'm:ActivateUser'
	if key0 in parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']:
		email = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:ActivateUser']['ActivateUserRequest']['appleUserID']
		accountID = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:ActivateUser']['ActivateUserRequest']['accountID']
		shipTo = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:ActivateUser']['ActivateUserRequest']['shipTo']
		adrSecurityKey = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:ActivateUser']['ActivateUserRequest']['adrSecurityKey']
		print('Activation request from ', email)
		password = adrSecurityKey[20:]
		verify, user_uuid = verify_credentials(email, accountID, password)
		if verify == True:
			soaped = generate_ActivateResponse()
			return soaped
		else:
			print('Error: FUA-10002, A server error occurred. Please contact support')
			soaped = generate_error_FUA10002()
			return soaped

	key1 = 'm:Authenticate'
	if key1 in parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']:
		email = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:Authenticate']['AuthenticateRequest']['appleUserID']
		password = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:Authenticate']['AuthenticateRequest']['password']
		accountID = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:Authenticate']['AuthenticateRequest']['accountID']
		shipTo = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:Authenticate']['AuthenticateRequest']['shipTo']
		adrSecurityKey = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:Authenticate']['AuthenticateRequest']['adrSecurityKey']
		print('Authentication request from ', email)
		verify, user_uuid = verify_credentials(email, accountID, password)

		if verify == True:
			# Check to see if valid token exists, if not create one
			cursor.execute('SELECT * FROM users_tokens WHERE user_uuid = %(user_uuid)s', { 'user_uuid': user_uuid })
			check_token = cursor.fetchone()
			
			if check_token != None:
				check_expiration = check_token[3]

				# if exists and expired, create new token
				if check_expiration < unix_timestamp():
					sess_token = generate_mysql_session_token(user_uuid)
					soaped = generate_AuthenticateResponse(sess_token)
					return soaped
				# if exists and still valid, use existing token
				else:
					get_valid_token = check_token[2]
					soaped = generate_AuthenticateResponse(get_valid_token)
					return soaped
			else: # if nothing exists, create new token
				sess_token = generate_mysql_session_token(user_uuid)
				soaped = generate_AuthenticateResponse(sess_token)
				return soaped

		elif verify == False:
			print('Error: DS-10001, Invalid User ID/Password')
			soaped = generate_error_DS10001()
			return soaped

		else:
			print('Error: FUA-10001, A server error occurred whilst authenticating')
			soaped = generate_error_FUA10001()
			return soaped

	key2 = 'm:DiagnosticHeartBeat'
	if key2 in parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']:
		sessionToken = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:DiagnosticHeartBeat']['DiagnosticHeartBeatRequest']['userSession']['userSessionToken']
		print('Diagnostic HeartBeat')
		verify, existing_token = verify_session_token(sessionToken)

		if verify == True:
			# Check to see if valid token exists, if not create one
			cursor.execute('SELECT * FROM users_tokens WHERE user_session_token = %(user_session_token)s', { 'user_session_token': existing_token })
			check_token = cursor.fetchone()
			
			if check_token != None:
				check_expiration = check_token[3]

				# if exists and expired, kick user to reauthenticate
				if check_expiration < unix_timestamp():
					print('Error: ADR-20010, Session token has expired.')
					soaped = generate_error_ADR20010()
					return soaped
				# if exists and still valid, use existing token
				else:
					soaped = generate_DiagnosticHeartBeatResponse()
					return soaped

		elif verify == False:
			print('Error: ADR-20010, Invalid/Empty Session Token.')
			soaped = generate_error_ADR20010()
			return soaped

		else:
			print('Error: FUA-10002, A server error occurred. Please contact support')
			soaped = generate_error_FUA10002()
			return soaped

	key3 = 'm:CreateDiagnosticHeader'
	if key3 in parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']:
		sessionToken = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:CreateDiagnosticHeader']['CreateDiagnosticHeaderRequest']['userSession']['userSessionToken']
		toolID = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:CreateDiagnosticHeader']['CreateDiagnosticHeaderRequest']['diagnosticHeaderRequestData']['toolID']
		toolVersion = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:CreateDiagnosticHeader']['CreateDiagnosticHeaderRequest']['diagnosticHeaderRequestData']['toolVersion']
		diagnosticStartTimeStamp = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:CreateDiagnosticHeader']['CreateDiagnosticHeaderRequest']['diagnosticHeaderRequestData']['diagnosticStartTimeStamp']
		serialNumber = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:CreateDiagnosticHeader']['CreateDiagnosticHeaderRequest']['diagnosticHeaderRequestData']['serialNumber']
		imeiNumber = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:CreateDiagnosticHeader']['CreateDiagnosticHeaderRequest']['diagnosticHeaderRequestData']['imeiNumber']
		serverID = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:CreateDiagnosticHeader']['CreateDiagnosticHeaderRequest']['diagnosticHeaderRequestData']['serverID']
		networkID = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:CreateDiagnosticHeader']['CreateDiagnosticHeaderRequest']['diagnosticHeaderRequestData']['networkID']
		channelID = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:CreateDiagnosticHeader']['CreateDiagnosticHeaderRequest']['diagnosticHeaderRequestData']['channelID']
		print('Diagnostic Header Request')
		
		verify, user_uuid, existing_token = verify_credentials_for_diagnostics(sessionToken)
		converted_diag_start_time = string_date_to_unix_timestamp(diagnosticStartTimeStamp)
		if verify == True:
			# Check to see if valid token exists, if not create one
			cursor.execute('SELECT * FROM users_tokens WHERE user_session_token = %(user_session_token)s', { 'user_session_token': existing_token })
			check_token = cursor.fetchone()
			#user_uuid = check_token[1]
			
			if check_token != None:
				check_expiration = check_token[3]

				# if exists and expired, kick user to reauthenticate
				if check_expiration < unix_timestamp():
					print('Error: ADR-20010, Session token has expired.')
					soaped = generate_error_ADR20010()
					return soaped
				# if exists and still valid, create diagnostic header
				else:
					created_at = unix_timestamp() # id, user_uuid, event_num, tool_id,  tool_version, diag_start_timestamp, diag_end_timestamp, serial, server_id, account_id, profile_file, log_file, test_result, pass_count, created_at, deleted_at tech_notes
					soaped, diagnostic_event_number = generate_CreateDiagnosticHeaderResponse()
					cursor.execute('INSERT INTO users_diagnostics_headers VALUES (NULL, %s, %s, %s, %s, %s, NULL, %s, %s, %s, NULL, NULL, NULL, NULL, %s, NULL, NUll)', (user_uuid, diagnostic_event_number, toolID, toolVersion, converted_diag_start_time, serialNumber, serverID, networkID, created_at))
					db.commit()
					return soaped

		elif verify == False:
			print('Error: ADR-20010, Invalid/Empty Session Token.')
			soaped = generate_error_ADR20010()
			return soaped

		else:
			print('Error: FUA-10002, A server error occurred. Please contact support')
			soaped = generate_error_FUA10002()
			return soaped		

	key4 = 'm:UploadDiagnosticTestLog'
	if key4 in parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']:
		sessionToken = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:UploadDiagnosticTestLog']['UploadDiagnosticTestLogRequest']['userSession']['userSessionToken']
		diagnosticEventNumber = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:UploadDiagnosticTestLog']['UploadDiagnosticTestLogRequest']['testLogUploadRequestData']['diagnosticEventNumber']
		fileName = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:UploadDiagnosticTestLog']['UploadDiagnosticTestLogRequest']['testLogUploadRequestData']['fileName']
		fileData = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:UploadDiagnosticTestLog']['UploadDiagnosticTestLogRequest']['testLogUploadRequestData']['fileData']
		print('Uploading Diagnostic Test Log')

		verify, user_uuid, existing_token = verify_credentials_for_diagnostics(sessionToken)
		verify_diag_num, existing_diag_num = verify_diagnosticEventNumber(diagnosticEventNumber)
		#converted_diag_start_time = string_date_to_unix_timestamp(diagnosticStartTimeStamp)
		if verify == True:
			# Check to see if valid token exists, if not create one
			cursor.execute('SELECT * FROM users_tokens WHERE user_session_token = %(user_session_token)s', { 'user_session_token': existing_token })
			check_token = cursor.fetchone()
			
			if check_token != None:
				check_expiration = check_token[3]

				# if exists and expired, kick user to reauthenticate
				if check_expiration < unix_timestamp():
					print('Error: ADR-20010, Session token has expired.')
					soaped = generate_error_ADR20010()
					return soaped
				# if exists and still valid, create diagnostic test log file
				elif verify_diag_num == True and check_expiration > unix_timestamp():
					path = "logs/full/"+diagnosticEventNumber+".txt"
					cursor.execute('UPDATE users_diagnostics_headers SET log_file = %s WHERE diagnostic_event_number = %s',(path, diagnosticEventNumber))
					db.commit()

					decoded = base64.b64decode(fileData).decode('utf8')
					with open('templates/'+path,"w+") as log:
						#log.write(str(decoded))
						log.write(decoded)

					soaped = generate_UploadDiagnosticTestLogResponse()
					return soaped
				else:
					print('Error: FUA-10002, A server error occurred. Please contact support')
					soaped = generate_error_FUA10002()
					return soaped

		elif verify == False:
			print('Error: ADR-20010, Invalid/Empty Session Token.')
			soaped = generate_error_ADR20010()
			return soaped

		else:
			print('Error: FUA-10002, A server error occurred. Please contact support')
			soaped = generate_error_FUA10002()
			return soaped

	key5 = 'm:UploadDiagnosticProfile'
	if key5 in parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']:
		sessionToken = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:UploadDiagnosticProfile']['UploadDiagnosticProfileRequest']['userSession']['userSessionToken']
		diagnosticEventNumber = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:UploadDiagnosticProfile']['UploadDiagnosticProfileRequest']['profileUploadRequestData']['diagnosticEventNumber']
		fileName = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:UploadDiagnosticProfile']['UploadDiagnosticProfileRequest']['profileUploadRequestData']['fileName']
		fileData = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:UploadDiagnosticProfile']['UploadDiagnosticProfileRequest']['profileUploadRequestData']['fileData']
		print('Uploading Diagnostic Profile')
		
		verify, user_uuid, existing_token = verify_credentials_for_diagnostics(sessionToken)
		verify_diag_num, existing_diag_num = verify_diagnosticEventNumber(diagnosticEventNumber)
		#converted_diag_start_time = string_date_to_unix_timestamp(diagnosticStartTimeStamp)
		if verify == True:
			# Check to see if valid token exists, if not create one
			cursor.execute('SELECT * FROM users_tokens WHERE user_session_token = %(user_session_token)s', { 'user_session_token': existing_token })
			check_token = cursor.fetchone()
			
			if check_token != None:
				check_expiration = check_token[3]

				# if exists and expired, kick user to reauthenticate
				if check_expiration < unix_timestamp():
					print('Error: ADR-20010, Session token has expired.')
					soaped = generate_error_ADR20010()
					return soaped
				# if exists and still valid, create diagnostic header
				elif verify_diag_num == True and check_expiration > unix_timestamp():
					path = "logs/profile/"+diagnosticEventNumber+".json"
					cursor.execute('UPDATE users_diagnostics_headers SET profile_file = %s WHERE diagnostic_event_number = %s',(path, diagnosticEventNumber))
					db.commit()

					decoded = base64.b64decode(fileData).decode('utf8')
					sub1 = '<?xml version="1.0" encoding="UTF-8"?>'
					sub2 = '</plist>'
					substring = find_text(decoded, sub1, sub2)
					#remove_footer = decoded[0:-91] - only worked for specific cases

					#write decoded log to file
					with open('templates/'+path,"w+") as log:
						log.write(substring)
						log.close()

					#open log to perform plist parsing - would be able to skip multiple write / load if could parse from string
					with open('templates/'+path, 'rb') as fp:
						pl = plistlib.load(fp)
					
					dump = json.dumps(pl)

					# rewrite newly parsed and json formated log
					with open('templates/'+path,"w+") as log2:
						#log.write(str(base64_converted))
						log2.write(dump)
						log2.close()
						

					soaped = generate_UploadDiagnosticProfileResponse()
					return soaped
				else:
					print('Error: FUA-10002, A server error occurred. Please contact support')
					soaped = generate_error_FUA10002()
					return soaped

		elif verify == False:
			print('Error: ADR-20010, Invalid/Empty Session Token.')
			soaped = generate_error_ADR20010()
			return soaped

		else:
			print('Error: FUA-10002, A server error occurred. Please contact support')
			soaped = generate_error_FUA10002()
			return soaped

	key6 = 'm:CreateDiagnosticTestResult'
	if key6 in parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']:
		sessionToken = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:CreateDiagnosticTestResult']['CreateDiagnosticTestResultRequest']['userSession']['userSessionToken']
		diagnosticEventNumber = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:CreateDiagnosticTestResult']['CreateDiagnosticTestResultRequest']['diagnosticTestResultRequestData']['diagnosticEventNumber']
		moduleName = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:CreateDiagnosticTestResult']['CreateDiagnosticTestResultRequest']['diagnosticTestResultRequestData']['moduleName']
		moduleLocation = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:CreateDiagnosticTestResult']['CreateDiagnosticTestResultRequest']['diagnosticTestResultRequestData']['moduleLocation']
		moduleSerialNumber = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:CreateDiagnosticTestResult']['CreateDiagnosticTestResultRequest']['diagnosticTestResultRequestData']['moduleSerialNumber']
		moduleTestName = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:CreateDiagnosticTestResult']['CreateDiagnosticTestResultRequest']['diagnosticTestResultRequestData']['moduleTestName']
		moduleTestNumber = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:CreateDiagnosticTestResult']['CreateDiagnosticTestResultRequest']['diagnosticTestResultRequestData']['moduleTestNumber']
		moduleTestResult = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:CreateDiagnosticTestResult']['CreateDiagnosticTestResultRequest']['diagnosticTestResultRequestData']['moduleTestResult']
		print('Creating Diagnostic Test Result')
		
		verify, user_uuid, existing_token = verify_credentials_for_diagnostics(sessionToken)
		verify_diag_num, existing_diag_num = verify_diagnosticEventNumber(diagnosticEventNumber)
		#converted_diag_start_time = string_date_to_unix_timestamp(diagnosticStartTimeStamp)
		if verify == True:
			# Check to see if valid token exists, if not create one
			cursor.execute('SELECT * FROM users_tokens WHERE user_session_token = %(user_session_token)s', { 'user_session_token': existing_token })
			check_token = cursor.fetchone()
			
			if check_token != None:
				check_expiration = check_token[3]

				# if exists and expired, kick user to reauthenticate
				if check_expiration < unix_timestamp():
					print('Error: ADR-20010, Session token has expired.')
					soaped = generate_error_ADR20010()
					return soaped
				# if exists and still valid, create diagnostic header
				elif verify_diag_num == True and check_expiration > unix_timestamp():
					created_at = unix_timestamp() # id, user_uuid, diagnostic_event_number, module_name, module_location, module_serial_number, module_test_name, module_test_number, module_test_result, created_at
					soaped = generate_CreateDiagnosticTestResultResponse()
					cursor.execute('INSERT INTO users_diagnostics_results VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, NULL)', (user_uuid, diagnosticEventNumber, moduleName, moduleLocation, moduleSerialNumber, moduleTestName, moduleTestNumber, moduleTestResult, created_at))
					db.commit()
					return soaped

		elif verify == False:
			print('Error: ADR-20010, Invalid/Empty Session Token.')
			soaped = generate_error_ADR20010()
			return soaped

		else:
			print('Error: FUA-10002, A server error occurred. Please contact support')
			soaped = generate_error_FUA10002()
			return soaped

	key7 = 'm:SetDiagnosticEventEndIndicator'
	if key7 in parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']:
		sessionToken = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:SetDiagnosticEventEndIndicator']['DiagnosticEventEndIndicatorRequest']['userSession']['userSessionToken']
		diagnosticEventNumber = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:SetDiagnosticEventEndIndicator']['DiagnosticEventEndIndicatorRequest']['eventEndIndicatorRequestData']['diagnosticEventNumber']
		diagnosticEndTimeStamp = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:SetDiagnosticEventEndIndicator']['DiagnosticEventEndIndicatorRequest']['eventEndIndicatorRequestData']['diagnosticEndTimeStamp']
		diagnosticTestEndResult = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:SetDiagnosticEventEndIndicator']['DiagnosticEventEndIndicatorRequest']['eventEndIndicatorRequestData']['diagnosticTestEndResult']
		diagnosticPassCount = parsed['SOAP-ENV:Envelope']['SOAP-ENV:Body']['m:SetDiagnosticEventEndIndicator']['DiagnosticEventEndIndicatorRequest']['eventEndIndicatorRequestData']['diagnosticPassCount']
		print('Setting Diagnostic Event End Indicator')
		
		verify, user_uuid, existing_token = verify_credentials_for_diagnostics(sessionToken)
		verify_diag_num, existing_diag_num = verify_diagnosticEventNumber(diagnosticEventNumber)
		converted_diag_end_time = string_date_to_unix_timestamp(diagnosticEndTimeStamp)
		#converted_diag_start_time = string_date_to_unix_timestamp(diagnosticStartTimeStamp)
		if verify == True:
			# Check to see if valid token exists, if not create one
			cursor.execute('SELECT * FROM users_tokens WHERE user_session_token = %(user_session_token)s', { 'user_session_token': existing_token })
			check_token = cursor.fetchone()
			
			if check_token != None:
				check_expiration = check_token[3]

				# if exists and expired, kick user to reauthenticate
				if check_expiration < unix_timestamp():
					print('Error: ADR-20010, Session token has expired.')
					soaped = generate_error_ADR20010()
					return soaped
				# if exists and still valid, update final test results
				elif verify_diag_num == True and check_expiration > unix_timestamp():
					#print('here')
					#cursor.execute('UPDATE users_diagnostics_headers SET diagnostic_end_timestamp = %s WHERE diagnostic_event_number = %s',(converted_diag_end_time, diagnosticEventNumber))
					cursor.execute('UPDATE users_diagnostics_headers SET diagnostic_end_timestamp = %s, test_result = %s, pass_count = %s WHERE diagnostic_event_number = %s',(converted_diag_end_time, diagnosticTestEndResult, diagnosticPassCount, diagnosticEventNumber))
					db.commit()
					soaped = generate_SetDiagnosticEventEndIndicatorResponse()
					return soaped
				else:
					print('Error: FUA-10002, A server error occurred. Please contact support')
					soaped = generate_error_FUA10002()
					return soaped

		elif verify == False:
			print('Error: ADR-20010, Invalid/Empty Session Token.')
			soaped = generate_error_ADR20010()
			return soaped

		else:
			print('Error: FUA-10002, A server error occurred. Please contact support')
			soaped = generate_error_FUA10002()
			return soaped

@app.template_filter('convert')
def unix_timestamp_to_string_date(unix_time):
	converted = datetime.datetime.fromtimestamp(unix_time).strftime('%d-%b-%y %H:%M:%S')
	return converted

if __name__ == "__main__":
	app.run(debug=True, host='0.0.0.0')
