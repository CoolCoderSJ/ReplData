import web
import os
import sqlite3
from replit import db
import requests
import json
import ast

render = web.template.render('templates/')

urls = (
	'/', 'index',
	'/login', 'login',
	'/signup', 'signup',
	'/repl/(.*)', 'show',
	'/api', 'api',
	'/account', 'account',
	'/apidoc', 'apidoc',
	'/delete', 'delete'
)


app = web.application(urls, locals())

class apidoc:
	def GET(self):
		return render.api()

class index:
	def GET(self):
		if web.cookies().get("user"):
			raise web.seeother('/account')
		else:
			return render.promo()

class login:
	def GET(self):
		if not web.cookies().get("user"):
			i = web.input(code=0)
			msg = ""
			if i.code == "1":
				msg = "Either the username or password is incorrect."
			elif i.code == "2":
				msg = "This account does not exist."
			return render.login(msg)
		else:
			raise web.seeother('/')
	def POST(self):
		i = web.input()
		r = requests.post("https://SJAUTH.coolcodersj.repl.co/apil", data={"user": i.user, "passw": i.passw})
		if r.text == "Wrong auth":
			raise web.seeother("/login?code=1")
		elif r.text == "Does not exist":
			raise web.seeother("/login?code=2")
		else:
			web.setcookie("user", i.user)
			raise web.seeother('/')

def tokenate():
	import hashlib, random

	def generate():
		letters = ["a","b",	"c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"]
		token2 = ""
		for x in range(15):
			token2 += random.choice(letters)

		token = token2.encode(encoding="utf-8")
		hash_object = hashlib.sha256(token)
		token = hash_object.hexdigest()
		return token

	def check(token):
		conn = sqlite3.connect("database.db")
		db2 = conn.cursor()
		tokens = db2.execute("SELECT token from users").fetchall()
		if token not in tokens:
			return True
		else:
			token = generate()
			check(token)


	token = generate()
	if check(token) is True:
		return token

class signup:
	def GET(self):
		if not web.cookies().get("user"):
			i = web.input(code=0)
			msg = ""
			if i.code == "1":
				msg = "This account already exists. Please visit the login page to login."
			return render.signup(msg)
		else:
			raise web.seeother('/')
	def POST(self):
		i = web.input()
		r = requests.post("https://SJAUTH.coolcodersj.repl.co/apisi", data={"user": i.user, "passw": i.passw})
		if r.text == "Exists":
			raise web.seeother("/signup?code=1")
		else:
			web.setcookie("user", i.user)
			conn = sqlite3.connect("database.db")
			db2 = conn.cursor()
			TOKEN = tokenate()
			db2.execute(f"INSERT into users (user, token) VALUES ('{i.user}', '{TOKEN}')")
			conn.commit()
			db2.close()
			raise web.seeother('/account')
			


class account:
	def GET(self):
		i=web.input(code=0)
		code = i.code
		if code == 0:
			msg = ""
		elif code == "1":
			msg = "Success! Visit <code>https://ReplData.coolcodersj.repl.co/repl/REPLDATA_REPL_ID</code> to track it, or see <code>https://ReplData.coolcodersj.repl.co/apidoc</code> to find instructions for adding the tracking code."
		if web.cookies().get("user"):
			user = web.cookies().get("user")
			conn = sqlite3.connect("database.db")
			db2 = conn.cursor()
			tokenlist = db2.execute(f"SELECT token from users WHERE user = '{user}'").fetchall()
			token = tokenlist[0][0]
			try:
				repllist = db2.execute(f"SELECT * from repls WHERE token = '{token}'").fetchall()
			except:
				repllist = []
			names = []
			if repllist != []:
				for repl in repllist:
					names.append([repl[3], repl[0]])
			return render.account(user, token, len(repllist), names, msg)
		else:
			raise web.seeother('/login')
	def POST(self):
		i = web.input()
		user = web.cookies().get("user")
		conn = sqlite3.connect("database.db")
		db2 = conn.cursor()
		tokenlist = db2.execute(f"SELECT token from users WHERE user = '{user}'").fetchall()
		token = tokenlist[0][0]
		db2.execute(f"INSERT into repls (token, users, name) VALUES ('{token}', '[]', '{i.name}')")
		conn.commit()
		raise web.seeother("/account?code=1")

class api:
	def GET(self):
		i = web.input()
		if "TOKEN" in i:
			print("Token checked")
			id = int(i.ID)
			user = i.USER
			conn = sqlite3.connect("database.db")
			db2 = conn.cursor()
			badrepl = []
			repls = db2.execute("SELECT * from repls").fetchall()
			for repl in repls:
				if i.TOKEN == repl[1]:
					print("Token verification initiated")
					replid = repl[0]
					print(replid)
					if int(replid) == id:
						print("Token verified")
						if repl[2] != "[]":
							users = ast.literal_eval(repl[2])
						else:
							users = []
						users.append(user)
						db2.execute(f"""UPDATE repls SET users = "{users}" WHERE id = {replid}""")
						conn.commit()
						return "success"
					else:
						return "TOKEN AND ID ARE NOT FROM THE SAME ACCOUNT"
				else:
					badrepl.append(repl)
			if badrepl == len(repls):
				return "INVALID TOKEN"

			
			

class show:
	def GET(self, id):
		conn = sqlite3.connect("database.db")
		db2 = conn.cursor()
		repls = db2.execute(f"SELECT * from repls JOIN users ON repls.token = users.token WHERE repls.id = {id}").fetchall()[0]
		if repls[2] != "[]":
			users = ast.literal_eval(repls[2])
		else:
			users = ""
		repl = {"name": repls[3], "users":users, "user": repls[5]}
		return render.repl(repl)

class delete:
	def POST(self):
		i = web.input()
		conn = sqlite3.connect("database.db")
		db2 = conn.cursor()
		db2.execute("DELETE FROM repls WHERE id = "+str(i.id))
		conn.commit()
		db2.close()
		raise web.seeother("/account")

if __name__ == "__main__":
	app.run()

###################
# DB STRUCTURE
###################

######################################
# TABLE: REPLS
# [id, token, users, name]
######################################
######################################
# TABLE: USERS
# [id, user, token]
######################################