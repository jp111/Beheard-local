import webapp2
import webapp2
from google.appengine.api import users
from google.appengine.api import mail
from google.appengine.ext import blobstore
import cgi 
from google.appengine.ext import db
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp.util import run_wsgi_app
import jinja2
import os
import json
import time
from datetime import date
#setting the environment for templates
JINJA_ENVIRONMENT = jinja2.Environment(
	    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
	        extensions=['jinja2.ext.autoescape'],
		    autoescape=True)

from math import sin, cos, asin, sqrt, degrees, radians

Earth_radius_km = 6371.0
RADIUS = Earth_radius_km

def haversine(angle_radians):
    return sin(angle_radians / 2.0) ** 2

def inverse_haversine(h):
    return 2 * asin(sqrt(h)) # radians

def distance_between_points(lat1, lon1, lat2, lon2):
    # all args are in degrees
    # WARNING: loss of absolute precision when points are near-antipodal
    lat1 = radians(lat1)
    lat2 = radians(lat2)
    dlat = lat2 - lat1
    dlon = radians(lon2 - lon1)
    h = haversine(dlat) + cos(lat1) * cos(lat2) * haversine(dlon)
    return RADIUS * inverse_haversine(h)

def bounding_box(lat, lon, distance):
    # Input and output lats/longs are in degrees.
    # Distance arg must be in same units as RADIUS.
    # Returns (dlat, dlon) such that
    # no points outside lat +/- dlat or outside lon +/- dlon
    # are <= "distance" from the (lat, lon) point.
    # Derived from: http://janmatuschek.de/LatitudeLongitudeBoundingCoordinates
    # WARNING: problems if North/South Pole is in circle of interest
    # WARNING: problems if longitude meridian +/-180 degrees intersects circle of interest
    # See quoted article for how to detect and overcome the above problems.
    # Note: the result is independent of the longitude of the central point, so the
    # "lon" arg is not used.
    dlat = distance / RADIUS
    dlon = asin(sin(dlat) / cos(radians(lat)))
    return degrees(dlat), degrees(dlon)

if __name__ == "__main__":

    # Examples from Jan Matuschek's article

    def test(lat, lon, dist):
        print "test bounding box", lat, lon, dist
        dlat, dlon = bounding_box(lat, lon, dist)
        print "dlat, dlon degrees", dlat, dlon
        print "lat min/max rads", map(radians, (lat - dlat, lat + dlat))
        print "lon min/max rads", map(radians, (lon - dlon, lon + dlon))

    print "liberty to eiffel"
    print distance_between_points(40.6892, -74.0444, 48.8583, 2.2945) # about 5837 km
    print
    print "calc min/max lat/lon"
    degs = map(degrees, (1.3963, -0.6981))
    test(*degs, dist=1000)
    print
    degs = map(degrees, (1.3963, -0.6981, 1.4618, -1.6021))
    print degs, "distance", distance_between_points(*degs) # 872 km

class complain(db.Model):
	     cuser=db.UserProperty()
             cname=db.StringProperty()
             desc=db.TextProperty()
	     contact=db.PhoneNumberProperty()
	     address=db.PostalAddressProperty()
	     coordinates=db.GeoPtProperty()
             mul=db.StringProperty()
	     image=db.BlobProperty()
class follow(db.Model):
	fuser=db.StringProperty()
	fcomp=db.StringProperty()
	status=db.IntegerProperty()
class chatit(db.Model):
	     user=db.StringProperty()
	     
class like(db.Model):	     
	    cid=db.StringProperty()
	    user=db.StringProperty()
	    flag=db.IntegerProperty()

class posts(db.Model):
            puser=db.StringProperty()
            comment=db.TextProperty()
            compid=db.StringProperty()


class donor(db.Model):
             dname=db.StringProperty()
	     duser=db.UserProperty()
	     bgroup=db.StringProperty(choices=set(["A+","A-","B+","B-","AB+","AB-","O+","O-"]))
	     contact=db.PhoneNumberProperty()
	     address=db.PostalAddressProperty()
	     coordinates=db.GeoPtProperty()
	     age=db.StringProperty()
	     image=db.BlobProperty()
class recipient(db.Model):
    	     ruser=db.UserProperty()
	     rname=db.StringProperty(required=True)
	     bgroup=db.StringProperty(required=True,choices=set(["A+","A-","B+","B-","AB+","AB-","O+","O-"]))
	     contact=db.PhoneNumberProperty(required=True)
	     address=db.PostalAddressProperty(required=True)
	     bunit=db.StringProperty(required=True)
	     bdate=db.DateProperty()
	     coord=db.GeoPtProperty()

class hospital(db.Model):
    	     huser=db.UserProperty()
	     contact=db.PhoneNumberProperty(required=True)
	     address=db.PostalAddressProperty(required=True)
	     rname=db.StringProperty(required=True)
	     abgroup=db.StringListProperty()

class camp(db.Model):
    	     cuser=db.UserProperty()
	     contact=db.PhoneNumberProperty()
	     address=db.PostalAddressProperty()
	     cname=db.StringProperty()
	     sdate=db.StringProperty()
	     edate=db.StringProperty()
	     coord=db.GeoPtProperty()
	     poster=db.BlobProperty()
class link(db.Model):
	    cid=db.StringProperty()
	    guser=db.StringProperty()
	    flag=db.IntegerProperty()

'''class posts(db.Model):
            puser=db.StringProperty()
            comment=db.TextProperty()
            campid=db.StringProperty()'''
class story(db.Model):
	    suser=db.UserProperty()
	    story=db.TextProperty()
	    tag=db.TextProperty()
	    pic=db.BlobProperty()
class notification(db.Model):
	    did=db.UserProperty()
	    rid=db.StringProperty()
	    flag=db.IntegerProperty()

class main(webapp2.RequestHandler):
    	def get(self):
		user = users.get_current_user()
	    	login=users.create_login_url("/index")
		template_values={'login':login}
		template=JINJA_ENVIRONMENT.get_template('html/main.html')
		self.response.write(template.render(template_values))


class index(webapp2.RequestHandler):
    	def get(self):
		likeit=[]
		numberit=[]
		flag=0
		user = users.get_current_user()
		if user:
			result=complain.all()
			followit=[]
			for i in result:
				folfilter=follow.all().filter('fuser =',str(user.email())).filter('fcomp =',str(i.key()))
				if folfilter.count()>0:
					if folfilter[0].status==1:
						followit.append(1)
					else:
						followit.append(2)
				else:
					followit.append(2)
				y=like.all().filter('cid =',str(i.key())).filter('flag =',1)
				x=like.all().filter('user =',str(user.email())).filter('cid =',str(i.key()))
				numberit.append(y.count())
				if x.count()!=0 and x[0].flag == 1:
					likeit.append(1)
				else:
					likeit.append(0)
			if result.count()>0:
				flag=1
	    		template_values={'flag':flag,'result':result, 'likeit':likeit, 'numberit':numberit, 'followit':followit}
	    		template=JINJA_ENVIRONMENT.get_template('html/index.html')
			self.response.write(template.render(template_values))
		else:
			self.redirect(users.create_login_url(self.request.uri))


class donate_blood(webapp2.RequestHandler):
    	def get(self):
		user = users.get_current_user()
	        if not user:
			self.redirect(users.create_login_url(self.request.uri))
	    	template_values={}
		upload_url=blobstore.create_upload_url('/upload_photo')
	    	template=JINJA_ENVIRONMENT.get_template('html/complainit.html')
#		self.response.out.write('<html><body>')
 #self.response.out.write('<form action="%s" method="POST" enctype="multipart/form-data">' % upload_url)
  #self.response.out.write('''Upload File: <input type="file" name="file"><br> <input type="submit"
#         name="submit" value="Submit"> </form></body></html>''')
		self.response.write(template.render(template_values))
	def post(self):
		v=str(self.request.get("lat"))
		l=str(self.request.get("long"))
		s=v+","+l
		var=complain(cname=self.request.get("name"),cuser=users.get_current_user(),contact=self.request.get("phone"),address=self.request.get("address"),coordinates=s)
		var.put()
		self.redirect("complainit")
class donate_blood(webapp2.RequestHandler):
    	def get(self):
		user = users.get_current_user()
	        if user:
			self.redirect('/pinfo')
		else:
			self.redirect(users.create_login_url(self.request.uri))
	    	template_values={}
		upload_url=blobstore.create_upload_url('/upload_photo')
	    	template=JINJA_ENVIRONMENT.get_template('html/donate_blood.html')
#		self.response.out.write('<html><body>')
 #self.response.out.write('<form action="%s" method="POST" enctype="multipart/form-data">' % upload_url)
  #self.response.out.write('''Upload File: <input type="file" name="file"><br> <input type="submit"
