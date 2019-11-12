#!/usr/bin/env python1.7

"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver

To run locally:

    python server.py

Go to http://localhost:8111 in your browser.

A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.sql import text
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response
import datetime

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


DATABASEURI = "postgresql://yw3241:7276@34.74.165.156/proj1part2"

engine = create_engine(DATABASEURI)

@app.before_request
def before_request():
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  try:
    g.conn.close()
  except Exception as e:
    pass

# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
@app.route('/', defaults={'time_constraint': None})
@app.route('/<int:time_constraint>')
def index(time_constraint):
  """
  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2
  """

  print request.args

  cursor = g.conn.execute("select * from events order by start_time desc;")
  events = []
  formatter = '%Y-%m-%d %H:%M:%S'
  for result in cursor:
    if (not time_constraint or abs((datetime.datetime.now() - result['start_time']).days) < time_constraint):
      event = dict(result)
      event['outdated'] = str(event['start_time'] < datetime.datetime.now())
      events.append(event)
  cursor.close()
  
  fields = list(g.conn.execute("select distinct field from events"))
  context = dict(events = events, fields = fields)
  return render_template("index.html", **context)

# don't remove the trailing '/' for the first url; VERY IMPORTANT!
@app.route('/apply/<pid>/', defaults={"error":''})
@app.route('/apply/<pid>/<error>')
def apply(pid, error):
  name = next(g.conn.execute(text("select name from prof_opps where pid = :pid;"), pid=int(pid)))['name']
  fields = list(g.conn.execute("select distinct field from students;"))
  return render_template("apply.html", error=error, fields=fields, pid=pid, name=name)

@app.route('/apply-add', methods=['POST'])
def apply_add():
  pid = request.form['pid']
  name = request.form['name'] 
  if (name == ''):
    return redirect('/apply/%d/%s' % (int(pid), "name cannot be null!"))

  field = request.form['field'] 
  year = request.form['year']
  uni = request.form['uni']
  if (uni == ''): 
    return redirect('/apply/%d/%s' % (int(pid), "uni cannot be null!"))
  phone = request.form['phone']

  # insert the student if not exist
  s = text("INSERT INTO students(uni, name, phone, field, year) select :uni, :name, :phone, :field, :year where not exists ( select * from students where uni = :uni);") 
  g.conn.execute(s, uni=uni, name=name, phone=phone, field=field, year=year)

  # insert into applies_to
  # TODO: error checking
  g.conn.execute(text('INSERT INTO applies_to(uni, pid, time) VALUES (:uni, :pid, date_trunc(\'second\', now())::timestamp);'), uni=uni, pid=int(pid))
  return redirect('/')

@app.route('/rsvp/<eid>/', defaults={"error":''})
@app.route('/rsvp/<eid>/<error>')
def rsvp(eid, error):
  fields = list(g.conn.execute("select distinct field from events"))
  name = g.conn.execute(text("select name from events where eid = :eid"), eid=int(eid)) 
  return render_template("rsvp.html", error=error, eid=eid, name=next(name)['name'], fields=fields)


