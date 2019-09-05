#!/usr/bin/env python
from __future__ import print_function
from flask import Flask, render_template, redirect, session, flash, request
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt       

#below lines needed for google calendar API integration
import datetime
from datetime import timedelta
import pickle
import os.path
import re 

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']
calendaridPT = '9n16t54iligakcd64916che4gs@group.calendar.google.com'

#needed for flask
app = Flask(__name__)
app.secret_key = "super secret"
bcrypt = Bcrypt(app)
db='the_black_cat'

#users:id, first name, last name, email, password, created at, updated at
#sessions: id, datetime, session length, user_id, notes
#blogs: id, content, user_id, created at, updated at
#comments: id, content, user_id, blog_id, created_at, updated_at

#allow more special characters in the regex
pw_regex = re.compile(r'^(?=.*[\d])(?=.*[A-Z])(?=.*[a-z])[\w\d]{8,}$')
email_regex = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
@app.route('/')
def index():
  return render_template('homepage.html')

@app.route('/login-register')
def registration_page():
  return render_template('registration.html')

@app.route('/register',methods=["POST"])
def register():
  mysql = connectToMySQL(db)
  is_valid=True
  #get form info
  fn = request.form['first_name']
  ln = request.form['last_name']
  pw = request.form['password']
  cpw = request.form['confirm_password']
  email = request.form['email'].lower()

  if len(fn)<1:
    flash('First Name must be filled in.')
    is_valid = False
  if len(ln)<1:
    flash('Last Name must be filled in.')
    is_valid = False
  if is_valid == True:
    query = "SELECT * from users where email = lower(%(email)s);"
    q_data = {
      'email':email
    }
    user_info = mysql.query_db(query,q_data)
    if user_info:
      flash('Email already registered. Please login.')
      return redirect('/login-register')
    pw_hash = bcrypt.generate_password_hash(pw)
    flash('Successfully added new user!')
    
    mysql=connectToMySQL(db)
    query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) values (%(fn)s,%(ln)s,%(email)s,%(pw)s,NOW(),NOW());"
    q_data = {
      'fn':fn,
      'ln':ln,
      'email':email,
      'pw':pw_hash
    }
    id = mysql.query_db(query,q_data)
    session['user_email'] = email
    session['first_name'] = fn
    session['id'] = id    
  return redirect('/login-register')

@app.route('/login',methods=["POST"])
def login():
  mysql = connectToMySQL(db)
  is_valid=True
  #get form info
  email = request.form['email'].lower()

  if len(request.form['password'])<1:
    flash('Password cannot be blank.')
    is_valid = False
  if len(email)<1:
    flash('Email cannot be blank.')
    is_valid = False
  if is_valid == True:
    query = "SELECT * from users where email = lower(%(email)s);"
    q_data = {
      'email':email
    }
    user_info = mysql.query_db(query,q_data)
    #print(user_info)
    if not user_info:
      flash('Email does not match a registered user')
      return redirect('/')
    else:#check if password matches
      print(user_info[0])
      if bcrypt.check_password_hash(user_info[0]['password'],request.form['password']) == True:
        print('password matched')
        session['user_email'] = email
        session['first_name'] = user_info[0]['first_name']
        session['id'] = user_info[0]['id']
        return redirect('/')
      else:
        flash('Password or email is incorrect.')
        return redirect('/login-register')
  return redirect('/')

@app.route('/logout')
def logout():
  session.clear()
  return redirect('/')


@app.route('/myaccount/<id>')
def edit(id):
  print(session['id'])
  #don't let someone get to this page if they're not logged in
  if 'id' not in session:
    return redirect('/')
  #don't let someone get to this page if they're trying to get to a different ID
  if int(id) != session['id']:
    return redirect('/')
  mysql = connectToMySQL(db)
  query = "SELECT * from users where id = %(id)s;"
  q_data = { 'id':id}
  data = mysql.query_db(query,q_data)

  #get the client's session lists
  mysql = connectToMySQL(db)
  query = 'SELECT * from sessions where user_id = %(id)s and date_time > NOW() order by date_time;'
  sessions = mysql.query_db(query,q_data)
  print(sessions)
  cancel_date = datetime.datetime.now()+timedelta(hours=1)*24

  return render_template('myaccount.html',id=id,data=data[0],sessions=sessions, cancel_date=cancel_date)

@app.route('/users/<id>/update', methods=["POST"])
def update_user(id):
  mysql = connectToMySQL(db)
  query = "UPDATE users set first_name=%(fn)s, last_name=%(ln)s, email=%(email)s, updated_at=NOW() where id=%(id)s;"
  print(id)
  q_data = {
    'id':id,
    'fn':request.form['first_name'],
    'ln':request.form['last_name'],
    'email':request.form['email']
  }
  mysql.query_db(query,q_data)
  flash('Successfully updated user')
  return redirect('/myaccount/'+str(id))

@app.route('/users/<id>/destroy')
def delete(id):
  mysql = connectToMySQL(db)
  query = "DELETE from users where id=%(id)s;"
  q_data = {'id':id}
  mysql.query_db(query,q_data)
  flash('User deleted')
  session.clear()
  return redirect('/')