#         name="submit" value="Submit"> </form></body></html>''')
		self.response.write(template.render(template_values))
	def post(self):
		v=str(self.request.get("lat"))
		l=str(self.request.get("long"))
		s=v+","+l
		var=donor(dname=self.request.get("name"),duser=users.get_current_user(),bgroup=self.request.get("bgroup"),contact=self.request.get("phone"),address=self.request.get("address"),age=self.request.get("age"),coordinates=s)
		var.put()
		self.redirect("/index")
class comp_loc(webapp2.RequestHandler):
	def get(self):
		user = users.get_current_user()
		if user:
			template_values={}
	    		template=JINJA_ENVIRONMENT.get_template('html/comp_loc.html')
			self.response.write(template.render(template_values))

		else:
			self.redirect(users.create_login_url(self.request.uri))
	def post(self):
		v=str(self.request.get("lat"))
		f=str(self.request.get("long"))
		s=v+','+f
		add=self.request.get("address")
		k=complain.all()
		lat=[]
                lng=[]
                final=[]
                add=[]
                name=[]
                lis=[]
		for i in k:
			g=str(i.coordinates)
			l=g.split(",")
			lis.append(i.address)
			lis.append(i.contact)
			lis=[]
			lat.append(float(l[0]))
			lat.append(float(l[1]))
			lat.append(i.cname)
			lat.append(i.mul)
			lat.append(i.address)
			lat.append(str(i.key()))
			final.append(lat)
			lat=[]
			add.append(i.address)
			name.append(add)
		template_values={'k':k,'final':json.dumps(final),'locate':add,'long':float(f),'latit':float(v)}
                template=JINJA_ENVIRONMENT.get_template('html/all_comp.html')
                self.response.write(template.render(template_values))
class liked(webapp2.RequestHandler):
	def get(self,ky):
		self.redirect("/allcomplain")
	def post(self,ky):
		user=users.get_current_user()
		x=like.all().filter('user =',str(user.email())).filter('cid =',str(ky))
		if x.count()==0:
			var=like(cid=str(ky),user=str(user.email()),flag=1)
			var.put()
		else:
			k=x[0].key()
			obj=like.get(k)
			obj.flag=1
			obj.put()
		self.redirect("/allcomplain")

	
class liked1(webapp2.RequestHandler):
	def get(self,ky):
		self.redirect("/mycomplain")
	def post(self,ky):
		user=users.get_current_user()
		x=like.all().filter('user =',str(user.email())).filter('cid =',str(ky))
		if x.count()==0:
			var=like(cid=str(ky),user=str(user.email()),flag=1)
			var.put()
		else:
			k=x[0].key()
			obj=like.get(k)
			obj.flag=1
			obj.put()
		self.redirect("/mycomplain")
class liked2(webapp2.RequestHandler):
	def get(self,ky,flg):
		self.redirect("/category/"+flg)
	def post(self,ky,flg):
		user=users.get_current_user()
		x=like.all().filter('user =',str(user.email())).filter('cid =',str(ky))
		if x.count()==0:
			var=like(cid=str(ky),user=str(user.email()),flag=1)
			var.put()
		else:
			k=x[0].key()
			obj=like.get(k)
			obj.flag=1
			obj.put()
		self.redirect("/category/"+flg)
class liked3(webapp2.RequestHandler):
	def get(self,ky):
		self.redirect("/comp_follow")
	def post(self,ky):
		user=users.get_current_user()
		x=like.all().filter('user =',str(user.email())).filter('cid =',str(ky))
		if x.count()==0:
			var=like(cid=str(ky),user=str(user.email()),flag=1)
			var.put()
		else:
			k=x[0].key()
			obj=like.get(k)
			obj.flag=1
			obj.put()
		self.redirect("/comp_follow")
class liked4(webapp2.RequestHandler):
	def get(self,ky):
		self.redirect("/viewit/"+ky)
	def post(self,ky):
		user=users.get_current_user()
		x=like.all().filter('user =',str(user.email())).filter('cid =',str(ky))
		if x.count()==0:
			var=like(cid=str(ky),user=str(user.email()),flag=1)
			var.put()
		else:
			k=x[0].key()
			obj=like.get(k)
			obj.flag=1
			obj.put()
		self.redirect("/viewit/"+ky)
class followit(webapp2.RequestHandler):
	def get(self,ky):
		self.redirect("/allcomplain")
	def post(self,ky):
		user=users.get_current_user()
		x=follow.all().filter('fuser =',str(user.email())).filter('fcomp =',str(ky))
		st=complain.all()
		for i in st:
			if str(i.key())==str(ky):
				obj=i
				break
		to_addr1=user.email()
		self.response.write(to_addr1)
		message = mail.EmailMessage(sender="Akash Agrawall <akash.wanted@gmail.com>",subject="Beheard")
		message.to = to_addr1
		message.body = """you are following the complaint %s""" % obj.desc
		message.send()

		self.response.write(to_addr1)
		message = mail.EmailMessage(sender="Akash Agrawall <akash.wanted@gmail.com>",subject="Beheard")
		message.to = obj.cuser.email()
		message.body = """The complaint has been followed by %s""" % user.email()
		message.send()

		if x.count()==0:
			var=follow(fcomp=str(ky),fuser=str(user.email()),status=1)
			var.put()
		else:
			k=x[0].key()
			obj=follow.get(k)
			obj.status=1
			obj.put()
		self.redirect("/allcomplain")
class followit1(webapp2.RequestHandler):
	def get(self,ky):
		self.redirect("/allcomplain")
	def post(self,ky):
		user=users.get_current_user()
		x=follow.all().filter('fuser =',str(user.email())).filter('fcomp =',str(ky))
		st=complain.all()
		for i in st:
			if str(i.key())==str(ky):
				obj=i
				break
#rst=recipient.all().filter("ruser =", user)
#		rbgroup=rst[0].bgroup
#		don=donor.all().filter("bgroup =",rbgroup)
#		for i in don:
#to_addr = self.request.get("friend_email")
		to_addr1=user.email()
		self.response.write(to_addr1)
		message = mail.EmailMessage(sender="Akash Agrawall <akash.wanted@gmail.com>",subject="Beheard")
		message.to = to_addr1
		message.body = """you are following the complaint %s""" % obj.desc
		message.send()

		self.response.write(to_addr1)
		message = mail.EmailMessage(sender="Akash Agrawall <akash.wanted@gmail.com>",subject="Beheard")
		message.to = obj.cuser.email()
		message.body = """The complaint has been followed by %s""" % user.email()
		message.send()

		if x.count()==0:
			var=follow(fcomp=str(ky),fuser=str(user.email()),status=1)
			var.put()
		else:
			k=x[0].key()
			obj=follow.get(k)
			obj.status=1
			obj.put()
		self.redirect("/mycomplain")
class followit2(webapp2.RequestHandler):
	def get(self,ky,flag):
		self.redirect("/category/"+flag)
	def post(self,ky,flag):
		user=users.get_current_user()
		x=follow.all().filter('fuser =',str(user.email())).filter('fcomp =',str(ky))
		st=complain.all()
		for i in st:
			if str(i.key())==str(ky):
				obj=i
				break
		to_addr1=user.email()
		self.response.write(to_addr1)
		message = mail.EmailMessage(sender="Akash Agrawall <akash.wanted@gmail.com>",subject="Beheard")
		message.to = to_addr1
		message.body = """you are following the complaint %s""" % obj.desc
		message.send()

		self.response.write(to_addr1)
		message = mail.EmailMessage(sender="Akash Agrawall <akash.wanted@gmail.com>",subject="Beheard")
		message.to = obj.cuser.email()
		message.body = """The complaint has been followed by %s""" % user.email()
		message.send()

		if x.count()==0:
			var=follow(fcomp=str(ky),fuser=str(user.email()),status=1)
			var.put()
		else:
			k=x[0].key()
			obj=follow.get(k)
			obj.status=1
			obj.put()
		self.redirect("/category/"+flag)
class followit3(webapp2.RequestHandler):
	def get(self,ky):
		self.redirect("/comp_follow")
	def post(self,ky):
		user=users.get_current_user()
		x=follow.all().filter('fuser =',str(user.email())).filter('fcomp =',str(ky))
		st=complain.all()
		for i in st:
			if str(i.key())==str(ky):
				obj=i
				break
		to_addr1=user.email()
		self.response.write(to_addr1)
		message = mail.EmailMessage(sender="Akash Agrawall <akash.wanted@gmail.com>",subject="Beheard")
		message.to = to_addr1
		message.body = """you are following the complaint %s""" % obj.desc
		message.send()

		self.response.write(to_addr1)
		message = mail.EmailMessage(sender="Akash Agrawall <akash.wanted@gmail.com>",subject="Beheard")
		message.to = obj.cuser.email()
		message.body = """The complaint has been followed by %s""" % user.email()
		message.send()

		if x.count()==0:
			var=follow(fcomp=str(ky),fuser=str(user.email()),status=1)
			var.put()
		else:
			k=x[0].key()
			obj=follow.get(k)
			obj.status=1
			obj.put()
		self.redirect("/comp_follow")