# Example of adding new data to the database
@app.route('/rsvp-add', methods=['POST'])
def rsvp_add():

  eid = request.form['eid']
  name = request.form['name']
  if (name == ''):
    return redirect('/rsvp/%d/%s' % (int(eid), "name cannot be null!"))
  field = request.form['field'] 

  # when the person is a student
  if (request.form['identity'].strip() == 'student'):
    year = request.form['year'] 
    uni = request.form['uni']
    if (uni == ''): 
      return redirect('/rsvp/%d/%s' % (int(eid), "uni cannot be null!"))
    phone = request.form['phone']
    
    # insert student if not exists
    g.conn.execute(text('INSERT INTO students(uni, name, phone, field, year) select :uni, :name, :phone, :field, :year where not exists ( select * from students where uni = :uni);'), uni=uni, name=name, phone=phone, field=field, year=year)

    # insert into RSVP AFTER ERROR CHECKING
    # TODO: error checking
    g.conn.execute(text('INSERT INTO rsvp_student(uni, eid, time) VALUES (:uni, :eid, date_trunc(\'second\', now())::timestamp);'), uni=uni, eid=int(eid)) 

  # when the person is a recruiter
  elif (request.form['identity'].strip() == 'recruiter'):
    company = request.form['company']
    position = request.form['position']
    
    # insert recruiter if not exists
    g.conn.execute(text('INSERT INTO recruiters(name, field, company, position) select :name, :field, :company, :position where not exists ( select * from recruiters where name = :name and company = :company);'), name=name, field=field, company=company, position=position)
  
    # insert into RSVP AFTER ERROR CHECKING
    # TODO: error checking
    rid = g.conn.execute(text('select rid from recruiters where name = :name and company = :company;'), name=name, company=company).fetchone()['rid']
    g.conn.execute(text('INSERT INTO rsvp_recruiter(rid, eid, time) VALUES (:rid, :eid, now()::timestamp);'), rid=int(rid), eid=int(eid))       
  
  else:
    return redirect('/rsvp/%d/%s' % (int(eid), "Please choose either of the two identities!"))
 
  return redirect('/')


@app.route('/event/<eid>')
def event(eid):
  info = g.conn.execute(text('select * from events where eid = :eid;'), eid=int(eid)).fetchone()
  venue = g.conn.execute(text('select name, address from venues where vid = :vid;'), vid=info['vid']).fetchone()
  host = g.conn.execute(text('select o.name from organizations o join hosts h on o.oid = h.oid where h.eid = :eid;'), eid=int(eid)).fetchone()['name']
  
  # querying the rsvped students and recruiters
  cursor = g.conn.execute(text('select s.uni, s.name, s.field, s.year from students s join rsvp_student r_s on s.uni = r_s.uni where r_s.eid = :eid;'), eid=int(eid))
  students = []
  for student in cursor:
    students.append(student)

  cursor = g.conn.execute(text('select r.rid, r.name, r.field, r.company, r.position from recruiters r join rsvp_recruiter r_r on r.rid = r_r.rid where r_r.eid = :eid;'), eid=int(eid))
  recruiters = []
  for recruiter in cursor:
    prof_opps = []
    cursor2 = g.conn.execute(text('select p.pid, p.name from prof_opps p where p.rid = :rid;'), rid=int(recruiter['rid']))
    for prof_opp in cursor2:
	prof_opps.append(prof_opp)
    recruiter2 = dict(recruiter)
    recruiter2['prof_opps'] = prof_opps
    recruiters.append(recruiter2)
  
  return render_template("event.html", info=info, stu_count=len(students), rec_count=len(recruiters), students=students, recruiters=recruiters, \
					venue=venue, host=host)

@app.route('/prof-opp/<pid>')
def prof_opp(pid):
  opp = g.conn.execute(text('select * from prof_opps where pid = :pid;'), pid=pid).fetchone()
  company = g.conn.execute(text('select r.company from recruiters r join prof_opps p on r.rid = p.rid where p.pid = :pid;'), pid=pid).fetchone()['company'] 
  stu_count = g.conn.execute(text('select count(*) as count from students s join applies_to a on s.uni = a.uni where a.pid = :pid;'), pid=pid).fetchone()['count']

  return render_template("prof_opp.html", opp=opp, company=company, stu_count=stu_count)

@app.route('/create-event/', defaults={"error":''})
@app.route('/create-event/<error>')
def create_event(error):
  fields= list(g.conn.execute('select distinct field from students'))
  organizations=list(g.conn.execute('select distinct name from organizations'))
  venues=list(g.conn.execute('select distinct name from venues')) 
  
  context = dict(error=error, fields=fields, organizations=organizations, venues=venues)
  return render_template("create-event.html", **context)

