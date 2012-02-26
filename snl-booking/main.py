#!/usr/bin/env python
import json
import datetime
import time
import APICREDENTIALS
import webapp2
from twilio.rest import TwilioRestClient
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

class Root(webapp2.RequestHandler):
  def get(self):
    self.response.out.write('Snakes & Lattes API.')

class SMS:
  
  MAXLENGTH=155
  
  client=TwilioRestClient(APICREDENTIALS.TWILIO.ACCOUNT,
                          APICREDENTIALS.TWILIO.TOKEN)
  class sendAPI(webapp2.RequestHandler):
    def get(self):
      GET=self.request.get
      if GET('API_KEY')!='abc': raise Exception("Invalid API key!")        
      if len(GET('cell'))==0: raise Exception("No cell phone # given!")
      sms=SMS.client.sms.messages.create(to="+1"+GET('cell'),
                                         from_="+16479316320",
                                         body="Snakes & Lattes: your table is ready!")
      self.response.out.write(str(sms))
      
  def send30minreminder(number,message):
    if len(message)>SMS.MAXLENGTH: raise Exception("Message exceeds length for SMS")
    sms=SMS.client.sms.messages.create(to="+1"+str(number),
                                       from_="+16479316320",
                                       body=message)

class Remind(webapp2.RequestHandler):
  def get(self):
    a=Appointment.all()
    a.filter("date >=", datetime.timedelta(minutes=-30)+datetime.datetime.today())
    a.filter("date <", datetime.timedelta(minutes=-30)+datetime.datetime.today())
    a.filter("remindersSent ==",0)
    a.filter("isCellphone ==", True)
    a.filter("remindViaSMS ==", True)
    results=a.fetch()
    for r in results:
      SMS.send30minreminder()
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
          'allDay':   False,
          'editable': True
        })
      self.response.headers.add('Content-Type','application/json')
      self.response.out.write("ADDEVENTS("+json.dumps(jsonAppointments)+")")

  class ShowEvent(webapp2.RequestHandler):
    def get(self):
      GET=self.request.get
      if GET('API_KEY')!='abc': raise Exception("Invalid API key!")
      if len(GET('id'))==0: raise Exception("No event ID given!")
      a=Appointment.all()
      a.filter("id ==", GET('id'))
      result=a.fetch(1)
      if len(result)==0: raise Exception("No events found for that ID!")
      r=result[0]
      self.response.headers.add('Content-Type','application/json')      
      self.response.out.write("ADDEVENTS("+json.dumps({
        'name':   r.name,
        'email':  r.email,
        'phone':  str(r.phone),
        'notes':  r.notes,
        'date':   r.date.isoformat(),
        'size':   
      })+")")

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

################################################################################
# URL Handlers.

app = webapp2.WSGIApplication([
    ('/',                     Root),
    ('/schedule/showrange/',  Schedule.ShowRange),
    ('/schedule/try/',        Schedule.Try),
    
    ('/remind/',              Remind),
    ('/SMS/',                 SMS.sendAPI)
], debug=True)