class followit4(webapp2.RequestHandler):
	def get(self,ky):
		self.redirect("/viewit/"+ky)
	def post(self,ky):
		user=users.get_current_user()
		x=follow.all().filter('fuser =',str(user.email())).filter('fcomp =',str(ky))
		st=complain.all()
		for i in st:
			if str(i.key())==str(ky):
				obj=i
				break
		to_addr1=user.email()
		self.response.write(to_addr1)
		message = mail.EmailMessage(sender="Akash Agrawall <akash.wanted@gmail.com>",subject="Beheard")
		message.to = to_addr1
		message.body = """you are following the complaint %s""" % obj.desc
		message.send()

		self.response.write(to_addr1)
		message = mail.EmailMessage(sender="Akash Agrawall <akash.wanted@gmail.com>",subject="Beheard")
		message.to = obj.cuser.email()
		message.body = """The complaint has been followed by %s""" % user.email()
		message.send()

		if x.count()==0:
			var=follow(fcomp=str(ky),fuser=str(user.email()),status=1)
			var.put()
		else:
			k=x[0].key()
			obj=follow.get(k)
			obj.status=1
			obj.put()
		self.redirect("/viewit/"+ky)
class unfollowit(webapp2.RequestHandler):
	def get(self,ky):
		self.redirect("/allcomplain")
	def post(self,ky):
		user=users.get_current_user()
		x=follow.all().filter('fuser =',str(user.email())).filter('fcomp =',str(ky))
		st=complain.all()
		for i in st:
			if str(i.key())==str(ky):
				obj=i
				break

		to_addr1=user.email()
		self.response.write(to_addr1)
		message = mail.EmailMessage(sender="Akash Agrawall <akash.wanted@gmail.com>",subject="Beheard")
		message.to = to_addr1
		message.body = """you have unfollowed the complaint %s""" % obj.desc
		message.send()

		self.response.write(to_addr1)
		message = mail.EmailMessage(sender="Akash Agrawall <akash.wanted@gmail.com>",subject="Beheard")
		message.to = obj.cuser.email()
		message.body = """your complaint with title %s has been unfollowed by %s""" %(obj.cname,user.email())
		message.send()
		if x.count()==0:
			var=follow(fcomp=str(ky),fuser=str(user.email()),status=2)
			var.put()
		else:
			k=x[0].key()
			obj=follow.get(k)
			obj.status=2
			obj.put()
		self.redirect("/allcomplain")
class unfollowit1(webapp2.RequestHandler):
	def get(self,ky):
		self.redirect("/mycomplain")
	def post(self,ky):
		user=users.get_current_user()
		x=follow.all().filter('fuser =',str(user.email())).filter('fcomp =',str(ky))
		st=complain.all()
		for i in st:
			if str(i.key())==str(ky):
				obj=i
				break
		to_addr1=user.email()
		self.response.write(to_addr1)
		message = mail.EmailMessage(sender="Akash Agrawall <akash.wanted@gmail.com>",subject="Beheard")
		message.to = to_addr1
		message.body = """you are unfollowing the complaint %s""" % obj.desc
		message.send()

		self.response.write(to_addr1)
		message = mail.EmailMessage(sender="Akash Agrawall <akash.wanted@gmail.com>",subject="Beheard")
		message.to = obj.cuser.email()
		message.body = """your complaint with title %s has been unfollowed by %s""" %(obj.cname,user.email())
		message.send()

		if x.count()==0:
			var=follow(fcomp=str(ky),fuser=str(user.email()),status=2)
			var.put()
		else:
			k=x[0].key()
			obj=follow.get(k)
			obj.status=2
			obj.put()
		self.redirect("/mycomplain")
class unfollowit2(webapp2.RequestHandler):
	def get(self,ky,flag):
		self.redirect("/category/"+flag)
	def post(self,ky,flag):
		user=users.get_current_user()
		x=follow.all().filter('fuser =',str(user.email())).filter('fcomp =',str(ky))
		st=complain.all()
		for i in st:
			if str(i.key())==str(ky):
				obj=i
				break
		to_addr1=user.email()
		self.response.write(to_addr1)
		message = mail.EmailMessage(sender="Akash Agrawall <akash.wanted@gmail.com>",subject="Beheard")
		message.to = to_addr1
		message.body = """you are following the complaint %s""" % obj.desc
		message.send()

		self.response.write(to_addr1)
		message = mail.EmailMessage(sender="Akash Agrawall <akash.wanted@gmail.com>",subject="Beheard")
		message.to = obj.cuser.email()
		message.body = """your complaint with title %s has been unfollowed by %s""" %(obj.cname,user.email())
		message.send()

		if x.count()==0:
			var=follow(fcomp=str(ky),fuser=str(user.email()),status=2)
			var.put()
		else:
			k=x[0].key()
			obj=follow.get(k)
			obj.status=2
			obj.put()
		self.redirect("/category/"+flag)
class unfollowit3(webapp2.RequestHandler):
	def get(self,ky):
		self.redirect("/category/"+flag)
	def post(self,ky):
		user=users.get_current_user()
		x=follow.all().filter('fuser =',str(user.email())).filter('fcomp =',str(ky))
		st=complain.all()
		for i in st:
			if str(i.key())==str(ky):
				obj=i
				break
		to_addr1=user.email()
		self.response.write(to_addr1)
		message = mail.EmailMessage(sender="Akash Agrawall <akash.wanted@gmail.com>",subject="Beheard")
		message.to = to_addr1
		message.body = """you are following the complaint %s""" % obj.desc
		message.send()

		self.response.write(to_addr1)
		message = mail.EmailMessage(sender="Akash Agrawall <akash.wanted@gmail.com>",subject="Beheard")
		message.to = obj.cuser.email()
		message.body = """your complaint with title %s has been unfollowed by %s""" %(obj.cname,user.email())
		message.send()
		if x.count()==0:
			var=follow(fcomp=str(ky),fuser=str(user.email()),status=2)
			var.put()
		else:
			k=x[0].key()
			obj=follow.get(k)
			obj.status=2
			obj.put()
		self.redirect("/comp_follow")
class unfollowit4(webapp2.RequestHandler):
	def get(self,ky):
		self.redirect("/viewit/"+ky)
	def post(self,ky):
		user=users.get_current_user()
		x=follow.all().filter('fuser =',str(user.email())).filter('fcomp =',str(ky))
		st=complain.all()
		for i in st:
			if str(i.key())==str(ky):
				obj=i
				break
		to_addr1=user.email()
		self.response.write(to_addr1)
		message = mail.EmailMessage(sender="Akash Agrawall <akash.wanted@gmail.com>",subject="Beheard")
		message.to = to_addr1
		message.body = """you are following the complaint %s""" % obj.desc
		message.send()

		self.response.write(to_addr1)
		message = mail.EmailMessage(sender="Akash Agrawall <akash.wanted@gmail.com>",subject="Beheard")
		message.to = obj.cuser.email()
		message.body = """your complaint with title %s has been unfollowed by %s""" %(obj.cname,user.email())
		message.send()
		if x.count()==0:
			var=follow(fcomp=str(ky),fuser=str(user.email()),status=2)
			var.put()
		else:
			k=x[0].key()
			obj=follow.get(k)
			obj.status=2
			obj.put()
		self.redirect("/viewit/"+ky)
class complain_accepted(webapp2.RequestHandler):
	def get(self):
		user=users.get_current_user()
		if user:
			template_values={}
	    		template=JINJA_ENVIRONMENT.get_template('html/complain_accepted.html')
			self.response.write(template.render(template_values))
		else:
			self.redirect(users.create_login_url(self.request.uri))
class viewit(webapp2.RequestHandler):
	def get(self,ky):
		user=users.get_current_user()
		if user:
			var=complain.all()
			likeit=like.all().filter('cid =',ky)
			cntlike=likeit.count()
			commentit=posts.all().filter('compid =',str(ky))
			for i in var:
				if str(i.key())==str(ky):
					obj=i
					break

			folfilter=follow.all().filter('fuser =',str(user.email())).filter('fcomp =',str(obj.key()))
			if folfilter.count()>0:
				if folfilter[0].status==1:
					followit=1
				else:
					followit=2
			else:
				followit=2
			y=like.all().filter('cid =',str(obj.key())).filter('flag =',1)
			x=like.all().filter('user =',str(user.email())).filter('cid =',str(obj.key()))
			numberit=[]
			numberit.append(y.count())
			if x.count()!=0 and x[0].flag == 1:
				likeit=1
			else:
				likeit=2
	    		template_values={'obj':obj, 'cntlike':cntlike, 'commentit':commentit, 'likeit':likeit, 'followit':followit, 'numberit':numberit}
	    		template=JINJA_ENVIRONMENT.get_template('html/viewit.html')
			self.response.write(template.render(template_values))
		else:
			self.redirect(users.create_login_url(self.request.uri))
