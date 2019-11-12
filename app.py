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
@app.route('/', defaults={'field': None})
@app.route('/<field>')
def index(field):
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
    if (not field or result['field'] == field):
      event = dict(result)
      event['outdated'] = str(event['start_time'] < datetime.datetime.now())
      events.append(event)
  cursor.close()
  
  fields = list(g.conn.execute("select distinct field from events"))
  context = dict(events = events, fields = fields)
  return render_template("index.html", **context)

@app.route('/apply/<pid>')
def apply(pid):
  name = next(g.conn.execute("select name from prof_opps where pid = " + pid + ";"))['name']
  return render_template("apply.html", pid=pid, name=name)

@app.route('/apply-add', methods=['POST'])
def apply_add():
  pid = request.form['pid']
  name = request.form['name']
  if (name == ''):
    print("name is null") 
    # TODO
  field = request.form['field']
  year = request.form['year'] 
  uni = request.form['uni']
  if (uni == ''): 
    print("uni is null")
    # TODO 
  phone = request.form['phone']

  # insert the student if not exist
  g.conn.execute('INSERT INTO students(uni, name, phone, field, year) select \'%s\', \'%s\', \'%s\', \'%s\', \'%s\'' % (uni, name, phone, field, year) + \
                    'where not exists ( select * from students where uni = \'%s\');' % (uni))

  # insert into applies_to
  # TODO: error checking
  g.conn.execute('INSERT INTO applies_to(uni, pid, time) VALUES (\'%s\', %d, date_trunc(\'second\', now())::timestamp);' % (uni, int(pid)));
  
  return redirect('/')

@app.route('/rsvp/<eid>')
def rsvp(eid):
  fields = list(g.conn.execute("select distinct field from events"))
  name = g.conn.execute("select name from events where eid = \'" + eid + "\';")
  return render_template("rsvp.html", eid=eid, name=next(name)['name'], fields=fields)


# Example of adding new data to the database
@app.route('/rsvp-add', methods=['POST'])
def rsvp_add():

  print("rsvp-add page says hello; identity " + request.form['identity'] + " equals identity is " + str(request.form['identity'] == 'student'))
  print(request.form)
  eid = request.form['eid']
  name = request.form['name']
  if (name == ''):
    print("name is null") 
    # TODO
  field = request.form['field'] 

  # when the person is a student
  if (request.form['identity'].strip() == 'student'):
    year = request.form['year'] 
    uni = request.form['uni']
    if (uni == ''): 
      print("uni is null")
      # TODO 
    phone = request.form['phone']
    
    # insert student if not exists
    g.conn.execute('INSERT INTO students(uni, name, phone, field, year) select \'%s\', \'%s\', \'%s\', \'%s\', \'%s\'' % (uni, name, phone, field, year) + \
    		    'where not exists ( select * from students where uni = \'%s\');' % (uni))

    # insert into RSVP AFTER ERROR CHECKING
    # TODO: error checking
    g.conn.execute('INSERT INTO rsvp_student(uni, eid, time) VALUES (\'%s\', %d, date_trunc(\'second\', now())::timestamp);' % (uni, int(eid))) 

  # when the person is a recruiter
  elif (request.form['identity'].strip() == 'recruiter'):
    company = request.form['company']
    position = request.form['position']
    
    # insert recruiter if not exists
    g.conn.execute('INSERT INTO recruiters(name, field, company, position) select \'%s\', \'%s\', \'%s\', \'%s\'' + \
                    'where not exists ( select * from recruiters where name = \'%s\' and company = \'%s\');' % (name, field, company, position, name, company))
  
    # insert into RSVP AFTER ERROR CHECKING
    # TODO: error checking
    rid = g.conn.execute('select rid from recruiters where name = \'%s\' and company = \'%s\';')['rid']
    g.conn.execute('INSERT INTO rsvp_student(rid, eid, time) VALUES (%d, %d, now()::timestamp);' % (int(rid), int(eid)))           
  
  else:
    print("identity is neither student nor recruiter")
    # TODO
  print("eid:", request.form['eid'])
  
  return redirect('/')


