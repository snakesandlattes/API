#!/usr/bin/env python
import json
import datetime
import time
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db

################################################################################
# Models.

class Appointment(db.Model):
    date=           db.DateTimeProperty(required=True)
    isWalkIn=       db.BooleanProperty(required=True)
    size=           db.IntegerProperty(required=True)
    name=           db.StringProperty(required=True)
    phone=          db.PhoneNumberProperty(required=True)
    email=          db.EmailProperty(required=True)
    remindSameDay=  db.BooleanProperty()
    remindSameWeek= db.BooleanProperty()
    notes=          db.StringProperty()

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

class MainPage(webapp.RequestHandler):
    def get(self):
        GET=self.request.get
        secretkey=GET('key')
        #self.response.out.write('the secret key is: '+secretkey)
        self.response.out.write('GET stuff: '+secretkey)

'''
http://localhost:8080/schedule/show/?API_KEY=abc&fromdate=1330110248388
http://localhost:8080/schedule/show/?API_KEY=abc&fromdate=1330119248388
'''

class ShowBooking(webapp.RequestHandler):
    def get(self):
        GET=self.request.get
        if GET('API_KEY')!='abc': raise Exception("Invalid API key!")        
        fromdate=float(GET('fromdate'))/1000
        a=Appointment.all()
        a.filter("date >=", datetime.datetime.fromtimestamp(fromdate))
        a.order("date")
        results=a.fetch(5)
        jsonAppointments=[]
        for r in results:
            jsonAppointments.append({
                'date':int(time.mktime(r.date.timetuple())*1e3),
                'iswalkin':r.isWalkIn,
                'size':r.size,
                'name':r.name,
                'phone':r.phone,
                'email':r.email,
                'sameday':r.remindSameDay,
                'sameweek':r.remindSameWeek,
                'notes':r.notes
            })
        self.response.out.write(json.dumps(jsonAppointments))

'''
http://localhost:8080/booking/try/?API_KEY=abc&size=5&iswalkin=true&name=Sonny Smith&phone=(141)124-4419&email=sunny@gmail.com&date=1330111248388
http://localhost:8080/booking/try/?API_KEY=abc&size=12&iswalkin=true&name=Joe Smith&phone=(141)123-4189&email=joe@home.com&date=1330119248388
http://localhost:8080/booking/try/?API_KEY=abc&size=4&iswalkin=false&name=Jane Doe&phone=(461)444-4444&email=jane@gmail.com&date=1330121248388

http://localhost:8080/booking/try/?API_KEY=abc&size=12&iswalkin=true&name=Joe Smith&phone=(14fdfd123-4189&email=joe@home.com&date=1330119248388
http://localhost:8080/booking/try/?API_KEY=abc&size=12&iswalkin=true&name=Joe Smith&phone=(141)123-4189&email=joe@home.com&date=Fri Feb 24 2012 13:40:02 GMT-0500 (EST)
'''

class TryBooking(webapp.RequestHandler):
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
            
        a=Appointment(date=             datetime.datetime.fromtimestamp(float(GET('date'))/1000),
                      isWalkIn=         bool(GET('iswalkin')),
                      size=             int(GET('size')),
                      name=             GET('name'),
                      phone=            GET('phone'),
                      email=            GET('email'),
                      remindSameDay=    bool(GET('sameday')),
                      remindSameWeek=   bool(GET('sameweek')),
                      notes=            GET('notes'))
        a.put()
        self.response.out.write(a)

################################################################################

application = webapp.WSGIApplication([
    ('/', MainPage),
    ('/schedule/show/', ShowBooking),
    ('/schedule/try/', TryBooking),
], debug=True)

def main():   
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