class addcomment(webapp2.RequestHandler):
	def get(self,ky):
		self.response.out.write("asf")
	def post(self,ky):
		commentit=self.request.get('comment')
		user=users.get_current_user()
		if user:
			var=posts(puser=str(user.email()),compid=str(ky),comment=commentit)
			var.put()
		else:
			self.redirect(users.create_login_url(self.request.uri))
		self.redirect('/viewit/'+str(ky))
class dislike(webapp2.RequestHandler):
	def get(self,ky):
		self.redirect("/allcomplain")
	def post(self,ky):
		user=users.get_current_user()
		x=like.all().filter('user =',str(user.email())).filter('cid =',str(ky))
		if x.count()==0:
			var=like(cid=str(ky),user=str(user.email()),flag=2)
			var.put()
		else:
			k=x[0].key()
			obj=like.get(k)
			obj.flag=2
			obj.put()
		self.redirect("/allcomplain")
class dislike1(webapp2.RequestHandler):
	def get(self,ky):
		self.redirect("/mycomplain")
	def post(self,ky):
		user=users.get_current_user()
		x=like.all().filter('user =',str(user.email())).filter('cid =',str(ky))
		if x.count()==0:
			var=like(cid=str(ky),user=str(user.email()),flag=2)
			var.put()
		else:
			k=x[0].key()
			obj=like.get(k)
			obj.flag=2
			obj.put()
		self.redirect("/mycomplain")
class dislike2(webapp2.RequestHandler):
	def get(self,ky,fl):
		self.redirect("/category/"+fl)
	def post(self,ky,fl):
		user=users.get_current_user()
		x=like.all().filter('user =',str(user.email())).filter('cid =',str(ky))
		if x.count()==0:
			var=like(cid=str(ky),user=str(user.email()),flag=2)
			var.put()
		else:
			k=x[0].key()
			obj=like.get(k)
			obj.flag=2
			obj.put()
		self.redirect("/category/"+fl)
class dislike3(webapp2.RequestHandler):
	def get(self,ky):
		self.redirect("/comp_follow")
	def post(self,ky):
		user=users.get_current_user()
		x=like.all().filter('user =',str(user.email())).filter('cid =',str(ky))
		if x.count()==0:
			var=like(cid=str(ky),user=str(user.email()),flag=2)
			var.put()
		else:
			k=x[0].key()
			obj=like.get(k)
			obj.flag=2
			obj.put()
		self.redirect("/comp_follow")
class dislike4(webapp2.RequestHandler):
	def get(self,ky):
		self.redirect("/viewit/"+ky)
	def post(self,ky):
		user=users.get_current_user()
		x=like.all().filter('user =',str(user.email())).filter('cid =',str(ky))
		if x.count()==0:
			var=like(cid=str(ky),user=str(user.email()),flag=2)
			var.put()
		else:
			k=x[0].key()
			obj=like.get(k)
			obj.flag=2
			obj.put()
		self.redirect("/viewit/"+ky)
class complainit(webapp2.RequestHandler):
	def get(self):
		flag=0
		user = users.get_current_user()
		if user:
			result=complain.all().filter('cuser =',user)
#if result.count()>0:
#				flag=1
	    		template_values={'flag':flag,'result':result}
	    		template=JINJA_ENVIRONMENT.get_template('html/complainit.html')
			self.response.write(template.render(template_values))
		else:
			self.redirect(users.create_login_url(self.request.uri))
	def post(self):
		user=users.get_current_user()
		result=complain.all().filter('cuser =',user)
		v=str(self.request.get("lat"))
		l=str(self.request.get("long"))
		s=v+", "+l
		if self.request.get("img"):
			image=self.request.get("img")
		k=complain()
		if self.request.get("img"):
			k.image=db.Blob(image)
		k.cname=self.request.get("name")
		k.cuser=users.get_current_user()
		k.contact=self.request.get("phone")
		k.desc=self.request.get("description")
		k.address=self.request.get("address")
		p=list(self.request.get_all("mul"))
		st=''
		for i in p:
			st=st+i
			st=st+','
		k.mul=st
		k.coordinates=s
		k.put()
			#var=donor(dname=self.request.get("name"),image=db.Blob(image),duser=users.get_current_user(),bgroup=self.request.get("bgroup"),contact=self.request.get("phone"),address=self.request.get("address"),age=self.request.get("age"),coordinates=s)
			#var.put()
		self.redirect("/complain_accepted")
class comp_follow(webapp2.RequestHandler):
	def get(self):
		user = users.get_current_user()
		if user:
	  		logout=users.create_logout_url("/")
			result1=complain.all().filter('cuser =', user)
			result=[]
			for i in result1:
				findit=follow.all().filter('fcomp =', str(i.key()))
				if findit.count()>0:
					if findit[0].status==1:
						result.append(i)
			followit=[]
			likeit=[]
			numberit=[]
			email=user.email()
			for i in result:
				folfilter=follow.all().filter('fuser =',str(user.email())).filter('fcomp =',str(i.key()))
				if folfilter.count()>0:
					if folfilter[0].status==1:
						followit.append(1)
					else:
						followit.append(2)
				else:
					followit.append(2)
				y=like.all().filter('cid =',str(i.key())).filter('flag =',1)
				x=like.all().filter('user =',str(user.email())).filter('cid =',str(i.key()))
				numberit.append(y.count())
				if x.count()!=0 and x[0].flag == 1:
					likeit.append(1)
				else:
					likeit.append(0)
			flag=0
			template_values={'logout':logout,'flag':flag,'result':result, 'likeit':likeit, 'numberit':numberit, 'followit':followit, 'email':email}
	    		template=JINJA_ENVIRONMENT.get_template('html/comp_follow.html')
			self.response.write(template.render(template_values))
		else:
			self.redirect(users.create_login_url(self.request.uri))
class mycomplain(webapp2.RequestHandler):
	def get(self):
		likeit=[]
		numberit=[]
		flag=0
		user = users.get_current_user()
		if user:
			result=complain.all().filter('cuser =', user)
			followit=[]
			for i in result:
				folfilter=follow.all().filter('fuser =',str(user.email())).filter('fcomp =',str(i.key()))
				if folfilter.count()>0:
					if folfilter[0].status==1:
						followit.append(1)
					else:
						followit.append(2)
				else:
					followit.append(2)
				y=like.all().filter('cid =',str(i.key())).filter('flag =',1)
				x=like.all().filter('user =',str(user.email())).filter('cid =',str(i.key()))
				numberit.append(y.count())
				if x.count()!=0 and x[0].flag == 1:
					likeit.append(1)
				else:
					likeit.append(0)
			if result.count()>0:
				flag=1
	    		template_values={'flag':flag,'result':result, 'likeit':likeit, 'numberit':numberit, 'followit':followit}
	    		template=JINJA_ENVIRONMENT.get_template('html/mycomplain.html')
			self.response.write(template.render(template_values))
		else:
			self.redirect(users.create_login_url(self.request.uri))
class allcomplain(webapp2.RequestHandler):
	def get(self):
		likeit=[]
		numberit=[]
		flag=0
		user = users.get_current_user()
		if user:
			result=complain.all()
			followit=[]
			for i in result:
				folfilter=follow.all().filter('fuser =',str(user.email())).filter('fcomp =',str(i.key()))
				if folfilter.count()>0:
					if folfilter[0].status==1:
						followit.append(1)
					else:
						followit.append(2)
				else:
					followit.append(2)
				y=like.all().filter('cid =',str(i.key())).filter('flag =',1)
				x=like.all().filter('user =',str(user.email())).filter('cid =',str(i.key()))
				numberit.append(y.count())
				if x.count()!=0 and x[0].flag == 1:
					likeit.append(1)
				else:
					likeit.append(0)
			if result.count()>0:
				flag=1
	    		template_values={'flag':flag,'result':result, 'likeit':likeit, 'numberit':numberit, 'followit':followit}
	    		template=JINJA_ENVIRONMENT.get_template('html/allcomplain.html')
			self.response.write(template.render(template_values))
		else:
			self.redirect(users.create_login_url(self.request.uri))

