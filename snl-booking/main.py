#!/usr/bin/env python

import datetime
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db

################################################################################
# Models.

class Appointment(db.Model):
    date=db.DateTimeProperty()
    isWalkIn=db.BooleanProperty(required=True)
    size=db.IntegerProperty(required=True)
    name=db.StringProperty(required=True)
    phone=db.PhoneNumberProperty(required=True)
    email=db.EmailProperty(required=True)
    remindSameDay=db.BooleanProperty()
    remindSameWeek=db.BooleanProperty()
    notes=db.StringProperty()

    def __str__(self):
        return  "Appointment for "+self.name+". A "+\
                ("walk-in" if self.isWalkIn==True else "reserved")+\
                " party, size of "+str(self.size)+". "+\
                ("They want a same-day reminder. " if self.remindSameDay==True else "")+\
                ("They want a same-week reminder. " if self.remindSameWeek==True else "")+\
                "Let them know at "+self.email+" or "+self.phone+". "+\
                (("Additionally, they said: "+self.notes) if len(self.notes) else "")

################################################################################
# Controllers.

class ErrorCodes:
    class json:
        pass

class MainPage(webapp.RequestHandler):
    def get(self):
        GET=self.request.get
        secretkey=GET('key')
        #self.response.out.write('the secret key is: '+secretkey)
        self.response.out.write('GET stuff: '+secretkey)

class ShowBooking(webapp.RequestHandler):
    def get(self):
        self.response.out.write('Hello wofsdfsdfsdrld!')

'''
http://localhost:8080/TryBooking?API_KEY=abc&size=12&iswalkin=true&name=Joe Smith&phone=(141)123-4189&email=joe@home.com
http://localhost:8080/TryBooking?API_KEY=abc&size=12&iswalkin=true&name=Joe Smith&phone=(14fdfd123-4189&email=joe@home.com
http://localhost:8080/TryBooking?API_KEY=abc&size=12&iswalkin=true&name=Joe Smith&phone=(141)123-4189&email=joe@home.com&date=Fri Feb 24 2012 13:40:02 GMT-0500 (EST)
'''

class TryBooking(webapp.RequestHandler):
    def get(self):
        GET=self.request.get
        if GET('API_KEY')!='abc': raise Exception("Invalid API key!")
        if  len(GET('iswalkin')) * \
            len(GET('size')) * \
            len(GET('name')) * \
            len(GET('phone')) * \
            len(GET('email')) == 0 :
            raise Exception("Required parameters missing!")
            
        a=Appointment(date=             GET('date'),
                      isWalkIn=         bool(GET('iswalkin')),
                      size=             int(GET('size')),
                      name=             GET('name'),
                      phone=            GET('phone'),
                      email=            GET('email'),
                      remindSameDay=    bool(GET('sameday')),
                      remindSameWeek=   bool(GET('sameweek')),
                      notes=            GET('notes'))
        self.response.out.write(a)

################################################################################

application = webapp.WSGIApplication([
    ('/', MainPage),
    ('/ShowBooking', ShowBooking),
    ('/TryBooking', TryBooking),
], debug=True)

def main():
    
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
