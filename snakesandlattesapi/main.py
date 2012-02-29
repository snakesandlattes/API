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

class StaffShift(db.Model):
  start=          db.DateTimeProperty(required=True)
  end=            db.DateTimeProperty(required=True)


class Customer(db.Model):
  name=           db.StringProperty(required=True)
  email=          db.EmailProperty(required=True)
  phone=          db.PhoneNumberProperty(required=True)
  isCellphone=    db.BooleanProperty()
  

class Appointment(db.Model):
  isWalkIn=       db.BooleanProperty(required=True)
  date=           db.DateTimeProperty(required=True)  
  size=           db.IntegerProperty(required=True)
  name=           db.StringProperty(required=True)
  phone=          db.PhoneNumberProperty(required=True)
  isCellphone=    db.BooleanProperty()
  email=          db.EmailProperty(required=True)  
  notes=          db.StringProperty()
  
  remindSameDay=  db.BooleanProperty()
  remindSameWeek= db.BooleanProperty()
  remindViaSMS=   db.BooleanProperty()
  remindViaEmail= db.BooleanProperty()
  
  remindersSent=  db.IntegerProperty()

################################################################################
# Errors.

class APIError:
  
  class BadKey(Exception):
    pass
  
  class SMSMessageTooLong(Exception):
    pass
  
  class MissingArgs(Exception):
    pass
  
  class TimeSlotFull(Exception):
    pass

  class General(Exception):
    pass

################################################################################
# Wrapper for class methods.

class Callable:
  def __init__(self, anycallable):
    self.__call__ = anycallable

################################################################################
# Controllers.

class Root(webapp2.RequestHandler):
  def get(self):
    self.response.out.write('Snakes & Lattes API.')

class SMS:  
  MAXLENGTH=155  
  client=TwilioRestClient(APICREDENTIALS.TWILIO.ACCOUNT,APICREDENTIALS.TWILIO.TOKEN)  
  def sendSMS(number,message):
    if len(message)>SMS.MAXLENGTH: raise APIError.SMSMessageTooLong
    sms=SMS.client.sms.messages.create(to="+1"+str(number),
                                       from_="+16479316320",
                                       body=message)
  sendSMS=Callable(sendSMS)

class Remind(webapp2.RequestHandler):
  def get(self):
    WRITE=self.response.out.write
    
    a=Appointment.all()
    # timedelta(hours=-5) not needed since it assumes GMT
    
    # Before this time in the future.
    a.filter("date >=", (datetime.timedelta(minutes=-30)+datetime.datetime.today()))
    # After this time in the past.
    a.filter("date <", (datetime.timedelta(minutes=+30)+datetime.datetime.today()))    
    
    a.filter("remindersSent ==",0)
    a.filter("isCellphone ==", True)
    a.filter("remindViaSMS ==", True)
    results=a.fetch(50)
    for r in results:
      SMS.sendSMS(r.phone,"Your reservation @ Snakes & Lattes begins in 30 min!")
      r.remindersSent+=1
      r.put()
    
    WRITE(str(len(results))+" reminders sent.")