class category(webapp2.RequestHandler):
	def get(self,fl):
		likeit=[]
		numberit=[]
		flag=0
		user = users.get_current_user()
		if user:
			result=complain.all()
			cat=['Water','Electricity','Transportation','Telecom','Sanitation']
			tofind=cat[int(fl)]
			displit=[]
			for i in result:
				splitit=i.mul.split(',')
				if tofind in splitit:
					displit.append(i)
					y=like.all().filter('cid =',str(i.key())).filter('flag =',1)
					x=like.all().filter('user =',str(user.email())).filter('cid =',str(i.key()))
					numberit.append(y.count())
					if x.count()!=0 and x[0].flag == 1:
						likeit.append(1)
					else:
						likeit.append(0)
			if result.count()>0:
				flag=1
			result=displit
			lat=[]
			lng=[]
			final=[]
			add=[]
			name=[]
			lis=[]
			if result:
				s=str(result[0].coordinates).split(",")
				lati=float(s[0])
				lon=float(s[1])
				addr=str(result[0].coordinates)
			else:
				lati=float(17.3660)
				lon=float(78.4760)
				addr="Hyderabad"
			for i in result:
				s=str(i.coordinates)
				l=s.split(",")
				lis.append(i.address)
				lis.append(i.contact)
				lis=[]
				lat.append(float(l[0]))
        	        	lat.append(float(l[1]))
				lat.append(str(i.cname))
				lat.append(str(i.address))
				lat.append(str(i.key()))
				final.append(lat)
				lat=[]
				add.append(i.address)
				name.append(add)
	    		template_values={'flag':flag,'result':result, 'likeit':likeit,'locate':addr,'latit':lati,'long':lon, 'numberit':numberit, 'fl':fl,'final':final}
	    		template=JINJA_ENVIRONMENT.get_template('html/category.html')
			self.response.write(template.render(template_values))
		else:
			self.redirect(users.create_login_url(self.request.uri))


class photoupload(blobstore_handlers.BlobstoreUploadHandler):
	def post(self):
	  try:
            upload = self.get_uploads()[0]
            user_photo = UserPhoto(user=users.get_current_user().user_id(),
                                   blob_key=upload.key())
            db.put(user_photo)

            self.redirect('/view_photo/%s' % upload.key())

          except:
            self.redirect('/html/upload_failure.html')
class map_donate(webapp2.RequestHandler):
	def get(self):
		user=users.get_current_user()
		q=donor.all().filter("duser = ", user)
		v=q[0].address
		template_values={'locate':v}
		template=JINJA_ENVIRONMENT.get_template('html/map_donate.html')
		self.response.write(template.render(template_values))
	def post(self):
		v=str(self.request.get("lat"))
		l=str(self.request.get("long"))
		user=users.get_current_user()
		k=donor.all().filter("duser = ", user)
		for i in k:
			i.coordinates=v+","+l
			i.put()
		self.redirect("/index")
class moveTo(webapp2.RequestHandler):
	def get(self):
		template_values={}
                template=JINJA_ENVIRONMENT.get_template('html/index.html')
                self.response.write(template.render(template_values))
	def post(self):
		q=db.GQLQuery('Select * from donor where duser= :1',users.get_current_user())
		s=str(self.request.get("latFld"))
		d=str(self.request.get("lngFld"))
		q['coordinate']=db.GeoPt(s,d)
class recieve_blood(webapp2.RequestHandler):
    	def get(self):
		user = users.get_current_user()
	        if user:
			self.redirect('/prinfo')
		else:
			self.redirect(users.create_login_url(self.request.uri))
	    	template_values={}
	    	template=JINJA_ENVIRONMENT.get_template('html/recieve_blood.html')
		self.response.write(template.render(template_values))
	def post(self):
		var=recipient(rname=self.request.get("name"),ruser=users.get_current_user(),bgroup=self.request.get("bgroup"),contact=self.request.get("phone"),address=self.request.get("address"))
		var.put()
		self.redirect("/map_view")

class prinfo(webapp2.RequestHandler):
	def get(self):
		flag=0
		user = users.get_current_user()
		if user:
			result=recipient.all().filter('ruser =',user)
			if result.count()>0:
				flag=1
	    		template_values={'flag':flag,'result':result}
	    		template=JINJA_ENVIRONMENT.get_template('html/prinfo.html')
			self.response.write(template.render(template_values))
		else:
			self.redirect(users.create_login_url(self.request.uri))
	def post(self):
		user=users.get_current_user()
		result=recipient.all().filter('ruser =',user)
		if result.count()>0:
			k=result[0].key()
			obj=recipient.get(k)
			obj.rname=self.request.get("name")
			obj.address=self.request.get("address")
			obj.contact=self.request.get("phone")
			obj.bgroup=self.request.get("bgroup")
			v=str(self.request.get("lat"))
             		l=str(self.request.get("long"))
			obj.coord=v+','+l
			obj.bunit=self.request.get('bunit')
			obj.put()
		else:
			v=str(self.request.get("lat"))
             		l=str(self.request.get("long"))
			var=recipient(rname=self.request.get("name"),ruser=users.get_current_user(),bdate=date.today(),bunit=self.request.get("bunit"),bgroup=self.request.get("bgroup"),contact=self.request.get("phone"),address=self.request.get("address"),coord=v+','+l)
			var.put()
		self.redirect("/show_donor")


class cinfo(webapp2.RequestHandler):
	def get(self):
		flag=0
		user=users.get_current_user()
		if user:		  
	  		logout=users.create_logout_url("/")
	    		template_values={}
	    		template=JINJA_ENVIRONMENT.get_template('html/cinfo.html')
			self.response.write(template.render(template_values))
	def post(self):
		v=str(self.request.get("lat"))
             	l=str(self.request.get("long"))
		s=v+','+l
		if self.request.get("img"):
			post=self.request.get("img")
		k=camp()
		if self.request.get("img"):
			k.poster=db.Blob(post)
		k.cname=self.request.get("name")
		k.cuser=users.get_current_user()
		k.sdate=self.request.get("sdate")
		k.edate=self.request.get("edate")
		k.contact=self.request.get("phone")
		k.contact=self.request.get("address")
		k.coord=s
		k.put()
		#var=camp(cname=self.request.get("name"),cuser=users.get_current_user(),sdate=self.request.get("sdate"),edate=self.request.get("edate"),contact=self.request.get("phone"),address=self.request.get("address"),coord=v+','+l)
		#var.put()
		self.redirect("/organise")

class send_mail(webapp2.RequestHandler):
	def post(self):
		user=users.get_current_user()
		rst=recipient.all().filter("ruser =", user)
		rbgroup=rst[0].bgroup
		don=donor.all().filter("bgroup =",rbgroup)
		for i in don:
#to_addr = self.request.get("friend_email")	
			to_addr=i.duser.email()
			self.response.write(to_addr)
			message = mail.EmailMessage()
			message.sender = user.email()
			message.to = to_addr
			message.body = """You can save many lives : this user needs this units of blood dated on this please help him by donating the blood """ 
			message.send()
		self.redirect("/view_mail")
class view_mail(webapp2.RequestHandler):
	def get(self):

		logout=users.create_logout_url("/")
	    	template_values={'logout':logout}
	    	template=JINJA_ENVIRONMENT.get_template('html/send_mail.html')
		self.response.write(template.render(template_values))		
class hero(webapp2.RequestHandler):
	def get(self):
		don=donor.all()
		#posts = db.GqlQuery("select * from donor")
		#account_key=self.request.get('key')
		#account = db.get(account_key)
    		#if account.profile_pic:
       	#		self.response.headers['Content-Type'] = "image/png"
      	#		self.response.out.write(account.profile_pic)
    	#	else:
       	#		self.error(404)

		logout=users.create_logout_url("/")
	    	template_values={'logout':logout,'posts':posts}
	    	template=JINJA_ENVIRONMENT.get_template('html/hero.html')
		self.response.write(template.render(template_values))		
class imagehandler(webapp2.RequestHandler):
	def get(self):
                account_key=self.request.get('key')
                account = db.get(account_key)
                if account.image:
                        self.response.headers['Content-Type'] = "image/jpg"
                        self.response.out.write(account.image)
                else:
                        self.error(404)

class ima(webapp2.RequestHandler):
	def get(self):
		don=donor.all()
	        template_values={'don':don}
		template=JINJA_ENVIRONMENT.get_template('html/ima.html')
                self.response.write(template.render(template_values))
class view_request(webapp2.RequestHandler):
	def get(self,param1):
		p=param1
		value=None
		rec=recipient.all()
		for i in rec:
			if str(i.key())==str(param1):
				value=i
				break
		logout=users.create_logout_url("/")
	    	template_values={'value':value,'p':p,'param1':param1,'logout':logout}
	    	template=JINJA_ENVIRONMENT.get_template('html/view_request.html')
		self.response.write(template.render(template_values))		