@app.route('/blog')
def blog():
  return render_template('blog-simple.html')

@app.route('/personaltraining/calendar')
def schedulesession():
  if 'id' not in session:
    flash('Please login to view the calendar')
    return redirect('/personaltraining/schedulesession/login-register')
  return render_template('schedulesession.html')

@app.route('/personaltraining/schedulesession/login-register')
def schedulesessregistration():
  return render_template('schedulesesslogin.html')

@app.route('/register-schedulesession',methods=["POST"])
def registerpt():
  mysql = connectToMySQL(db)
  is_valid=True
  #get form info
  fn = request.form['first_name']
  ln = request.form['last_name']
  pw = request.form['password']
  cpw = request.form['confirm_password']
  email = request.form['email'].lower()

  if len(fn)<1:
    flash('First Name must be filled in.')
    is_valid = False
  if len(ln)<1:
    flash('Last Name must be filled in.')
    is_valid = False
  if is_valid == True:
    query = "SELECT * from users where email = lower(%(email)s);"
    q_data = {
      'email':email
    }
    user_info = mysql.query_db(query,q_data)
    if user_info:
      flash('Email already registered. Please login.')
      return redirect('/personaltraining/schedulesession/login-register')
    pw_hash = bcrypt.generate_password_hash(pw)
    #flash('Successfully added new user!')
    mysql=connectToMySQL(db)
    query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) values (%(fn)s,%(ln)s,%(email)s,%(pw)s,NOW(),NOW());"
    q_data = {
      'fn':fn,
      'ln':ln,
      'email':email,
      'pw':pw_hash
    }
    id = mysql.query_db(query,q_data)
    session['user_email'] = email
    session['first_name'] = fn
    session['id'] = id    
    return redirect('/personaltraining/calendar')    
  return redirect('/personaltraining/calendar')

@app.route('/login-schedulesession',methods=["POST"])
def loginpt():
  mysql = connectToMySQL(db)
  is_valid=True
  #get form info
  email = request.form['email'].lower()

  if len(request.form['password'])<1:
    flash('Password cannot be blank.')
    is_valid = False
  if len(email)<1:
    flash('Email cannot be blank.')
    is_valid = False
  if is_valid == True:
    query = "SELECT * from users where email = lower(%(email)s);"
    q_data = {
      'email':email
    }
    user_info = mysql.query_db(query,q_data)
    #print(user_info)
    if not user_info:
      flash('Email does not match a registered user')
      return redirect('/personaltraining/schedulesession/login-register')
    else:#check if password matches
      print(user_info[0])
      if bcrypt.check_password_hash(user_info[0]['password'],request.form['password']) == True:
        print('password matched')
        session['user_email'] = email
        session['first_name'] = user_info[0]['first_name']
        session['id'] = user_info[0]['id']
        return redirect('/personaltraining/calendar')
      else:
        flash('Password or email is incorrect.')
        return redirect('/personaltraining/schedulesession/login-register')
  return redirect('/personaltraining/calendar')

def recurring_event(argument):
  switcher = {
    'DAILY': timedelta(days=1),
    'WEEKLY': timedelta(weeks=1)
  }
  return switcher.get(argument)

