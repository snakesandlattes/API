#!/usr/bin/env python
import json
import datetime
import time
import webapp2
from google.appengine.ext.webapp import util
from google.appengine.ext import db

################################################################################
# Models.

class Customer(db.Model):
  name=           db.StringProperty(required=True)
  phone=          db.PhoneNumberProperty(required=True)
  isCellphone=    db.BooleanProperty()
  email=          db.EmailProperty(required=True)

class Appointment(db.Model):
  date=           db.DateTimeProperty(required=True)
  isWalkIn=       db.BooleanProperty(required=True)
  size=           db.IntegerProperty(required=True)
  name=           db.StringProperty(required=True)
  phone=          db.PhoneNumberProperty(required=True)
  isCellphone=    db.BooleanProperty()
  email=          db.EmailProperty(required=True)  
  notes=          db.StringProperty()
  
  remindSameDay=  db.BooleanProperty()
  remindSameWeek= db.BooleanProperty()
  remindersSent=  db.IntegerProperty()  
  remindViaSMS=   db.BooleanProperty()
  remindViaEmail= db.BooleanProperty()

  def __str__(self):
    return  "Appointment for "+self.name+". A "+\
            ("walk-in" if self.isWalkIn==True else "reserved")+\
            " party, size of "+str(self.size)+". "+\
            " Set for "+self.date.strftime("%I:%M %p at %A, %B %d, %Y")+". "+\
            ("They want a same-day reminder. " if self.remindSameDay==True else "")+\
            ("They want a same-week reminder. " if self.remindSameWeek==True else "")+\
            "Let them know at "+self.email+" or "+self.phone+". "+\
            (("Additionally, they said: "+self.notes) if len(self.notes) else "")

################################################################################
# Controllers.

'''
Take a look at replacement for BlinkConnect interface here:
http://arshaw.com/fullcalendar/
'''

class Root(webapp2.RequestHandler):
  def get(self):
    self.response.out.write('Snakes & Lattes API.')

'''
http://localhost:8080/schedule/showrange/?API_KEY=abc&start=1330110248.388
http://localhost:8080/schedule/showrange/?API_KEY=abc&start=1330119248.388
'''

class SMS:
  def send30minreminder():
    pass

class Remind(webapp2.RequestHandler):
  def get(self):
    a=Appointment.all()
    a.filter("date >=", datetime.timedelta(minutes=-30)+datetime.datetime.today())
    a.filter("remindersSent ==",0)
    a.filter("isCellphone ==", True)
    a.filter("remindViaSMS ==", True)
    self.response.out.write("OK!")

class Schedule:
  class ShowRange(webapp2.RequestHandler):
    def get(self):
      GET=self.request.get
      if GET('API_KEY')!='abc': raise Exception("Invalid API key!")        
      fromdate=float(GET('start'))
      a=Appointment.all()
      a.filter("date >=", datetime.datetime.fromtimestamp(fromdate))
      a.order("date")
      results=a.fetch(10)
      jsonAppointments=[]
      for r in results:
        jsonAppointments.append({
          'id':       r.key().id(),
          'title':    r.name+" for "+str(r.size),
          'start':    r.date.isoformat(),
          'allDay':   False
        })
      self.response.headers.add('Content-Type','application/json')
      self.response.out.write("ADDEVENTS("+json.dumps(jsonAppointments)+")")

  class ShowEvent(webapp2.RequestHandler):
    def get(self):
      GET=self.request.get
      if GET('API_KEY')!='abc': raise Exception("Invalid API key!")
      

  # should only give back a true or false.
  class Try(webapp2.RequestHandler):
    def get(self):
      GET=self.request.get
      if GET('API_KEY')!='abc': raise Exception("Invalid API key!")
      if  len(GET('iswalkin')) * \
          len(GET('date')) * \
          len(GET('size')) * \
          len(GET('name')) * \
          len(GET('phone')) * \
          len(GET('email')) == 0 :
        raise Exception("Required parameters missing!")
      
      # todo: sanitize data, throw appropriate errors if data is fucked
      
      a=Appointment(date=             datetime.datetime.fromtimestamp(float(GET('date'))/1000),
                    isWalkIn=         bool(GET('iswalkin')),
                    size=             int(GET('size')),
                    name=             GET('name'),
                    phone=            GET('phone'),
                    email=            GET('email'),
                    remindSameDay=    bool(GET('sameday')),
                    remindSameWeek=   bool(GET('sameweek')),
                    notes=            GET('notes'),
                    isCellphone=      bool(GET('iscellphone')),
                    remindersSent=    0
                    )
      a.put()
      self.response.out.write(a)
      

'''
http://localhost:8080/schedule/try/?API_KEY=abc&size=5&iswalkin=true&name=Sonny Smith&phone=(141)124-4419&email=sunny@gmail.com&date=1330111248388
http://localhost:8080/schedule/try/?API_KEY=abc&size=12&iswalkin=true&name=Joe Smith&phone=(141)123-4189&email=joe@home.com&date=1330119248388
http://localhost:8080/schedule/try/?API_KEY=abc&size=4&iswalkin=false&name=Jane Doe&phone=(461)444-4444&email=jane@gmail.com&date=1330121248388

http://snl-booking.appspot.com/schedule/try/?API_KEY=abc&size=5&iswalkin=true&name=Sonny Smith&phone=(141)124-4419&email=sunny@gmail.com&date=1330111248388
http://snl-booking.appspot.com/schedule/try/?API_KEY=abc&size=12&iswalkin=true&name=Joe Smith&phone=(141)123-4189&email=joe@home.com&date=1330119248388
http://snl-booking.appspot.com/schedule/try/?API_KEY=abc&size=4&iswalkin=false&name=Jane Doe&phone=(461)444-4444&email=jane@gmail.com&date=1330121248388

http://localhost:8080/schedule/try/?API_KEY=abc&size=12&iswalkin=true&name=Joe Smith&phone=(14fdfd123-4189&email=joe@home.com&date=1330119248388
http://localhost:8080/schedule/try/?API_KEY=abc&size=12&iswalkin=true&name=Joe Smith&phone=(141)123-4189&email=joe@home.com&date=Fri Feb 24 2012 13:40:02 GMT-0500 (EST)
'''

################################################################################

app = webapp2.WSGIApplication([
    ('/',                     Root),
    ('/schedule/showrange/',  Schedule.ShowRange),
    ('/schedule/try/',        Schedule.Try),
    
    ('/remind/',              Remind),
], debug=True)