class camps_detail(webapp2.RequestHandler):
    	def get(self):
	    user=users.get_current_user()
	    if user:
	    	result=camp.all()
	    	li=link.all()
	    	having=[]
	    	rest=[]
		logout=users.create_logout_url("/")
	    	for i in result:
	    		fl=0
	    		for j in li:
	    			if str(i.key())==str(j.cid) and j.guser==user.email() and j.flag==1:
	    				having.append(i)
	    				fl=1
	    				break
	    		if fl==0:
	    			rest.append(i)		
	    	template_values={'having':having,'rest':rest,'user':user,'logout':logout}
	    	template=JINJA_ENVIRONMENT.get_template('html/camps_detail.html')
	    	self.response.write(template.render(template_values))		
    	    else:
			self.redirect(users.create_login_url(self.request.uri))

class camp_post(webapp2.RequestHandler):
	def get(self,camp_id):
	    name=camp.all()
	    for i in name:
		if str(i.key())==str(camp_id):
			cur_camp=i		
	    user=users.get_current_user()
	    post=posts.all().filter("campid = ",str(camp_id))
	    template_values={'post':post,'cuser':user,'cur_camp':cur_camp}
	    template=JINJA_ENVIRONMENT.get_template('html/camp_post.html')
	    self.response.write(template.render(template_values))			    
	def post(self,camp_id):
	    user=users.get_current_user()
	    var=posts(campid=str(camp_id),puser=user,comment=self.request.get("comment"))
	    var.put()
	    self.redirect('/camp_post/'+camp_id)
class map_view(webapp2.RequestHandler):
    	def get(self):
		user=users.get_current_user()
		q=recipient.all().filter("ruser = ", user)
		v=q[0].address
		template_values={'locate':v}
		template=JINJA_ENVIRONMENT.get_template('html/map_view.html')
		self.response.write(template.render(template_values))
	def post(self):
		v=str(self.request.get("lat"))
		l=str(self.request.get("long"))
		user=users.get_current_user()
		k=recipient.all().filter("ruser = ", user)
		for i in k:
			i.coord=v+","+l
			i.put()
		self.redirect("/show_donor")

class recipient_request(webapp2.RequestHandler):
	def get(self):
		user=users.get_current_user()
		if user:	
			logout=users.create_logout_url("/")
			r=recipient.all()
	    		template_values={'r':r,'user':user,'logout':logout}
	    		template=JINJA_ENVIRONMENT.get_template('html/recipient_request.html')
			self.response.write(template.render(template_values))		
    		else:
			self.redirect(users.create_login_url(self.request.uri))
class add_notification(webapp2.RequestHandler):
	def get(self,rec_id):
		user=users.get_current_user()
		var=notification(did=user,rid=str(rec_id),flag=0)
		var.put()
		self.redirect("/hero")
class show_notification(webapp2.RequestHandler):
	def get(self,get_key):	
		user=users.get_current_user()
		notify=notification.all()
		request=[]
		for i in notify:
			if str(i.key())==str(get_key):
				request.append(i)
	    	template_values={'request':request}
	    	template=JINJA_ENVIRONMENT.get_template('html/show_notification.html')
		self.response.write(template.render(template_values))		
class pop(webapp2.RequestHandler):
	def get(self):
	    	template_values={}
	    	template=JINJA_ENVIRONMENT.get_template('html/pop.html')
		self.response.write(template.render(template_values))		
class show_donor(webapp2.RequestHandler):
	def get(self):
		user=users.get_current_user()
		k=recipient.all().filter("ruser = ",user)
		q=donor.all().filter("bgroup = ", k[0].bgroup)
		r=str(k[0].coord)
		r=r.split(",")
		a={}
		lat=[]
		lng=[]
		final=[]
		add=[]
		name=[]
		lis=[]
		for i in q:
			s=str(i.coordinates)
			l=s.split(",")
			lis.append(distance_between_points(float(l[0]),float(l[1]),float(r[0]),float(r[1])))
			lis.append(i.address)
			lis.append(i.contact)
			a[i.dname]=lis
			lis=[]
			lat.append(i.dname)
			lat.append(float(l[0]))	
			lat.append(float(l[1]))
			lat.append(str(i.key()))
			final.append(lat)
			lat=[]
			add.append(i.address)
			add.append(i.dname)
			name.append(add)
			add=[]
		sorted(a.values())

		logout=users.create_logout_url("/")
		template_values={'locate':k[0].address,'vivek':a,'final':json.dumps(final),'long':float(r[1]),'latit':float(r[0]),'name':name,'a':a,'logout':logout,'q':q}
		template=JINJA_ENVIRONMENT.get_template('html/show_donor.html')
		self.response.write(template.render(template_values))
		'''v=self.request.get("location")
	    	template_values={'locate':v}
	    	template=JINJA_ENVIRONMENT.get_template('map_view.html')
		self.response.write(template.render(template_values))'''
import datetime
class todaycamp(webapp2.RequestHandler):
	def get(self):
		user=users.get_current_user()
		today=datetime.date.today()
		f=today.strftime('%d %B, %Y')
		b=''
		fl=1
		if f[0]=='0':
			fl=0
			for i in range(0,len(f)):
				if i!=0:
					b+=f[i]
		
		k=camp.all()
		ans=[]
		for i in k:
			if fl==0:
				if b[2]=='J':
					if b[3]=='a':
						ms=1
					if b[3]=='u':
						if b[4]=='n':
							ms=6
						if b[4]=='l':
							ms=7
				elif b[2]=='F':
					ms=2
				elif b[2]=='M':
					if b[4]=='y':
						ms=5
					elif b[4]=='r':
						ms=3
				elif b[2]=='A':
					if b[3]=='p':
						ms=4
					elif b[3]=='u':
						ms=8
				elif b[2]=='S':
					ms=9
				elif b[2]=='O':
					ms=10
				elif b[2]=='N':
					ms=11
				elif b[2]=='D':
					ms=12
			else:
				if b[3]=='J':
					if b[4]=='a':
						ms=1
					if b[4]=='u':
						if b[5]=='n':
							ms=6
						if b[5]=='l':
							ms=7
				elif b[3]=='F':
					ms=2
				elif b[3]=='M':
					if b[5]=='y':
						ms=5
					elif b[5]=='r':
						ms=3
				elif b[3]=='A':
					if b[4]=='p':
						ms=4
					elif b[4]=='u':
						ms=8
				elif b[3]=='S':
					ms=9
				elif b[3]=='O':
					ms=10
				elif b[3]=='N':
					ms=11
				elif b[3]=='D':
					ms=12
			if i.sdate[1]==' ':
				if i.sdate[2]=='J':
					if i.sdate[3]=='a':
						mss=1
					if i.sdate[3]=='u':
						if i.sdate[4]=='n':
							mss=6
						if i.sdate[4]=='l':
							mss=7
				elif i.sdate[2]=='F':
					mss=2
				elif i.sdate[2]=='M':
					if i.sdate[4]=='y':
						mss=5
					elif i.sdate[4]=='r':
						mss=3
				elif i.sdate[2]=='A':
					if i.sdate[3]=='p':
						mss=4
					elif i.sdate[3]=='u':
						mss=8
				elif i.sdate[2]=='S':
					mss=9
				elif i.sdate[2]=='O':
					mss=10
				elif i.sdate[2]=='N':
					mss=11
				elif i.sdate[2]=='D':
					mss=12
			else:
				if i.sdate[3]=='J':
					if i.sdate[4]=='a':
						mss=1
					if i.sdate[4]=='u':
						if i.sdate[5]=='n':
							mss=6
						if i.sdate[5]=='l':
							mss=7
				elif i.sdate[3]=='F':
					mss=2
				elif i.sdate[3]=='M':
					if i.sdate[5]=='y':
						mss=5
					elif i.sdate[5]=='r':
						mss=3
				elif i.sdate[3]=='A':
					if i.sdate[4]=='p':
						mss=4
					elif i.sdate[4]=='u':
						mss=8
				elif i.sdate[3]=='S':
					mss=9
				elif i.sdate[3]=='O':
					mss=10
				elif i.sdate[3]=='N':
					mss=11
				elif i.sdate[3]=='D':
					mss=12
			if i.edate[1]==' ':
				if i.edate[2]=='J':
					if i.edate[3]=='a':
						me=1
					if i.edate[3]=='u':
						if i.edate[4]=='n':
							me=6
						if i.edate[4]=='l':
							me=7
				elif i.edate[2]=='F':
					me=2
				elif i.edate[2]=='M':
					if i.edate[4]=='y':
						me=5
					elif i.edate[4]=='r':
						me=3
				elif i.edate[2]=='A':
					if i.edate[3]=='p':
						me=4
					elif i.edate[3]=='u':
						me=8
				elif i.edate[2]=='S':
					me=9
				elif i.edate[2]=='O':
					me=10
				elif i.edate[2]=='N':
					me=11
				elif i.edate[2]=='D':
					me=12
			else:
				if i.edate[3]=='J':
					if i.edate[4]=='a':
						me=1
					if i.edate[4]=='u':
						if i.edate[5]=='n':
							me=6
						if i.edate[5]=='l':
							me=7
				elif i.edate[3]=='F':
					me=2
				elif i.edate[3]=='M':
					if i.edate[5]=='y':
						me=5
					elif i.edate[5]=='r':
						me=3
				elif i.edate[3]=='A':
					if i.edate[4]=='p':
						me=4
					elif i.edate[4]=='u':
						me=8
				elif i.edate[3]=='S':
					me=9
				elif i.edate[3]=='O':
					me=10
				elif i.edate[3]=='N':
					me=11
				elif i.edate[3]=='D':
					me=12
			if fl==0:
				if ms>=mss and ms<=me:
					if i.sdate[1]!=' ' and i.edate[1]!=' ':
						if int(i.sdate[0]*10+i.sdate[1])<=int(b[0]) and int(i.edate[0]*10+i.edate[1])>=int(b[0]):
							ans.append(i)
					elif i.sdate[1]==' ' and i.edate[1]!=' ':
						if int(i.sdate[0])<=int(b[0]) and int(i.edate[0]*10+i.edate[1])>=int(b[0]):
							ans.append(i)
					elif i.sdate[1]==' ' and i.edate[1]==' ':
						if i.sdate[0]<=b[0] and i.edate[0]>=b[0]:
							ans.append(i)
			elif fl==1:
				if ms>=mss and ms<=me:
					if i.sdate[1]!=' ' and i.edate[1]!=' ':
						if i.sdate[0]*10+i.sdate[1]<=b[0]*10+b[1] and i.edate[0]*10+i.edate[1]>=b[0]*10+b[1]:
							ans.append(i)
					elif i.sdate[1]==' ' and i.edate[1]!=' ':
						if i.sdate[0]<=b[0]*10+b[1] and i.edate[0]*10+i.edate[1]>=b[0]*10+b[2]:
							ans.append(i)
					elif i.sdate[1]==' ' and i.edate[1]==' ':
						if i.sdate[0]<=b[0]*10+b[1] and i.edate[0]>=b[0]*10+b[1]:
							ans.append(i)

		lat=[]
		lng=[]
		final=[]
		add=[]
		name=[]
		lis=[]

		for i in ans:
			s=str(i.coord)
			l=s.split(",")
			lis.append(i.address)
			lis.append(i.contact)
			lis=[]
			lat.append(float(l[0]))
                        lat.append(float(l[1]))
			lat.append(i.cname)
			lat.append(i.address)
			lat.append(i.sdate)
			lat.append(i.edate)
			lat.append(str(i.key()))
			final.append(lat)
			lat=[]
			add.append(i.address)
			name.append(add)
			add=[]
		logout=users.create_logout_url("/")
		template_values={'final':json.dumps(final),'logout':logout}
		template=JINJA_ENVIRONMENT.get_template('html/todaycamp.html')
		self.response.write(template.render(template_values))
		