@app.route('/createevent', methods=['POST'])
def createevent():
  #get form data
  startdate = request.form['date'] #string
  starttime = datetime.datetime.strptime(request.form['time'],'%H:%M') #datetime
  recurrence = request.form['recurrence'] #DAILY or WEEKLY
  duration = request.form['length'] #string
  starttimeTime = starttime.time().strftime('%H:%M') #string
  occurrences = request.form['count'] #an integer from 1 to 20
  
  td = timedelta(hours=1) #datetime.timedelta
  enddatetime = starttime + td * float(duration) #datetime
  notes = request.form['notes']

  startTime = startdate + 'T' + starttimeTime + ':00' #string
  endtime = enddatetime.time().strftime('%H:%M') #string
  endTime = startdate + 'T' + endtime + ':00' #string
  print(startTime,endTime)

  #the following section adds the event to the google calendar
  creds = None
  # The file token.pickle stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists('token.pickle'):
      with open('token.pickle', 'rb') as token:
          creds = pickle.load(token)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
      if creds and creds.expired and creds.refresh_token:
          creds.refresh(Request())
      else:
          flow = InstalledAppFlow.from_client_secrets_file(
              'credentials.json', SCOPES)
          creds = flow.run_local_server(port=0)
      # Save the credentials for the next run
      with open('token.pickle', 'wb') as token:
          pickle.dump(creds, token)

  service = build('calendar', 'v3', credentials=creds)

  # Call the Calendar API
  #now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
  event = {
  'summary': session['first_name']+"'s session with Paul",
  #'location': '800 Howard St., San Francisco, CA 94103',
  #'description': 'A chance to hear more about Google\'s developer products.',
  'start': {
      'dateTime': startTime,
      'timeZone': 'America/Chicago',
  },
  'end': {
      'dateTime': endTime,
      'timeZone': 'America/Chicago',
  },
  'recurrence': [
      'RRULE:FREQ='+recurrence+';COUNT='+occurrences
  ],
  'attendees': [
      {'email': session['user_email']}
  ],
  'reminders': {
      'useDefault': False,
      'overrides': [
      {'method': 'email', 'minutes': 24 * 60},
      {'method': 'popup', 'minutes': 10},
      ],
  },
  }
  event = service.events().insert(calendarId=calendaridPT, body=event).execute()
  print(event)
  print(event['id'])

  #if occurrences is greater than 1, get a date array so you can insert more events
  num_occurrences = int(occurrences)
  if num_occurrences > 1:
    session_list = list(range(num_occurrences)) #initialize the list
    session_list[0] = startdate #set the first element in the list to the start date
    td_occurences = recurring_event(recurrence) #get a timedelta object to add for the recurring events
    #fill the list of recurring sessions
    for i in range(1,len(session_list)):
      #this list converts the session_list[i] to a datetime object, then back to a string
      session_list[i] = (datetime.datetime.strptime(session_list[i-1],'%Y-%m-%d') + td_occurences).strftime('%Y-%m-%d')
    for i in range(len(session_list)):
      recurringStartTime = session_list[i]+'T'+starttimeTime+':00' #string
      mysql = connectToMySQL(db)
      query = "INSERT INTO sessions (google_event_id,date_time, session_length, user_id, notes, created_at, updated_at) values (%(eventId)s,%(startTime)s,%(duration)s,%(id)s,%(notes)s,NOW(),NOW());"
      q_data = {
        'eventId':event['id'],
        'startTime':recurringStartTime,
        'duration':float(duration)*60,
        'id':session['id'],
        'notes':notes
      }  
      session_id = mysql.query_db(query,q_data)    
  else:
    mysql = connectToMySQL(db)
    query = "INSERT INTO sessions (google_event_id,date_time, session_length, user_id, notes, created_at, updated_at) values (%(eventId)s,%(startTime)s,%(duration)s,%(id)s,%(notes)s,NOW(),NOW());"
    q_data = {
      'eventId':event['id'],
      'startTime':startTime,
      'duration':float(duration)*60,
      'id':session['id'],
      'notes':notes
    }  
    session_id = mysql.query_db(query,q_data)

  return redirect('/personaltraining/calendar')

@app.route('/delete_session/<id>', methods =['POST'])
def delete_session(id):
  mysql = connectToMySQL(db)
  query = "DELETE from sessions where id = %(id)s;"
  q_data = {'id':id}
  mysql.query_db(query,q_data)
  flash('Session deleted. Contact Paul to remove from his calendar.')
  return redirect('/myaccount/'+str(session['id']))

@app.route('/reschedule_session/<id>')
def reschedule_template(id):
  mysql = connectToMySQL(db)
  query = "SELECT * from sessions where id = %(id)s;"
  q_data = {'id':id}
  session_data = mysql.query_db(query,q_data)
  session_data = session_data[0]
  session_data['date'] = session_data['date_time'].strftime('%Y-%m-%d')
  session_data['time'] = session_data['date_time'].strftime('%H:%M')
  print(session_data)

  #get the client's session lists
  mysql = connectToMySQL(db)
  query = 'SELECT * from sessions where user_id = %(id)s and date_time > NOW() order by date_time;'
  q_data = {'id':session['id']}
  sessions = mysql.query_db(query,q_data)
  cancel_date = datetime.datetime.now()+timedelta(hours=1)*24
  return render_template('reschedule_session.html',session_data = session_data, sessions=sessions, cancel_date = cancel_date)

@app.route('/reschedule_session/<id>/update', methods=["POST"])
def reschedule_session(id):
  #get form data
  print(request.form)
  startdate = request.form['date'] #string
  starttime = datetime.datetime.strptime(request.form['time'],'%H:%M') #datetime
  #recurrence = request.form['recurrence'] #DAILY or WEEKLY
  duration = request.form['length'] #string
  notes = request.form['notes']
  
  starttimeTime = starttime.time().strftime('%H:%M') #string
  #occurrences = request.form['count'] #an integer from 1 to 20
  
  td = timedelta(hours=1) #datetime.timedelta
  enddatetime = starttime + td * float(duration) #datetime
  
  startTime = startdate + 'T' + starttimeTime + ':00' #string
  endtime = enddatetime.time().strftime('%H:%M') #string
  endTime = startdate + 'T' + endtime + ':00' #string
  print(startTime,endTime)

  mysql = connectToMySQL(db)
  query = "UPDATE sessions set date_time = %(startTime)s, session_length = %(duration)s, notes = %(notes)s, updated_at = NOW() where id = %(id)s;"
  q_data = {
    'startTime':startTime,
    'duration':float(duration)*60,
    'notes':notes,
    'id':id
  }  
  mysql.query_db(query,q_data)
  return redirect('/myaccount/'+str(session['id']))

if __name__ == "__main__":
  app.run(debug=True)