@app.route('/create-event-add', methods=['POST'])
def create_event_add():
  name = request.form['name']
  if (name == ''):
    return redirect('/create-event/%s' % 'name cannot be null!')

  print("create event add: the request", request.form)
  start_time = request.form['start-time']
  end_time = request.form['end-time']
  if (start_time == '' or end_time == ''):
    return redirect('/create-event/%s' % 'time cannot be null!')

  field = request.form['field']
  venue = request.form['venue']
  description = request.form['description']
  organization = request.form['organization']
  print("the venue gotton is", venue)
  try:   
  	vid = g.conn.execute(text("select vid from venues where name = :name;"), name=venue).fetchone()['vid']
  	print("vid,", vid) 
  except:
	return redirect('/create-event/%s' % 'Please choose a venue on the designated list.')

  # insert event if does not exist
  g.conn.execute(text('INSERT INTO events(name, field, vid, description, start_time, end_time) select :name, :field, :vid, :description, :start_time, :end_time where not exists ( select * from events where name = :name and field = :field );'), name=name, field=field, vid=vid, description=description, start_time=start_time, end_time=end_time)
  
  try:
  	eid = g.conn.execute(text("select eid from events where name = :name and field = :field;"), name=name, field=field).fetchone()['eid']
  	oid = g.conn.execute(text("select oid from organizations where name = :name"), name=organization).fetchone()['oid']
  	print("eid and oid:", eid, oid)
  except:
	return redirect('/create-event/%s' % 'Please choose an organization on the designated list.')

  # insert into hosts relation
  g.conn.execute(text('insert into hosts(oid, eid) values (:oid, :eid);'), oid=oid, eid=int(eid)) 
 
  return redirect('/')

@app.route('/create-job/<rid>/<error>')
@app.route('/create-job/<rid>/', defaults={"error":''})
def create_job(rid, error):
  jobtypes = list(g.conn.execute('select distinct job_type from prof_opps'))
  fields= list(g.conn.execute('select distinct field from students'))
  return render_template("create-job.html", error=error, rid=rid, jobtypes=jobtypes, fields=fields)

@app.route('/create-job-add', methods=['POST'])
def create_job_add():
  
  name = request.form['name']
  rid = request.form['rid']
  if (name == ''):
    return redirect('/create-job/%d/%s' % (int(rid), "name cannot be null!"))

  start_time = request.form['start-time']
  end_time = request.form['end-time']
  if (start_time == '' or end_time == ''):
    return redirect('/create-job/%d/%s' % (int(rid), 'time cannot be null!'))

  field = request.form['field']
  job_type= request.form['job-type']

  # insert event if does not exist
  g.conn.execute(text('INSERT INTO prof_opps(name, field, job_type, start_time, end_time, rid) select :name, :field, :job_type, :start_time, :end_time, :rid where not exists ( select * from prof_opps where name = :name and field = :field and rid = :rid);'), name=name, field=field, job_type=job_type, start_time=start_time, end_time=end_time, rid=int(rid))

  return redirect('/recruiter/' + rid)


@app.route('/recruiter/<rid>')
def recruiter(rid):
  past_events = list(g.conn.execute(text('select e.eid, e.name, e.start_time from events e join rsvp_recruiter r on e.eid = r.eid where r.rid=:rid and e.start_time < now()::timestamp;'), rid=int(rid)))
  events = list(g.conn.execute(text('select e.eid, e.name, e.start_time from events e join rsvp_recruiter r on e.eid = r.eid' 
				     ' where r.rid=:rid and e.start_time > now()::timestamp;'), rid=int(rid)))
  rec = g.conn.execute(text('select * from recruiters where rid = :rid;'), rid=int(rid)).fetchone()
  prof_opps = list(g.conn.execute(text('select * from prof_opps where rid = :rid;'), rid=int(rid)))
  return render_template("recruiter.html", rec=rec, prof_opps=prof_opps, events=events, past_events=past_events)

#temporary coping with errors
@app.route('/error-message/<msg>')
def error_message(msg):
  return render_template("error-message.html", msg=msg)

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