class going_event(webapp2.RequestHandler):
    	def get(self,camp_id):
	    user=users.get_current_user()
	    var=link(cid=str(camp_id),guser=str(user.email()),flag=1)
	    var.put()
	    c_all=camp.all()
	    for i in c_all:
			if str(i.key())==camp_id:
				camp_name=i.cname
				ad=i.address
				st=i.sdate
				et=i.edate
	    s=st.split(",")
	    l=s[0].split()
	    start=""
	
	    if l[1]=="November":
		start+=s[1][1:]+"-"+"11-"+l[0]
	    if l[1]=="December":
		start+=s[1][1:]+"-"+"12-"+l[0]
	    
	    if l[1]=="January":
		start+=s[1][1:]+"-"+"1-"+l[0]
	    if l[1]=="February":
		start+=s[1][1:]+"-"+"2-"+l[0]
	    if l[1]=="March":
		start+=s[1][1:]+"-"+"3-"+l[0]
	    if l[1]=="April":
		start+=s[1][1:]+"-"+"4-"+l[0]
	    if l[1]=="May":
		start+=s[1][1:]+"-"+"5-"+l[0]
	    if l[1]=="June":
		start+=s[1][1:]+"-"+"6-"+l[0]

	    if l[1]=="July":
		start+=s[1][1:]+"-"+"7-"+l[0]
	    if l[1]=="August":
		start+=s[1][1:]+"-"+"8-"+l[0]
	    if l[1]=="September":
		start+=s[1][1:]+"-"+"9-"+l[0]
	
	    if l[1]=="October":
		start+=s[1][1:]+"-"+"10-"+l[0]
	    fs=start
	    s=et.split(",")
	    l=s[0].split()
	    start=""
	    if l[1]=="November":
		start+=s[1][1:]+"-"+"11-"+l[0]
	    if l[1]=="December":
		start+=s[1][1:]+"-"+"12-"+l[0]
	    
	    if l[1]=="January":
		start+=s[1][1:]+"-"+"1-"+l[0]
	    if l[1]=="February":
		start+=s[1][1:]+"-"+"2-"+l[0]
	    if l[1]=="March":
		start+=s[1][1:]+"-"+"3-"+l[0]
	    if l[1]=="April":
		start+=s[1][1:]+"-"+"4-"+l[0]
	    if l[1]=="May":
		start+=s[1][1:]+"-"+"5-"+l[0]
	    if l[1]=="June":
		start+=s[1][1:]+"-"+"6-"+l[0]

	    if l[1]=="July":
		start+=s[1][1:]+"-"+"7-"+l[0]
	    if l[1]=="August":
		start+=s[1][1:]+"-"+"8-"+l[0]
	    if l[1]=="September":
		start+=s[1][1:]+"-"+"9-"+l[0]
	
	    if l[1]=="October":
		start+=s[1][1:]+"-"+"10-"+l[0]

	    fe=start

            logout=users.create_logout_url("/")
	    template_values={'user':user,'camp_user':camp_name,'address':ad,'start':fs,'end':fe,'logout':logout}
	    template=JINJA_ENVIRONMENT.get_template('html/going_event.html')
	    self.response.write(template.render(template_values))	
	    
class coming_donors(webapp2.RequestHandler):
    	def get(self,camp_key):
	    logout=users.create_logout_url("/")
	    user=users.get_current_user()
	    notify=notification.all().filter("rid = ",str(user)).filter("flag = ",0)
	    request=[]
	    for i in notify:
				request.append(i)
	    donr=link.all().filter("cid = ",str(camp_key))	     
	    self.response.write(donr)
	    out="Name	Email	Contact     Address "
	    don=donor.all()
	    a=[]
	    empty=[]
	    for i in donr:
		fl=0
	    	for j in don:
	 		st=str(j.duser.email())
			if st==str(i.guser):
				fl=1
				out+=(str(j.dname)+str(st)+str(j.contact)+str(j.address))
				a.append(j)                                                     
				break
		if fl==0:
		  	empty.append(str(i.guser))
			out+=("--"+"--"+"-----"+"--------"+str(i.guser))
	    template_values={'donor':donr,'out':out,'logout':logout,'a':a,'request':request,'empty':empty}
	    template=JINJA_ENVIRONMENT.get_template('html/coming_donors.html')
	    self.response.write(template.render(template_values))	
class final_receive(webapp2.RequestHandler):
	def get(self):
		logout=users.create_logout_url("/")
	    	template_values={'logout':logout}
	    	template=JINJA_ENVIRONMENT.get_template('html/final_receive.html')
		self.response.write(template.render(template_values))		
class about(webapp2.RequestHandler):
	def get(self):
		logout=users.create_logout_url("/")
	    	template_values={'logout':logout}
	    	template=JINJA_ENVIRONMENT.get_template('html/about.html')
		self.response.write(template.render(template_values))		
class contact(webapp2.RequestHandler):
	def get(self):
		logout=users.create_logout_url("/")
	    	template_values={'logout':logout}
	    	template=JINJA_ENVIRONMENT.get_template('html/contact.html')
		self.response.write(template.render(template_values))		
class organise(webapp2.RequestHandler):
	def get(self):
		logout=users.create_logout_url("/")
		user=users.get_current_user()
		camps=camp.all()
		ky=None
		flag=0
		camp_keys={}
		for i in camps:
			if str(i.cuser.email())==str(user.email()):
				ky=i.key()
				q=link.all().filter("cid = ",str(ky))
				camp_keys[str(i.cname)]=(str(ky))
				if q.count()!=0:
					flag=1
	    	template_values={'logout':logout,'flag':flag,'camp_keys':camp_keys}
	    	template=JINJA_ENVIRONMENT.get_template('html/organise.html')
		self.response.write(template.render(template_values))		

