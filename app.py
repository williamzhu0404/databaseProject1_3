#!/usr/bin/env python2.7

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

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@104.196.18.7/w4111
#
# For example, if you had username biliris and password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://biliris:foobar@104.196.18.7/w4111"
#
DATABASEURI = "postgresql://yw3241:7276@34.74.165.156/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#

class Event:
  def __init__(self, name, field, description):
    self.name = name
    self.field = field
    self.description = description

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
@app.route('/')
def index():
  """
  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2
  """

  print request.args

  cursor = g.conn.execute("select * from events;")
  events = []
  for result in cursor:
    events.append(Event(result['name'], result['field'], result['description']))
  cursor.close()
  
  context = dict(events = events)
  return render_template("index.html", **context)

@app.route('/rsvp')
def rsvp():
  return render_template("rsvp.html")


# Example of adding new data to the database
@app.route('/rsvp-add', methods=['POST'])
def rsvp_add():
  name = request.form['name']
  if (name == ''):
    print("name is null") 
    # deal with it!!!!!!!!!!!!!!!!! 
  field = request.form['field'] 

  if (request.form['identity'] == 'student'):
    year = request.form['year'] 
    uni = request.form['uni']
    if (uni == ''): 
      print("uni is null")
      # deal with it!!!!!!!!!!!!!!!!! 

    phone = request.form['phone']
    
    g.conn.execute('INSERT INTO students(uni, name, phone, field, year) VALUES (\'%s\', \'%s\', \'%s\', \'%s\', \'%s\');' \
		    % (uni, name, phone, field, year))
  elif (request.form['identity'] == 'recruiter'):
    company = request.form['company']
    position = request.form['position']
    
    g.conn.execute('INSERT INTO recruiters(name, field, company, positon) VALUES (\'%s\', \'%s\', \'%s\', \'%s\');' \
		    % (name, field, company, position))
  else:
    print("identity is neither student nor recruiter")
    # throw error!!!!!!!!!!!!!!!!!!1

  return redirect('/')


@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()


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