class Schedule:
  
  # todo: when datepicker clicked, this fires, returns array of
  # times already alloted for the date selected.
  class GetExistingForDay(webapp2.RequestHandler):
    def get(self):      
      HEADER=self.response.headers.add
      GET=self.request.get
      WRITE=self.response.out.write
      
      if GET('API_KEY') not in APICREDENTIALS.SNAKESANDLATTES.KEYS:
        raise APIError.BadKey
      
      fromdate=datetime.datetime.fromtimestamp(fromdate)  #+datetime.timedelta(hours=-5)
      
  
  class ShowRange(webapp2.RequestHandler):
    def get(self):
      HEADER=self.response.headers.add
      GET=self.request.get
      WRITE=self.response.out.write
      
      if len(GET('API_KEY'))==0 or GET('API_KEY') not in APICREDENTIALS.SNAKESANDLATTES.KEYS:
        raise APIError.BadKey
      
      fromdate=float(GET('start'))
      a=Appointment.all()
      a.filter("date >=", datetime.datetime.fromtimestamp(fromdate))
      a.order("date")
      results=a.fetch(1000)
      jsonAppointments=[]
      for r in results:
        jsonAppointments.append({
          'id':       r.key().id(),
          'title':    r.name+" for "+str(r.size),
          # convert from GMT (unix timestamp) to EST/EDT
          'start':    (r.date+datetime.timedelta(hours=-5)).isoformat(),
          'allDay':   False,
          'editable': False,
          'end':      (r.date+datetime.timedelta(hours=-5,minutes=+30)).isoformat(),
        })
      HEADER('Content-Type','application/json')
      WRITE("ADDEVENTS("+json.dumps(jsonAppointments)+")")


  class ShowEvent(webapp2.RequestHandler):
    def get(self):
      HEADER=self.response.headers.add
      WRITE=self.response.out.write
      GET=self.request.get
      
      if len(GET('API_KEY'))==0 or GET('API_KEY') not in APICREDENTIALS.SNAKESANDLATTES.KEYS:
        raise APIError.BadKey
      
      if len(GET('id'))==0:
        raise APIError.MissingArgs("No event ID given!")
      
      a=Appointment.get_by_id(long(GET('id')))
      if a==None: raise APIError.General("No events found for that ID!")
      
      HEADER('Content-Type','application/json')
      WRITE("SHOWEVENT("+json.dumps({
        'id':             a.key().id(),
        'name':           a.name,
        'email':          a.email,
        'phone':          str(a.phone),
        'notes':          a.notes,
        'date':           a.date.isoformat(),
        'size':           a.size,
        'remindViaSMS':   a.remindViaSMS,
        'remindViaEmail': a.remindViaEmail,
        'remindersSent':  a.remindersSent,
      })+")")
  
  class DeleteEvent(webapp2.RequestHandler):
    def get(self):
      HEADER=self.response.headers.add
      WRITE=self.response.out.write
      GET=self.request.get
      
      if len(GET('API_KEY'))==0 or GET('API_KEY') not in APICREDENTIALS.SNAKESANDLATTES.KEYS:
        raise APIError.BadKey
      
      if len(GET('id'))==0:
        raise APIError.MissingArgs("No event ID given!")      
      a=Appointment.get_by_id(long(GET('id')))
      if a==None: raise APIError.General("No events found for that ID!")
      a.delete()
      
  
  class SendEventSMS(webapp2.RequestHandler):
    def get(self):
      HEADER=self.response.headers.add
      WRITE=self.response.out.write
      GET=self.request.get
      
      if len(GET('API_KEY'))==0 or GET('API_KEY') not in APICREDENTIALS.SNAKESANDLATTES.KEYS:
        raise APIError.BadKey
      
      if len(GET('id'))==0:
        raise APIError.MissingArgs("No event ID given!")
      
      a=Appointment.get_by_id(long(GET('id')))
      if a==None: raise APIError.General("No events found for that ID!")
      SMS.sendSMS(a.phone,"Hi "+a.name+", your table @ Snakes & Lattes is ready!")
      a.remindersSent+=1
      a.put()
      
  
  class Try(webapp2.RequestHandler):
    def get(self):      
      GET=self.request.get
      WRITE=self.response.out.write
      
      try:
        if len(GET('API_KEY'))==0 or GET('API_KEY') not in APICREDENTIALS.SNAKESANDLATTES.KEYS:
          raise APIError.BadKey
        if  len(GET('isWalkIn')) * \
            len(GET('date')) * \
            len(GET('size')) * \
            len(GET('name')) * \
            len(GET('phone')) * \
            len(GET('email')) == 0 :
          raise APIError.MissingArgs
        
        date=datetime.datetime.fromtimestamp(float(GET('date'))/1000)
        
        a=Appointment.all()
        a.filter("date ==", date)
        results=a.fetch(10)
        if len(results)!=0: raise APIError.TimeSlotFull
        
        a=Appointment(
          date=             date,
          isWalkIn=         bool(GET('isWalkIn')),
          size=             int(GET('size')),
          name=             GET('name'),
          phone=            GET('phone'),
          email=            GET('email'),
          remindSameDay=    bool(GET('remindSameDay')),
          remindSameWeek=   bool(GET('remindSameWeek')),
          remindViaSMS=     bool(GET('remindViaSMS')),
          remindViaEmail=   bool(GET('remindViaEmail')),
          notes=            GET('notes'),
          isCellphone=      bool(GET('isCellphone')),
          remindersSent=    0
        )
        
      except APIError.MissingArgs:
        WRITE('BOOK.FAIL('+json.dumps({
          'text':'Missing required information!',
          'isWalkin':len(GET('isWalkin')),
          'date':len(GET('date')),
          'size':len(GET('size')),
          'name':len(GET('name')),
          'phone':len(GET('phone')),
          'email':len(GET('email')),
        })+')')        
      except APIError.BadKey:
        WRITE('BOOK.FAIL('+json.dumps({'text':'Invalid API key!'})+')')
      except APIError.TimeSlotFull:
        WRITE('BOOK.FAIL('+json.dumps({'text':'Time slot not available!'})+')')
      else:
        a.put()
        WRITE('BOOK.SUCCESS()')

################################################################################
# URL Handlers.

app = webapp2.WSGIApplication([
    ('/',                     Root),
    ('/schedule/delete/',     Schedule.DeleteEvent),
    ('/schedule/show/event/', Schedule.ShowEvent),
    ('/schedule/show/range/', Schedule.ShowRange),
    ('/schedule/try/',        Schedule.Try),
    
    ('/remind/',              Remind),
    ('/SMS/',                 Schedule.SendEventSMS),
], debug=True)