class about1(webapp2.RequestHandler):
	def get(self):
		login=users.create_login_url("/index")
	    	template_values={'login':login}
	    	template=JINJA_ENVIRONMENT.get_template('html/about1.html')
		self.response.write(template.render(template_values))		
class contact1(webapp2.RequestHandler):
	def get(self):
		login=users.create_login_url("/index")
	    	template_values={'login':login}
	    	template=JINJA_ENVIRONMENT.get_template('html/contact1.html')
		self.response.write(template.render(template_values))		
			
class gplus(webapp2.RequestHandler):
	def get(self):
	    	template_values={}
	    	template=JINJA_ENVIRONMENT.get_template('html/gplus.html')
		self.response.write(template.render(template_values))		
	def post(self):
		'''if request.args.get('state', '') != session['state']:
		     response = make_response(json.dumps('Invalid state parameter.'), 401)
		     response.headers['Content-Type'] = 'application/json'
		     self.response.write(response)
 		gplus_id = request.args.get('gplus_id')
		code = request.data
	
		try:
		    # Upgrade the authorization code into a credentials object
    		 	oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
		 	oauth_flow.redirect_uri = 'postmessage'
    		 	credentials = oauth_flow.step2_exchange(code)
  		except FlowExchangeError:
    			response = make_response(
        		json.dumps('Failed to upgrade the authorization code.'), 401)
    			response.headers['Content-Type'] = 'application/json'
    			return response
  # Check that the access token is valid.
  		access_token = credentials.access_token
  		url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
        		 % access_token)
  		h = httplib2.Http()
  		result = json.loads(h.request(url, 'GET')[1])
  # If there was an error in the access token info, abort.
  		if result.get('error') is not None:
    			response = make_response(json.dumps(result.get('error')), 500)
    			response.headers['Content-Type'] = 'application/json'
    			return response
  # Verify that the access token is used for the intended user.
  		if result['user_id'] != gplus_id:
    			response = make_response(
        			json.dumps("Token's user ID doesn't match given user ID."), 401)
    			response.headers['Content-Type'] = 'application/json'
    			return response
  # Verify that the access token is valid for this app.
  		if result['issued_to'] != CLIENT_ID:
    			response = make_response(
      			  json.dumps("Token's client ID does not match app's."), 401)
    			response.headers['Content-Type'] = 'application/json'
    			return response
  		stored_credentials = session.get('credentials')
  		stored_gplus_id = session.get('gplus_id')
  		if stored_credentials is not None and gplus_id == stored_gplus_id:
    			response = make_response(json.dumps('Current user is already connected.'),
                             200)
    			response.headers['Content-Type'] = 'application/json'
    		i	return response
  # Store the access token in the session for later use.
  		session['credentials'] = credentials
  		session['gplus_id'] = gplus_id
  		response = make_response(json.dumps('Successfully connected user.', 200))'''
class imagehandler2(webapp2.RequestHandler):
	def get(self):
                account_key=self.request.get('key')
                account = db.get(account_key)
                if account.image:
                        self.response.headers['Content-Type'] = "pic/jpg"
                        self.response.out.write(account.image)
                else:
                        self.error(404)
class imagehandler3(webapp2.RequestHandler):
        def get(self):
                account_key=self.request.get('key')
                account = db.get(account_key)
                if account.poster:
                        self.response.headers['Content-Type'] = "pic/jpg"
                        self.response.out.write(account.poster)
                else:
                        self.error(404)
class share(webapp2.RequestHandler):
	def get(self):
	    	user=users.get_current_user()		
		pstories=story.all().filter("suser =",user)
	    	template_values={'pstories':pstories}
	    	template=JINJA_ENVIRONMENT.get_template('html/share.html')
		self.response.write(template.render(template_values))			
class putstory(webapp2.RequestHandler):
	def get(self):
	    	template_values={}
	    	template=JINJA_ENVIRONMENT.get_template('html/putstory.html')
		self.response.write(template.render(template_values))			
	def post(self):
	    	user=users.get_current_user()
		if self.request.get("img"):
			image=self.request.get("img")
		k=story()
		k.story=self.request.get("story")		
		k.tag=self.request.get("tag")		
		k.suser=user
		if self.request.get("img"):
			k.pic=db.Blob(image)
		k.put()		
		#var=story(story=self.request.get("story"),tag=self.request.get("tag"),suser=user)
		#var.put()
		self.redirect("/share")
class stry(webapp2.RequestHandler):
	def get(self):
		all_story=story.all()
	    	template_values={'stories':all_story}
	    	template=JINJA_ENVIRONMENT.get_template('html/stry.html')
		self.response.write(template.render(template_values))			
class copy(webapp2.RequestHandler):
	def get(self):
	    	template_values={}
	    	template=JINJA_ENVIRONMENT.get_template('html/copy.html')
		self.response.write(template.render(template_values))			

class faq(webapp2.RequestHandler):
	def get(self):
		user=users.get_current_user()
		notify=notification.all().filter("rid = ",str(user)).filter("flag = ",0)
		request=[]
		for i in notify:
				request.append(i)
		lngth=len(request)
	    	template_values={'notify':notify,'lngth':lngth}
	    	template=JINJA_ENVIRONMENT.get_template('html/faq.html')
		self.response.write(template.render(template_values))			
class feedback(webapp2.RequestHandler):
	def get(self):
		user=users.get_current_user()
		notify=notification.all().filter("rid = ",str(user)).filter("flag = ",0)
		request=[]
		for i in notify:
				request.append(i)
		lngth=len(request)
	    	template_values={'notify':notify,'lngth':lngth}
	    	template=JINJA_ENVIRONMENT.get_template('html/feedback.html')
		self.response.write(template.render(template_values))			

application=webapp2.WSGIApplication([
	                ("/",main),
	                ("/index",index),
			("/complainit",complainit),
			("/complain_accepted",complain_accepted),
			("/addcomment/(\S+)",addcomment),
			("/liked/(\S+)",liked),
			("/liked1/(\S+)",liked1),
			("/liked2/(\S+)/(\S+)",liked2),
			("/liked3/(\S+)",liked3),
			("/liked4/(\S+)",liked4),
			("/followit/(\S+)",followit),
			("/followit1/(\S+)",followit1),
			("/followit2/(\S+)",followit2),
			("/followit3/(\S+)",followit3),
			("/followit4/(\S+)",followit4),
			("/unfollowit/(\S+)",unfollowit),
			("/unfollowit1/(\S+)",unfollowit1),
			("/unfollowit2/(\S+)",unfollowit2),
			("/unfollowit3/(\S+)",unfollowit3),
			("/unfollowit4/(\S+)",unfollowit4),
			("/viewit/(\S+)",viewit),
			("/dislike/(\S+)",dislike),
			("/dislike1/(\S+)",dislike1),
			("/dislike2/(\S+)/(\S+)",dislike2),
			("/dislike3/(\S+)",dislike3),
			("/dislike4/(\S+)",dislike4),
			("/mycomplain",mycomplain),
			("/allcomplain",allcomplain),
			("/category/(\S+)",category),
			("/comp_follow",comp_follow),
			("/comp_loc",comp_loc),
	                ("/feedback",feedback),
	                ("/donate_blood",donate_blood),
	                ("/recieve_blood",recieve_blood),
	                ("/map_view",map_view),
			("/map_donate",map_donate),
			("/moveTo",moveTo),
			("/show_donor",show_donor),
			("/prinfo",prinfo),
			("/cinfo",cinfo),
			("/stry",stry),
			("/add_notification/(\S+)",add_notification),
			("/send_mail",send_mail),
			("/view_mail",view_mail),
			("/viewit",viewit),
			("/recipient_request",recipient_request),
			("/view_request/(\S+)",view_request),
			("/camps_detail",camps_detail),
			("/camp_post/(\S+)",camp_post),
			("/upload_photo",photoupload),
			("/final_receive",final_receive),
			("/copy",copy),
			#("/going_event/(\w+@\w+\.\w+)",going_event),
			("/going_event/(\S+)",going_event),
			("/about",about),
			("/contact",contact),
			("/coming_donors/(\S+)",coming_donors),
			("/putstory",putstory),
			("/about1",about1),
			("/contact1",contact1),
			("/share",share),
			("/faq",faq),
			("/putstory",putstory),
			("/show_notification/(\S+)",show_notification),
			("/hero",hero),
			("/pop",pop),
			("/organise",organise),
			("/gplus",gplus),
			("/ima",ima),
			("/imagehandler",imagehandler),
			("/imagehandler2",imagehandler2),
			("/imagehandler3",imagehandler3),
			("/todaycamp",todaycamp)
],debug=True)

