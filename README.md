# databaseProject1_3
CS W4111

The PostgreSQL account where your database on our server resides is yw3241.

The URL of your web application is http://35.231.255.134:8111/

Features implemented in the original proposal in Part 1:

Student organizations can post the information of their events on this platform,
recruiters can also post fellowship/internship opportunities on this website, or RSVP to present at certain events. 
Other students can filter these events based on time, and field of study, and RSVP for such events. 

Features not implemented in the original proposal in Part 1:

Filtering events based on location does not seem to be an awfully useful functionality, which is therefore not implemented.


Webpage 1: /event/(eid)
Interesting database operation:
select s.uni, s.name, s.field, s.year from students s join rsvp_student r_s on s.uni = r_s.uni where r_s.eid = (eid);

It uses the eid as input and outputs the number of students who have rsvp'ed the event.
It is an interesting query as students might be interested to know how popular this event might be to help them decide whether to attend it. It also joins 2 tables to achieve that end.

Webpage 2: /rsvp-add
Interesting database operation:
INSERT INTO students(uni, name, phone, field, year) select ( (uni), (name), (phone), (field), (year)) where not exists ( select * from students where uni = (uni));
It uses the uni, name, phone, field and year as input and insert the record of new students with those input as attributes if the uni is not found in the table Students in our database, making this database operation quite interesting in our opinion.

