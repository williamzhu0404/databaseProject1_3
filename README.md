# databaseProject1_3
CS W4111
Yuanyuting Wang (yw3241) and Yifan Zhu (yz3780)

1) The PostgreSQL account for database: yw3241.

2) The URL of web application: http://35.231.255.134:8111/

3) Features implemented:

  a) Those included in part 1 
	i) Student organizations can use this platform to post their events, and publicize such events for students and recruiters to RSVP.
	ii) Students can use this platform to browse the past the future events happening on campus, and can filter these events by time / field of study according to their personal needs.
	iii) The recruiters can use this platform to RSVP for student events that they want to attend to publicize their professional opportunities. They can also customizably post the professional opportunities that their companies offer.
  
  b) Things not included in part 1
	i) The dynamic rendering of the same page catering to different users (students/recruiters), which generates different input fields and applies different contraints to the users, and which also allows error message to appear without rerouting to another web page.
	ii) The event page also includes an extensive enumeration of the RSVP'ed students and recruiters for the user to estimate the nature of each certain event; for the RSVP'ed recruiters the page also lists the job opportunities they are offering, which makes it more convenient for student users to reach out to those recruiters coming to the same event as they are.
	iii) Students can conveniently go to the page of a professional opportunity and link to its related recruiters, and can also view all events the recruiter is going to, as well as the opportunities that this recruiter is offering on this recruiter's personal profile page. This provides greater transparency for the students and makes networking, reaching out and obtaining professional success an easier reality.
	iv) Drop-down menus to expediate user's process of inputting their own data.

  c) Things to be included in the future
	i) Functionality wise: The branding of student organizations as a coherent entity and consistent host of on campus events; there should be pages about each organization alone too, including the information about their members and the events that have hosted / are going to hold. Also, if technology permits, there should be a miniature platform for direct communication between the students and the recruiters, maybe in the form of a small chat box or a portal for students to submit their resumes for review. 
	ii) Styling. The current website is way too ugly. More sense of direction needs to be given, otherwise in no way is this site user-friendly.

  d) Things in part 1 that are not included and why
	i) Filtering of events by location. Since the platform caters solely to on-campus events happening at designated venues, different locations would not make a huge different to the students, and are therefore not of our interest.
	ii) Major as an independent entity. We had the idea initially but was convinced by the TAs to substitute it with the field of study as separate attributes in multiple entities. The reason is there is not really any independent attribute to a field itself that is not dependent on other entities, and therefore it makes more sense to use the fields to characterize different entities individually instead.

4) Interesting queries
Webpage 1: /event/(eid)
Interesting database operation:
select s.uni, s.name, s.field, s.year from students s join rsvp_student r_s on s.uni = r_s.uni where r_s.eid = :eid;
select r.rid, r.name, r.field, r.company, r.position from recruiters r join rsvp_recruiter r_r on r.rid = r_r.rid where r_r.eid = :eid;
select p.pid, p.name from prof_opps p where p.rid = :rid;

It uses the eid as input and outputs the number of students and recruiters who have rsvp'ed the event, and thereby also displayed part of their information that might be relevant to the event, especially since there's a subquery nested within another subquery that extracts information about the professional opportunities that each recruiter is offering.
It is an interesting query as students might be interested to know how popular this event might be to help them decide whether to attend it. This also gives the students more information transparency.

Webpage 2: /rsvp-add
Interesting database operation:
INSERT INTO students(uni, name, phone, field, year) select ( (uni), (name), (phone), (field), (year)) where not exists ( select * from students where uni = (uni));
This web page, combined with /rsvp/<eid>, utilizes web routing to successfully transmit data from the browswer to frontend server, to database, and then to the browser again, mainly by relaying the eid key for querying and inserting values and by utilizing flask tricks like url variables and Jinja variables. 
It uses the uni, name, phone, field and year as input and insert the record of new students with those input as attributes if the uni is not found in the table Students in our database, while also making sure to error check by utilizing two folds of safety checks and providing a safe page to reroute to in case of database exceptions. This query is the center of an efficient and secure communication attempt between front and back end.
`