@app.route('/event/<eid>')
def event(eid):
  info = next(g.conn.execute('select * from events where eid = \'' + eid + '\';'))
  venue = next(g.conn.execute('select name, address from venues where vid = \'' + info['vid'] + '\';'))
  host = next(g.conn.execute('select o.name from organizations o join hosts h on o.oid = h.oid where h.eid = ' + eid + ';'))['name']
  
  # querying the rsvped students and recruiters
  cursor = g.conn.execute('select s.uni, s.name, s.field, s.year from students s join rsvp_student r_s on s.uni = r_s.uni where r_s.eid = \'' + eid + '\';')
  students = []
  for student in cursor:
    students.append(student)

  cursor = g.conn.execute('select r.rid, r.name, r.field, r.company, r.position from recruiters r join rsvp_recruiter r_r on r.rid = r_r.rid where r_r.eid = \'' + eid + '\';')
  recruiters = []
  for recruiter in cursor:
    prof_opps = []
    cursor2 = g.conn.execute('select p.pid, p.name from prof_opps p where p.rid = ' + str(recruiter['rid']) + ';')
    for prof_opp in cursor2:
	prof_opps.append(prof_opp)
    recruiter2 = dict(recruiter)
    recruiter2['prof_opps'] = prof_opps
    recruiters.append(recruiter2)
  
  return render_template("event.html", info=info, stu_count=len(students), rec_count=len(recruiters), students=students, recruiters=recruiters, \
					venue=venue, host=host)

@app.route('/prof-opp/<pid>')
def prof_opp(pid):
  opp = next(g.conn.execute('select * from prof_opps where pid = \'' + pid + '\';'))
  company = next(g.conn.execute('select r.company from recruiters r join prof_opps p on r.rid = p.rid where p.pid = \'' + pid + '\';'))['company']
  stu_count = next(g.conn.execute('select count(*) as count from students s join applies_to a on s.uni = a.uni where a.pid = \'' + pid + '\';'))['count']

  return render_template("prof_opp.html", opp=opp, company=company, stu_count=stu_count)

@app.route('/create-event')
def create_event():
  fields= list(g.conn.execute('select distinct field from students'))
  organizations=list(g.conn.execute('select distinct name from organizations'))
  venues=list(g.conn.execute('select distinct name from venues')) 
  
  context = dict(fields=fields, organizations=organizations, venues=venues)
  return render_template("create-event.html", **context)

@app.route('/create-event-add', methods=['POST'])
def create_event_add():
  name = request.form['name']
  if (name == ''):
    print("event without name")
    # TODO
  print("create event add: the request", request.form)
  start_time = request.form['start-time']
  end_time = request.form['end-time']
  field = request.form['field']
  venue = request.form['venue']
  description = request.form['description']
  organization = request.form['organization']
  print("the venue gotton is", venue)
  try:   
  	vid = next(g.conn.execute("select vid from venues where name = '" + venue + "';"))['vid']
  	print("vid,", vid) 
  except:
	print("the venue is wrong")
	# TODO
	return redirect('/error-message/venue-is-wrong')

  # insert event if does not exist
  g.conn.execute('INSERT INTO events(name, field, vid, description, start_time, end_time) select \'%s\', \'%s\', \'%s\', \'%s\', \'%s\', \'%s\' where not exists ( select * from events where name = \'%s\' and field = \'%s\');' % (name, field, vid, description, start_time, end_time, name, field))
  
  try:
  	eid = next(g.conn.execute("select eid from events where name = '" + name + "' and field = '" + field + "';"))['eid']
  	oid = next(g.conn.execute("select oid from organizations where name = '" + organization + "';"))['oid']
  	print("eid and oid:", eid, oid)
  except:
	print("the organization is wrong")
        # TODO
        return redirect('/error-message/organization-is-wrong')

  # insert into hosts relation
  g.conn.execute('insert into hosts(oid, eid) values (\'%s\', %d)' % (oid, int(eid))) 
 
  return redirect('/')


@app.route('/create-job/<rid>')
def create_job(rid):
  jobtypes = list(g.conn.execute('select distinct job_type from prof_opps'))
  fields= list(g.conn.execute('select distinct field from students'))
  return render_template("create-job.html", rid=rid, jobtypes=jobtypes, fields=fields)

@app.route('/create-job-add', methods=['POST'])
def create_job_add():
  
  name = request.form['name']
  if (name == ''):
    return redirect("/error-message/job-without-name")
    # TODO
  start_time = request.form['start-time']
  end_time = request.form['end-time']
  field = request.form['field']
  job_type= request.form['job-type']
  rid = request.form['rid']

  # insert event if does not exist
  g.conn.execute('INSERT INTO prof_opps(name, field, job_type, start_time, end_time, rid) select \'%s\', \'%s\', \'%s\', \'%s\', \'%s\', %s where not exists ( select * from prof_opps where name = \'%s\' and field = \'%s\' and rid = %s);' % (name, field, job_type, start_time, end_time, rid, name, field, rid))

  return redirect('/recruiter/' + rid)


@app.route('/recruiter/<rid>')
def recruiter(rid):
  rec = next(g.conn.execute('select * from recruiters where rid = ' + rid + ';'))
  prof_opps = list(g.conn.execute('select * from prof_opps where rid = ' + rid + ';'))
  return render_template("recruiter.html", rec=rec, prof_opps=prof_opps)

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
