import threading
import socket
import time
import datetime
import mysql.connector
from server_objects import *
from string import ascii_letters
from RSA import RsaEncryption
from re import findall, DOTALL
from os import remove, environ
from flask import Flask, request, jsonify
from pyperclip import copy
from random import choice
from select import select
from tkinter import *
from tkinter.font import *
from tkinter.ttk import Combobox, Treeview
from codecs import encode, decode

FONT = ("Arial", 10, NORMAL)
SERVER_PORT = 31000
API_MANAGER_PORT = 5000
GUI_SIZE = '1050x600'
DOCUMENT = "documentation.txt"
LIFE_MODE = 0
TIME_MODE = 1
API_TOKEN = "63894cwflanedfognk35ffik2"

# DB information
DB_CONFIG = {"host": environ.get("MYSQL_DB_HOST", "localhost"),
            "port": environ.get("MYSQL_DB_PORT", 10000),
            "user": environ.get("MYSQL_DB_USER", "wotserver"),
            'password': environ.get("MYSQL_DB_PASS", "wo653286ver"),
            'database': 'WOT_DB',
            'connection_timeout': 35}


class Server:
	"""The server-side of the project, handle all the clients and their requests while allows the admin
	manage its settings and control the accounts and the maps (including instructions guide in the console).
	uses mysql database for data storage."""
	def __init__(self):
		self.__ip = "0.0.0.0"
		self.__server_socket = socket.socket()
		self.__conn = None
  
		self.__encryptions_ids = []  # All the N's of the encrpytions with the client
		self.__accounts_list = []
		self.__maps_list = []
		self.__maps_display_index = 0  # The index of the current map in map list to display ()
		self.__accounts_updates_to_table = []  # All the updates the server need to commit in DB
		self.__stop_running = False
  
		self.__connections_allowed = None # Indication if admin allows new clients to connect to server
		self.__battles_allowed = None  # Indication if admin allows making for fights
		self.__players_online = None  # The number of players online (tkinter label object if using GUI else string)
		
		self.__life_map_data = ""  # Information of the map in use for the next life mode battle
		self.__life_battle_ip = ""  # Major player ip - for life mode
		self.__new_life_battlefield_id = 0  # the battlefield's number (always even for life mode)
		
		self.__time_map_data = ""  # Information of the map in use for the next life mode battle
		self.__time_battle_ip = ""  # Major player ip - for life mode
		self.__new_time_battlefield_id = 0  # the battlefield's number (always even for life mode)
  
	def build_my_accounts(self):
		"""Retrive the accounts data from the database"""
		curs = self.__conn.cursor()
		curs.execute("SELECT * FROM Accounts")
		data = [list(x) for x in curs.fetchall()]
		for acc in data:
			self.__accounts_list.append(Account(acc[0], acc[1], acc[2],
			                                    acc[3], acc[4], acc[5], acc[6], acc[7]))
		self.__accounts_list.sort(reverse=True, key=lambda x: x.get_points())
		curs.close()
	
	def build_my_maps(self):
		"""Retrive the maps data from the database"""
		curs = self.__conn.cursor()
		curs.execute("SELECT * FROM Maps")
		for m in curs.fetchall():
			self.__maps_list.append(Map(m[0], m[1], m[2], m[3], m[4]))
		curs.close()
  
	def set_db_connection(self):
		"""Set the database connection"""
		try:
			self.__conn = mysql.connector.connect(**DB_CONFIG)
		except:
			print("Can't connect to mysql database")

	
	def activate(self):
		"""activate server and its processes"""
		self.__server_socket.bind((self.__ip, SERVER_PORT))
		self.__server_socket.listen()
		self.set_db_connection()
		if self.__conn is None:
			print("Activation failed!")
			return
		print("Active!")
		self.build_my_accounts()
		self.build_my_maps()
		threading.Thread(target=self.update_users_data).start()
		threading.Thread(target=self.clients_adder).start()
		threading.Thread(target=self.refresh_bans).start()
		try:
			self.start_gui()
		except TclError:
			print("Can't start GUI, running API instead")
			self.__connections_allowed = True
			self.__battles_allowed = True
			self.__players_online = 0
			self.__app = Flask(__name__)
			self.api_setup()
			self.__app.run(host=self.__ip, port=API_MANAGER_PORT)

		self.__connections_allowed = None
		self.__battles_allowed = None
		self.__players_online = None
		self.__stop_running = True
		self.__server_socket.close()
		self.__conn.close()
  
	def api_setup(self):
		"""Setup the api server for remote management in case the GUI is not available"""
		@self.__app.route('/accounts')
		def get_accounts():
				auth_header = request.headers.get('Authorization')
				if not validate_token(auth_header):
					return jsonify({"message": "Unauthorized"}), 401
				if self.__accounts_list == []:
					return jsonify({"message": "There are no accounts"}), 400
				username = request.json.get('username')
				if username is not None: # Look for specific account
					for account in self.__accounts_list:
						if account.get_username() == username:
							account_dict = {}
							setup_dict(account, 0, account_dict)
							return jsonify(account_dict)
					return jsonify({"message": f'Account {username} not found'}), 400
				else:
					accounts_dict = {}
					for index, account in enumerate(self.__accounts_list):
						setup_dict(account, index, accounts_dict)
					return jsonify(accounts_dict)
 
		@self.__app.route('/accounts', methods=['PUT'])
		def reset_accounts():
				auth_header = request.headers.get('Authorization')
				if not validate_token(auth_header):
					return jsonify({"message": "Unauthorized"}), 401
				if self.__accounts_list == []:
					return jsonify({"message": "There are no accounts"}), 400
				username = request.json.get('username')
				if username is not None: # Look for specific account
					for account in self.__accounts_list:
						if account.get_username() == username:
							account.reset_account()
							curs = self.__conn.cursor()
							curs.execute("UPDATE Accounts SET Wins = 0, Loses = 0, \
		            	 	Draws = 0, Points = 0, Color = '4d784e', Bandate = '00/00/0000' WHERE Username = (%s)", (account.get_username(),))
							self.__conn.commit()
							curs.close()
							return '', 204
					return jsonify({"message": f'Account {username} not found'}), 400
				else:
					self.reset_all_accounts_command()
					return '', 204
            
            
		@self.__app.route('/accounts', methods=['POST'])
		def create_account():
			auth_header = request.headers.get('Authorization')
			if not validate_token(auth_header):
				return jsonify({"message": "Unauthorized"}), 401
			username, password = request.json.get('username'), request.json.get('password')
			if self.is_valid_username(username) and self.is_valid_password(password):
				if username not in [account.get_username() for account in self.__accounts_list]:
					self.register_new_player([username, password], True)
					return jsonify({"message": f"Account {username} created successfully"}), 201
				else:
					return jsonify({"message": "Account already exists"}), 400
			else:
				return jsonify({"message": "Invalid username or password"}), 400

		@self.__app.route('/suspensions', methods=['PUT'])
		def free_account():
			auth_header = request.headers.get('Authorization')
			if not validate_token(auth_header):
				return jsonify({"message": "Unauthorized"}), 401
			username = request.json.get('username')
			for account in self.__accounts_list:
				if account.get_username() == username:
					account.free()
					self.__accounts_updates_to_table.append([account, "B"]) # insert into the event list for later update
					return '', 204
			return jsonify({"message": f"Account {username} not found"}), 400


		@self.__app.route('/suspensions', methods=['POST'])
		def ban_account():
			auth_header = request.headers.get('Authorization')
			if not validate_token(auth_header):
				return jsonify({"message": "Unauthorized"}), 401
		
			username, ban_date = request.json.get('username'), request.json.get('ban_date')
			for account in self.__accounts_list:
				if account.get_username() == username:
					account.set_ban_until(ban_date)
					self.__accounts_updates_to_table.append([account, "B"]) # insert into the event list for later update
					return '', 204
		
			return jsonify({"message": f"Account {username} not found"}), 404


		@self.__app.route('/accounts', methods=['DELETE'])
		def remove_account():
			auth_header = request.headers.get('Authorization')
			if not validate_token(auth_header):
				return jsonify({"message": "Unauthorized"}), 401
			username = request.json.get('username')
			for account in self.__accounts_list:
				if account.get_username() == username:
					self.__accounts_list.remove(account)
					self.delete_account(account)
					return '', 204

			return jsonify({"message": f"Account {username} not found"}), 400

		@self.__app.route('/online')
		def get_online():
			auth_header = request.headers.get('Authorization')
			if not validate_token(auth_header):
				return jsonify({"message": "Unauthorized"}), 401
			return jsonify({"message": f"{self.__players_online} players currently online"}), 200

		@self.__app.route('/options', methods=['PUT'])
		def set_connections_allowed():
			auth_header = request.headers.get('Authorization')
			if not validate_token(auth_header):
				return jsonify({"message": "Unauthorized"}), 401
			option, value = request.json.get('option'), request.json.get('value') == 'true'
			if option == "connections":
				self.__connections_allowed = value
			else:
				self.__battles_allowed = value
			return '', 204
		
		def setup_dict(account, index, dict_to_json):
			"""Setup the dictionary of accounts asked by controller"""
			dict_to_json[index] = {
				"Username": account.get_username(), 
				"Password": account.get_password(), 
				"Wins": account.get_wins(),
				"Losses": account.get_loses(), 
				"Draws": account.get_draws(),
				"Points": account.get_points(), 
				"Color": account.get_color(),
				"Status": account.get_status(),
				"Ban date": account.get_ban_date(), 
				"Battle ID": account.get_battle_id()
			}

		def validate_token(auth_header):
			"""validate the token of the admin"""
			if not auth_header:
				return False
			try:
				client_token_type, client_token = auth_header.split()
				if client_token_type != 'Admin':
					return False
				return client_token == API_TOKEN
			except ValueError:
				return False

	def is_new_connections_allowed(self):
		"""Check if new connections from clients are allowed"""
		if isinstance(self.__connections_allowed, bool): # admin uses API
			return self.__connections_allowed
		else:
			return self.__connections_allowed.get() #admin uses GUI

	def is_new_battles_allowed(self):
		"""Check if server is allowed to start new battles"""
		if isinstance(self.__battles_allowed, bool): # admin uses API
			return self.__battles_allowed
		else:
			return self.__battles_allowed.get() #admin uses GUI

	def start_gui(self):
		"""Initialize the GUI of the server"""
		window = Tk()
		window.geometry(GUI_SIZE)
		window.title("My admin's GUI")
		window.resizable(OFF, OFF)
		window.configure(background='azure')
		Label(window, text="Listen on: " + self.__ip, fg='blue',
		      bg='white', borderwidth=5, relief=SUNKEN).place(x=850, y=30)
		self.__players_online = Label(window, text="0 players are online", fg='blue',
		                             bg='white', borderwidth=5, relief=SUNKEN)
		self.__players_online.place(x=850, y=70)
		
		Button(window, text='Open documentation', bg='lavender', font=FONT,
		       height=2, width=16, borderwidth=6, relief=RAISED,
		       command=lambda: self.documentation_window(window)).place(x=480, y=220)
		
		Button(window, text='Exit', bg='lavender', font=FONT,
		       height=2, width=16, borderwidth=6, relief=RAISED,
		       command=lambda: window.destroy()).place(x=480, y=300)
		
		# Switches
		self.__connections_allowed = BooleanVar(value=True)
		self.__battles_allowed = BooleanVar(value=True)
		connections_lf = LabelFrame(window, font=FONT, text="New Connections")
		connections_lf.place(x=0, y=215, width=120, height=130)
		Radiobutton(connections_lf, text="On", variable=self.__connections_allowed,
		            value=True).place(x=10, y=20)
		Radiobutton(connections_lf, text="Off", variable=self.__connections_allowed,
		            value=False).place(x=10, y=60)
		
		battlefields_lf = LabelFrame(window, font=FONT, text="New Battlefields")
		battlefields_lf.place(x=121, y=215, width=120, height=130)
		Radiobutton(battlefields_lf, text="On", variable=self.__battles_allowed,
		            value=True).place(x=10, y=20)
		Radiobutton(battlefields_lf, text="Off", variable=self.__battles_allowed,
		            value=False).place(x=10, y=60)
		
		# Maps control
		Button(window, command=lambda: self.maps_builder_window(window), text="Build new map", font=FONT,
		       borderwidth=6, width=15, height=2, relief=RAISED, bg="light gray").place(x=320, y=220)
		Button(window, command=lambda: self.maps_display_window(window), height=2, width=15,
		       borderwidth=6, bg="light gray", relief=RAISED, text="Display maps", font=FONT).place(x=320, y=300)
		
		# accounts configuration frame
		lf = LabelFrame(window, font=FONT, text="Account's configuration")
		lf.place(x=0, y=0, width=750, height=200)
		user, password = StringVar(), StringVar()
		day, month = StringVar(value="day"), StringVar(value="month")
		year = StringVar(value="year")
		
		Label(lf, text="Username:", font=FONT).place(x=30, y=10)
		Entry(lf, textvariable=user).place(x=125, y=15)
		
		Label(lf, text="Password:\n(Sign ups only)", font=FONT).place(x=20, y=50)
		Entry(lf, textvariable=password).place(x=125, y=55)
		
		Label(lf, text="Date:", font=FONT).place(x=300, y=10)
		
		Combobox(lf, state='readonly', takefocus=OFF, width=4, textvariable=day,
		         values=["day"] + [f"0{x}" if x < 10 else x for x in range(1, 32)]).place(x=360, y=10)
		
		Combobox(lf, state='readonly', takefocus=OFF, width=6, textvariable=month,
		         values=["month"] + [f"0{x}" if x < 10 else x for x in range(1, 13)]).place(x=430, y=10)
		
		Combobox(lf, state='readonly', takefocus=OFF, width=4, textvariable=year,
		         values=["year"] + [str(x) for x in range(datetime.datetime.now().year, datetime.datetime.now().year + 5)]).place(x=515, y=10)
		
		Button(lf, command=lambda: self.clear_input_command(user, password, day, month, year, window),
		       text="Clean inputs", borderwidth=3, width=15, bg="white").place(x=320, y=70)
		
		Button(lf, command=lambda: threading.Thread(target=self.signup_command,
		                                            args=(user, password, tree)).start(),
		       text='Sign up', borderwidth=3, width=10, bg='green').place(x=20, y=140)
		
		Button(lf, command=lambda: threading.Thread(target=self.ban_command,
		                                            args=(user, [day, month, year], tree)).start(),
		       text='Ban', borderwidth=3, width=10, bg='yellow').place(x=120, y=140)
		
		Button(lf, command=lambda: threading.Thread(target=self.free_command,
		                                            args=(user, tree)).start(),
		       text="Free", borderwidth=3, width=10, bg='deep sky blue').place(x=220, y=140)
		
		Button(lf, command=lambda: threading.Thread(target=self.delete_command,
		                                            args=(user, tree)).start(),
		       text='Delete', borderwidth=3, width=10, bg='red').place(x=320, y=140)
		
		Button(lf, command=lambda: threading.Thread(target=self.reset_command,
		                                            args=(user, tree)).start(), text="Reset",
		       borderwidth=3, width=10, bg="orange").place(x=420, y=140)
		
		Button(lf, text='Reset accounts', bg='dodger blue', height=2, width=16,
		       command=lambda: threading.Thread(target=self.reset_all_accounts_command).start()).place(x=585, y=70)
		
		# Accounts data display widget
		headers = ('Username', 'Password', 'Wins',
		           'Loses', 'Draws', 'Points', 'Color', 'Status', 'Ban date', 'Battlefield')
		scroll = Scrollbar(window, orient=VERTICAL)
		tree = Treeview(window, columns=headers, show='headings', yscrollcommand=scroll.set)
		for elem in headers:
			tree.heading(elem, text=elem)
			tree.column(elem, width=102, anchor='center')
		tree.place(y=375)
		scroll.config(command=tree.yview)
		scroll.place(x=1023, y=375, height=225, width=27)
		window.bind("<FocusIn>", lambda event: self.display_account_data(tree))
		window.bind("<Enter>", lambda event: self.display_account_data(tree))
		tree.bind("<FocusIn>", lambda event: self.display_account_data(tree))
		tree.bind("<Enter>", lambda event: self.display_account_data(tree))
		tree.bind("<Control-c>", lambda event: self.get_username_from_tree(tree))
		window.mainloop()
	
	def display_account_data(self, tree):
		"""Displays the account's data in the tree view widget
		parameters:
			tree: type tkinter treeview, the widget of the accounts data
		"""
		for i in tree.get_children():
			tree.delete(i)
		for account in self.__accounts_list:
			tree.insert("", END, values=str(account).split(' '))
   
	
	@staticmethod
	def documentation_window(root):
		"""open the document about the server which include the instructions about
		the button the admin's option over the server's console
		parameters:
			root: type tkinter window, the main console window
		"""
		new_window = Toplevel(root)
		new_window.geometry('1000x500')
		new_window.title("Documentation")
		new_window.config(bg='gray79')
		new_window.resizable(False, False)
		scroll = Scrollbar(new_window, orient=VERTICAL)
		t = Text(new_window, yscrollcommand=scroll.set, wrap=WORD, height=25, width=105)
		scroll.config(command=t.yview)
		with open(DOCUMENT, "r") as file_handler:
			data = file_handler.read()
		t.insert(END, data)
		t.config(state=DISABLED)
		t.place(y=10, x=10)
		scroll.place(x=855, y=10, height=405, width=18)
		new_window.grab_set()
	
	def maps_builder_window(self, root):
		"""Hides the server's main console and start the map builder after finish display the console again
		parameters:
			root: type tkinter window, the main console window"""
		root.withdraw()
		mb = MapBuilder(self.__conn, self.__maps_list)
		mb.start()
		root.deiconify()
	
	def maps_display_window(self, root):
		"""Opens the display window for maps, in it the admin can see the name of the map,
		of create it (only <admin> for now) and even can delete that map (if it is not the original map Map1)
		parameters:
			root: type tkinter window, the main console window
		"""
		minor_window = Toplevel(root)
		minor_window.geometry("1000x600")
		minor_window.resizable(False, False)
		minor_window.title("Maps display")
		self.__maps_display_index = 0
		my_displayed_map = self.__maps_list[self.__maps_display_index]
		photo = PhotoImage(file="Maps/" + my_displayed_map.get_name() + ".png")
		canvas = Canvas(minor_window, width=800, height=600)
		canvas.create_image((0, 0), anchor=NW, image=photo)
		canvas.image = photo
		
		details_label = Label(minor_window, borderwidth=6, relief=SOLID,
		                      text="Creator: " + my_displayed_map.get_creator() + "\nName: " + my_displayed_map.get_name())
		index_label = Label(minor_window, borderwidth=4, relief=GROOVE, width=10,
		                    text=f"{self.__maps_display_index + 1}/{len(self.__maps_list)}")
		
		Button(minor_window, text="Next map\n>>", relief=RAISED, borderwidth=2,
		       command=lambda: self.next_map(details_label, index_label, canvas)).place(x=920, y=100)
		Button(minor_window, text="Previous map\n<<", relief=RAISED, borderwidth=2,
		       command=lambda: self.previous_map(details_label, index_label, canvas)).place(x=825, y=100)
		Button(minor_window, text="Delete map!", bg="red", relief=RAISED, borderwidth=4,
		       command=lambda: self.delete_map(details_label, index_label, canvas)).place(x=865, y=195)
		
		canvas.place(x=0, y=0)
		details_label.place(x=840, y=30)
		index_label.place(x=865, y=155)
		minor_window.grab_set()
	
	def next_map(self, details_label, index_label, canvas):
		"""Goes to the next map to display
		parameters:
			details_label: type tkinter label, for display the data about the displayed map
			index_label: type tkinter label, for display the index in the map list
			canvas: type tkinter canvas, for display the map's image
		"""
		if self.__maps_display_index < len(self.__maps_list) - 1:
			self.__maps_display_index += 1
			self.update_map_display_window(details_label, index_label, canvas)
	
	def previous_map(self, details_label, index_label, canvas):
		"""Goes to the previous map to display
		parameters:
			details_label: type tkinter label, for display the data about the displayed map
			index_label: type tkinter label, for display the index in the map list
			canvas: type tkinter canvas, for display the map's image
		"""
		if self.__maps_display_index > 0:
			self.__maps_display_index -= 1
			self.update_map_display_window(details_label, index_label, canvas)
	
	def update_map_display_window(self, details_label, index_label, canvas):
		"""Updates the maps window by the current map
		parameters:
			details_label: type tkinter label, for display the data about the displayed map
			index_label: type tkinter label, for display the index in the map list
			canvas: type tkinter canvas, for display the map's image
		"""
		my_displayed_map = self.__maps_list[self.__maps_display_index]
		photo = PhotoImage(file="Maps/" + my_displayed_map.get_name() + ".Png")
		canvas.create_image((0, 0), anchor=NW, image=photo)
		canvas.image = photo
		details_label.config(text="Creator: " + my_displayed_map.get_creator()
		                          + "\nName: " + my_displayed_map.get_name())
		index_label.config(text=f"{self.__maps_display_index + 1}/{len(self.__maps_list)}")
	
	def delete_map(self, details_label, index_label, canvas):
		"""Deletes map if its not the original map (Map1)
		parameters:
			details_label: type tkinter label, for display the data about the displayed map
			index_label: type tkinter label, for display the index in the map list
			canvas: type tkinter canvas, for display the map's image
		"""
		if self.__maps_list[self.__maps_display_index].get_name() != "Map1":
			# delete from local database
			curs = self.__conn.cursor()
			curs.execute("DELETE FROM Maps WHERE MapId = (%s)",
			             (self.__maps_list[self.__maps_display_index].get_map_id(),))
			self.__conn.commit()
			# delete map's image
			remove(f"Maps/{self.__maps_list[self.__maps_display_index].get_name()}.png")
			self.__maps_list.pop(self.__maps_display_index)
			if self.__maps_display_index == len(self.__maps_list):
				self.__maps_display_index -= 1
			self.update_map_display_window(details_label, index_label, canvas)  # display another map
	
	@staticmethod
	def get_username_from_tree(tree):
		"""Coping username's easily for accounts management
		parameters:
			tree: type tkinter treeview, the widget of the account data
		"""
		line = tree.focus()
		username = tree.item(line)['values'][0]
		copy(username)
	
	@staticmethod
	def is_valid_username(username):
		"""Filter for username buffer, returns true if up to 10 chars,
		first must be letter and others must be letters or digits, otherwise returns false
		arguments:
			username: type string, the username to check
		"""
		return (0 < len(username) <= 10) and username[0] in ascii_letters and \
		       all([letter in ascii_letters
		            or letter.isdigit() for letter in username[1:]])
	
	@staticmethod
	def is_valid_password(password):
		"""Filter for password buffer, returns true if up to 10 chars,
		all digits or letters otherwise returns false
		arguments:
			username: type string, the username to check
		"""
		return (0 < len(password) <= 10) and all([letter in ascii_letters or
		                                          letter.isdigit() for letter in password])
	
	def signup_command(self, username_entry, password_entry, tree=None):
		"""Admin creates new account (sets its status to offline), if username belong to another account ignores the command
		parameters:
			username_entry: type tkinter entry, the username entry
			new_password: type tkinter entry, the password entry
			tree: type tkinter treeview, the widget of the account data (for refresh console)
		"""
		if self.is_valid_username(username_entry.get()) and self.is_valid_password(password_entry.get()):
			if username_entry.get() not in [element.get_username() for element in self.__accounts_list]:
				self.register_new_player([username_entry.get(), password_entry.get()], True)
		if tree is not None:
			tree.focus_set()
			tree.master.focus_set()
		password_entry.set("")
		username_entry.set("")
	
	# in all those commands if username doesn't belong to any account ignores the command
	def ban_command(self, username_entry, ban_date, tree=None):
		"""Admin bans an account, if date is invalid ignores the command
		parameters:
			username_entry: type tkinter entry, the username entry
			new_password: type list, the 3 string vars (of tkinter) of date (day month and year)
			tree: type tkinter treeview, the widget of the account data (for refresh console)
		"""
		if self.is_valid_username(username_entry.get()):
			try:
				day, month, year = [int(element.get()) for element in ban_date]
				_ = datetime.datetime(day=day, year=year, month=month) # if input is invalid datetime raises ValueError
				for account in self.__accounts_list:
					if account.get_username() == username_entry.get():
						ban_player_until = "/".join(element.get() for element in ban_date)
						account.set_ban_until(ban_player_until)
						self.__accounts_updates_to_table.append([account, "B"])
						break
			except ValueError:
				pass
		if tree is not None:
			tree.focus_set()
			tree.master.focus_set()
		username_entry.set("")
		ban_date[0].set("day")
		ban_date[1].set("month")
		ban_date[2].set("year")
	
	def free_command(self, username_entry, tree=None):
		"""Admin free an account from being banned
		parameters:
			username_entry: type tkinter entry, the username entry
			tree: type tkinter treeview, the widget of the account data (for refresh console)
		"""
		if self.is_valid_username(username_entry.get()):
			for acc in self.__accounts_list:
				if acc.get_username() == username_entry.get():
					acc.free()
					self.__accounts_updates_to_table.append([acc, "B"])
					break
		if tree is not None:
			tree.focus_set()
			tree.master.focus_set()
		username_entry.set("")
	
	def delete_command(self, username_entry, tree=None):
		"""Admin deletes an account
		parameters:
			username_entry: type tkinter entry, the username entry
			tree: type tkinter treeview, the widget of the account data (for refresh console)
		"""
		if self.is_valid_username(username_entry.get()):
			for acc in self.__accounts_list:
				if acc.get_username() == username_entry.get():
					self.__accounts_list.remove(acc)
					self.delete_account(acc)
					break
		if tree is not None:
			tree.focus_set()
			tree.master.focus_set()
		username_entry.set("")
	
	def delete_account(self, account):
		"""Deletes the account from the databases
		parameter:
			account, type Account, the account to delete
		"""
		curs = self.__conn.cursor()
		curs.execute("DELETE FROM Accounts WHERE Username = %s", (account.get_username(),))
		self.__conn.commit()
		curs.close()
	
	def reset_command(self, username_entry, tree=None):
		"""Admin reset an account to its default values (color points etc')
		parameters:
			username_entry: type tkinter entry, the username entry
			tree: type tkinter treeview, the widget of the account data (for refresh console)
		"""
		if self.is_valid_username(username_entry.get()):
			for account in self.__accounts_list:
				if account.get_username() == username_entry.get():
					account.reset_account()
					curs = self.__conn.cursor()
					curs.execute("UPDATE Accounts SET Wins = 0, Loses = 0, \
		            	 Draws = 0, Points = 0, Color = '4d784e', Bandate = '00/00/0000' WHERE Username = (%s)", (account.get_username(),))
					self.__conn.commit()
					curs.close()
		if tree is not None:
			tree.focus_set()
			tree.master.focus_set()
		username_entry.set("")
	

	@staticmethod
	def clear_input_command(username_entry, password_entry, day, month, year, window):
		"""Cleans all the fields of input in the server console
		parameter:
			username_entry: type tkinter entry, the username entry
			password_entry: type tkinter entry, the password entry
			day: type string var, the var of day
			month: type string var, the var of month
			year: type string var, the var of year
			window: type tkinter window, the main console window
		"""
		username_entry.set("")
		password_entry.set("")
		day.set("day")
		month.set("month")
		year.set("year")
		window.focus_set()
	
	def reset_all_accounts_command(self):
		"""Reset all the accounts to their defaults: color points bandate etc'"""
		for account in self.__accounts_list:
			account.reset_account()
		curs = self.__conn.cursor()
		curs.execute(f"UPDATE Accounts SET Wins = 0, Loses = 0,"
		             f" Draws = 0, Points = 0, Color = '4d784e', Bandate = '00/00/0000'")
		self.__conn.commit()
		curs.close()
	
	def update_users_data(self):
		"""Updates all the data of the account in the databases: wins, loses, draws, points, bandate and color
		scans the updates list every 2 seconds and keep the databases relevant"""
		print("Accounts updater start...")
		curs = self.__conn.cursor()
		while self.__stop_running is False:
			for update in self.__accounts_updates_to_table:
				account, act = update[0], update[1]
				if act == "W":
					curs.execute("UPDATE Accounts SET Wins = (%s), Points = (%s) WHERE Username = (%s)",
					             (account.get_wins(), account.get_points(), account.get_username()))
						
				elif act == "L":
					curs.execute("UPDATE Accounts SET Loses = (%s) WHERE Username = (%s)",
					             (account.get_loses(), account.get_username()))
						
				elif act == "E":
					curs.execute("UPDATE Accounts SET Draws = (%s), Points = (%s) WHERE Username = (%s)",
					             (account.get_loses(), account.get_points(), account.get_username()))
						
				elif act == "C":
					curs.execute("UPDATE Accounts SET Color = (%s) WHERE Username = (%s)",
					             (account.get_color(), account.get_username()))
						
				elif act == "B":
					curs.execute("UPDATE Accounts SET Bandate = (%s) WHERE Username = (%s)",
					             (account.get_ban_date(), account.get_username()))
						
				self.__accounts_updates_to_table.remove(update)  # the update done
			self.__conn.commit()
			time.sleep(2)
			self.__accounts_list.sort(reverse=True, key=lambda x: x.get_points())
		curs.close()
		print("Accounts updater shut down...")
	
	def refresh_bans(self):
		"""checks if there is an account that has banned and should be released
		if so releases it, (the check is every 3 seconds to allow clean shut down of the server)"""
		print("Refresh bans run...")
		while not self.__stop_running:
			today = datetime.datetime.replace(datetime.datetime.now(), hour=0, minute=0, second=0)
			banned_list = list(filter(lambda x: x.get_status() == "Banned", self.__accounts_list))
			for acc in banned_list:
				day, month, year = [int(x) for x in acc.get_ban_date().split("/")]
				ban_date = datetime.datetime(day=day, month=month, year=year)
				if ban_date <= today:
					acc.free()
			time.sleep(3)
		print("Refresh ban shut down...")
	
	def clients_adder(self):
		"""Opens new thread for every new client that connect to server (if new connection are allowed)"""
		print("Clients adder run...")
		while self.__stop_running is False:
			try:
				rlist, _, _ = select([self.__server_socket], [], [], 0)
				if self.__server_socket in rlist and (self.__connections_allowed is None or self.is_new_connections_allowed()):
					new_player_socket, _ = self.__server_socket.accept()
					threading.Thread(target=self.player_handler, args=(new_player_socket,)).start()
			except OSError:
				print("Server socket was already closed")
		print("Client adder shut down...")
	
	def send_to_client(self, client, encryption, data, account=None):
		"""Encrypts the packet and ending it to the client (using client services personal encryption)
		if gets an error disconnect from this client
		parameters:
			client: type socket, the socket of the client
			encryption: type RSA encryption, the encryption of this connection
			data: type string, the packet to send to client
			account: type account, the account to release if connection is lost
		"""
		encrypted_packet = encryption.encrypt(data)
		try:
			client.send(encrypted_packet)
		except socket.error:
			self.release_client(encryption, client, account)
	
	def receive_from_client(self, client, encryption, account=None):
		"""Receive packet from client and decrypt it (using client services personal encryption)
		if gets an error disconnect from this client, if not returns the packet (as string)
		parameters:
			client: type socket, the socket of the client
			encryption: type RSA encryption, the encryption of this connection
			account: type account, the account to release if connection is lost
		"""
		try:
			length = client.recv(1)  # first read packet length
			if length == b"":
				raise socket.error
			length = ord(length)
			data = encryption.decrypt(client.recv(length).decode())  # decrypt the packet
			return data
		except socket.error:
			self.release_client(encryption, client, account)
   
	def update_online_player_amount(self, is_increased):
		if isinstance(self.__players_online, Label): #Using GUI
			if is_increased:
				self.__players_online['text'] = \
				f"{int(self.__players_online['text'].split(' ')[0]) + 1} player are online"
			elif self.__players_online['text'].split(' ')[0] != 0:
				self.__players_online['text'] = \
					f"{int(self.__players_online['text'].split(' ')[0]) - 1} player are online"
		elif isinstance(self.__players_online, int): # Using API
			if is_increased:
				self.__players_online += 1
			else:
				self.__players_online -= 1
	
	def release_client(self, encryption, client, account=None):
		"""If server detects an error during communication with client, release its account
		parameters:
			encryption: type RSA encryption, the encryption of the client that should be release
			client: type socket, the socket of the client
			account: the account to set offline (used if error happened after client get an account)"""
		if account is not None:
			account.set_status("Offline")
		client.close()
		self.__encryptions_ids.remove(encryption.get_n())
		self.update_online_player_amount(False)
		exit()
	
	def player_handler(self, client):
		"""Takes care of the client, mostly when the client gets permission to use valid account, then
		can provide information about the account (color rating et'c) in addition to
		connect the client to other players for battles
		parameters:
			client: type socket, the socket of the client
		"""
		
		# Generate keys for encryption for this client session
		encryption = RsaEncryption()
		while encryption.get_n() in self.__encryptions_ids:
			encryption = RsaEncryption()
		self.__encryptions_ids.append(encryption.get_n())
		pk_to_send = encode(','.join([str(i) for i in encryption.get_public()]).encode(), 'base64')[::-1]
		pk_to_send = chr(len(pk_to_send)).encode() + pk_to_send
		client.send(pk_to_send)
		# Recive client's public key
		key_length = ord(client.recv(1))
		encryption.set_partner_public_key([int(x) for x in decode
		(client.recv(key_length)[::-1], 'base64').decode().split(',')])
  
		address = self.receive_from_client(client, encryption)
		account = self.allocate_account(client, encryption)
		if account is None:  # Client didn't connect to any account
			client.close()
			return
		self.update_online_player_amount(True)
		while not self.__stop_running:
			if account not in self.__accounts_list:  # account deleted
				self.send_to_client(client, encryption, "@")
				self.__encryptions_ids.remove(encryption.get_n())
				self.update_online_player_amount(False)
				break
			elif account.get_status() == "Banned":  # account get banned
				self.send_to_client(client, encryption, "!")
				self.send_to_client(client, encryption, account.get_ban_date())
				self.__encryptions_ids.remove(encryption.get_n())
				self.update_online_player_amount(False)
				break
			rlist, _, _ = select([client], [], [], 0)
			if client in rlist:
				request = self.receive_from_client(client, encryption, account).split(" ")
				# handle client's request
				if request[0] == "exit":
					self.release_client(encryption, client, account)
				
				elif request[0] == "GetColor":
					self.send_to_client(client, encryption, account.get_color(), account)
				
				elif request[0] == "SetColor":
					account.update_color(request[1])
					self.__accounts_updates_to_table.append([account, "C"])
				
				elif request[0] == "rating":
					self.send_rating(account, client, encryption)
				
				elif request[0] == "game":
					mode_code = int(request[1])
					self.player_battling(account, client, mode_code, address, encryption)
		client.close()
	
	def allocate_account(self, client, encryption):
		"""Allocates an account to client, for provide him information and services
		parameters:
			client: type socket, the socket of the client
			encryption: type socket, the encryption of the connection with client"""
		account = None
		while not self.__stop_running:
			rlist, _, _ = select([client], [], [], 0)
			if client in rlist:
				request = self.receive_from_client(client, encryption).split(" ")
				if request[0] == "exit":
					return None
				#  sending the data from client for identification
				elif request[0] == "Signup":  # client signup
					account = self.confirm_register(client, request[1], encryption)
				elif request[0] == "login":  # client login
					account = self.player_login(client, request[1], encryption)
				if account is not None:
					return account
	
	def send_rating(self, account, client, encryption):
		"""Builds a string about the current 3 champions and the player, sends it to player
		(if he isn't one of the champion) and returns it
		parameter:
			account: type account, the account which search its' rating in the accounts list
			client: type client, the socket of the client
			encryption: the RSA encryption, the encryption of the connection
		"""
		information = ""
		is_in_top_three = True
		if len(self.__accounts_list) >= 3:
			scan_range = 3
			if account not in self.__accounts_list[0: 3]:
				is_in_top_three = False
		else:
			scan_range = len(self.__accounts_list)
		for i in range(scan_range):
			champion = self.__accounts_list[i]
			information += f"{champion.get_username()} {champion.get_wins()} " \
			               f"{champion.get_loses()} {champion.get_draws()} {champion.get_points()} {i+1}\n"
		if not is_in_top_three:  # add the player to the rating string
			information += f"{account.get_username()} {account.get_wins()} " \
			               f"{account.get_loses()} {account.get_draws()} {account.get_points()}" \
			               f" {self.__accounts_list.index(account) + 1}"
		# rating packet is getting split for avoiding packet so long that encryption raise error
		split_information = findall(".{1,20}", information, DOTALL)
		self.send_to_client(client, encryption, str(len(split_information)), account)
		for x in split_information:
			self.send_to_client(client, encryption, x, account)
		
	def player_battling(self, account, client, mode_code, address, encryption):
		"""Runs the player's request to fight (Life/Time mode), when the battle ends
		gets the result from the player and update its data
		parameters:
			account: type account, the player's account
			client: type socket, the socket of the client
			mode_code: type int, the id of the asked mode of the player
			address: type tuple, the address of the client (ip, port)
			encryption: type RSA encryption, the encryption of the connection with client
		"""
		if not self.is_new_battles_allowed():  # Battlefields are locked
			self.send_to_client(client, encryption, "#", account)
			return
		self.send_to_client(client, encryption, "$", account)
		if mode_code == LIFE_MODE:
			is_need_release = self.life_battle_request(address, client, account, encryption)
		else:
			is_need_release = self.time_battle_request(address, client, account, encryption)
		if is_need_release:  # player disconnect
			self.release_client(encryption, client, account)
		elif is_need_release is False:  # clients goes backs to menu screen
			return
		while True:
			if self.__stop_running:
				client.close()
				exit()  # server shut down
			if account not in self.__accounts_list:
				account.set_battle_id(0)
				self.send_to_client(client, encryption, "@")  # account deleted
				self.__encryptions_ids.remove(encryption.get_n())
				self.update_online_player_amount(False)
				break
			if account.get_status() == "Banned":  # account gets banned
				account.set_battle_id(0)
				self.send_to_client(client, encryption, "!")
				self.send_to_client(client, encryption, account.get_ban_date())
				self.__encryptions_ids.remove(encryption.get_n())
				self.update_online_player_amount(False)
				break
			rlist, _, _ = select([client], [], [], 0)
			if client in rlist:
				outcome = ""
				try:
					outcome = client.recv(1)
					if outcome == b"":
						raise socket.error
					outcome = encryption.decrypt(client.recv(ord(outcome)).decode())
				except socket.error:
					account.set_battle_id(0)
					account.add_lose()
					self.release_client(encryption, client, account)
				act = None
				account.set_battle_id(0)
				if outcome == "exit":  # player exit the game
					self.__accounts_updates_to_table.append([account, "L"])
					client.close()
					account.add_lose()
					account.set_status("Offline")
					return True
				elif outcome == "Victory":  # player won
					act = "W"
					account.add_win()
					enemy_username = self.receive_from_client(client, encryption, account)
					account.get_bonus(self.calculate_bonus_points(enemy_username))  # get bonus only if win
				elif outcome == "Defeat":  # player lost
					act = "L"
					account.add_lose()
				elif outcome == "Draw":  # draw in the match
					act = "E"
					account.add_draws()
				elif outcome == "Cancel":
					# first player didn't identify attempt to connect
					pass
				self.__accounts_updates_to_table.append([account, act])
				break
	
	def calculate_bonus_points(self, enemy_username):
		"""players gets:
		-> 3 points bonus for winning the #1 champ
		-> 2 points bonus for winning the #2 champ
		-> 1 point bonus for winning the #3 champ
		parameters:
			enemy_username: type string, the enemy the player won
		"""
		# fix the top 3 players bonus logic!!!
		if enemy_username == self.__accounts_list[0].get_username() and self.__accounts_list[0].get_points() > 0:
			return 3
		elif enemy_username == self.__accounts_list[1].get_username() and self.__accounts_list[1].get_points() > 0:
			return 2
		elif len(self.__accounts_list) >= 3 and enemy_username == self.__accounts_list[2].get_username() and self.__accounts_list[2].get_points() > 0:
			return 1
		return 0
	
	def life_battle_request(self, address, client, account, encryption):
		"""Handles the request of the player for making a new battle in life mode,
		include actions for special cases like locking new battlefield.
		if player is major player (the first that searched for a match) stores his ip and waits until
		other player look for match.
		if player is minor player (the one who connect to the first player), sends him immediately the stored ip
		In addition sends them both the information of battlefield map
		parameter:
			address: type tuple, the address of the player (ip, port)
			client: type socket, the socket of the client
			account: type account, the player's account
			encryption: type RSA encryption, the encryption of the connection with client
		"""
		if self.__life_battle_ip == "":  # player create connection
			self.send_to_client(client, encryption, "T", account)
			self.__life_map_data = str(choice(self.__maps_list))
			battle_id = self.__new_life_battlefield_id = self.find_next_battlefield(LIFE_MODE)
			self.__life_battle_ip = address
			while self.__new_life_battlefield_id != 0:  # another player has been found
				rlist, _, _ = select([client], [], [], 0)
				if client in rlist:
					try:
						message = client.recv(1)
						if message == b"":
							raise socket.error
						message = encryption.decrypt(client.recv(ord(message)).decode())
					except socket.error:
						self.__life_battle_ip = ""
						return True
					if message == "exit":  # player disconnect
						self.__life_battle_ip = ""
						return True
					elif message == "%":  # player doesn't wait for match anymore
						self.__life_battle_ip = ""
						return False
				if not self.is_new_battles_allowed():
					client.send(b"##")  # New battles are locked
					self.__life_battle_ip = ""
					return False
				if self.__stop_running:
					client.close()
					exit()
			account.set_battle_id(battle_id)
			try:
				if not self.is_new_battles_allowed():
					client.send(b"##")  # New battles are locked
					self.__life_battle_ip = ""
					return False
				client.send(encryption.encrypt_map_data(self.__life_map_data))
			except socket.error:
				account.set_battle_id(0)
				self.release_client(encryption, client, account)
		
		else:  # second player
			ip = self.__life_battle_ip
			self.__life_battle_ip = ""  # players make communication, can start another battle
			account.set_battle_id(self.__new_life_battlefield_id)
			self.__new_life_battlefield_id = 0
			try:
				client.send(encryption.encrypt("F"))
				if not self.is_new_battles_allowed():  # New battles are locked
					client.send(encryption.encrypt("0.0.0.0"))  # indefinite ip address
					client.send(b"##")
					return False
				client.send(encryption.encrypt(ip))
				client.send(encryption.encrypt_map_data(self.__life_map_data))
			except socket.error:
				self.__life_battle_ip = ""
				account.set_battle_id(0)
				self.release_client(encryption, client, account)
	
	def time_battle_request(self, address, client, account, encryption):
		"""As the life_battle_request, but for time mode
		parameter:
			address: type tuple, the address of the player (ip, port)
			client: type socket, the socket of the client
			account: type account, the player's account
			encryption: type RSA encryption, the encryption of the connection with client
		"""
		if self.__time_battle_ip == "":  # player create connection
			self.send_to_client(client, encryption, "T", account)
			self.__time_map_data = str(choice(self.__maps_list))
			battle_id = self.__new_time_battlefield_id = self.find_next_battlefield(TIME_MODE)
			self.__time_battle_ip = address[0]
			while self.__new_time_battlefield_id != 0:  # another player has been found
				rlist, _, _ = select([client], [], [], 0)
				if client in rlist:
					try:
						message = client.recv(1)
						if message == b"":
							raise socket.error
						message = encryption.decrypt(client.recv(ord(message)).decode())
					except socket.error:
						self.__time_battle_ip = ""
						return True
					if message == "exit":  # player disconnect
						self.__time_battle_ip = ""
						return True
					elif message == "%":  # player doesn't wait for match anymore
						self.__time_battle_ip = ""
						return False
				if not self.is_new_battles_allowed():
					client.send(b"##")  # New battles are locked
					self.__time_battle_ip = ""
					return False
				if self.__stop_running:
					client.close()
					exit()
			account.set_battle_id(battle_id)
			try:
				if not self.is_new_battles_allowed():
					client.send(b"##")  # New battles are locked
					self.__time_battle_ip = ""
					return False
				client.send(encryption.encrypt_map_data(self.__time_map_data))
			except socket.error:
				account.set_battle_id(0)
				self.release_client(encryption, client, account)
		
		else:  # second player
			ip = self.__time_battle_ip
			self.__time_battle_ip = ""  # players make communication, can start another battle
			account.set_battle_id(self.__new_time_battlefield_id)
			self.__new_time_battlefield_id = 0
			try:
				client.send(encryption.encrypt("F"))
				if not self.is_new_battles_allowed():  # New battles are locked
					client.send(encryption.encrypt("0.0.0.0"))  # indefinite ip address
					client.send(b"##")
					return False
				client.send(encryption.encrypt(ip))
				client.send(encryption.encrypt_map_data(self.__time_map_data))
			except socket.error:
				self.__time_battle_ip = ""
				account.set_battle_id(0)
				self.release_client(encryption, client, account)
	
	def confirm_register(self, client, account, encryption):
		"""Checks if there isn't account with the username that was given from the client for signup
		sends back N if there is already username, Y if there isn't
		parameters:
			client: type socket, the socket of the client
			account: type account, the player's account
			encryption: type RSA encryption, the encryption of the connection with client"""
		new_player_data = account.split(",")
		is_invalid = False
		is_invalid = ((new_player_data[0] == "") or (new_player_data[1] == ""))
		if is_invalid: # one field is empty
			self.send_to_client(client, encryption, "P")
		else:
			for acc in self.__accounts_list:
				if acc.get_username() == new_player_data[0]:
					is_invalid = True
		if is_invalid:
			self.send_to_client(client, encryption, "N") # username is taken
		else:
			self.send_to_client(client, encryption, "Y")
			new_account = self.register_new_player(new_player_data, False)
			print("A new player signed up, his username is: " + new_player_data[0])
			return new_account
	
	def register_new_player(self, new_account_data, is_admin_command):
		"""After server makes sure the new account is valid for registering (from server/client creation)
		updates the databases with the new account
		parameter:
			new_account_data: type list, the username and password of the new account
			is_admin_command: boolean, if admin created the
			account set status to offline else set it to online
		"""
		
		curs = self.__conn.cursor()
		curs.execute("INSERT INTO Accounts VALUES(%s, %s, %s, %s, %s, %s, %s, %s)",
		               (new_account_data[0], new_account_data[1], 0, 0, 0, 0,
		                "4d784e", "00/00/0000"))
		self.__conn.commit()
		curs.close()
		new_account = Account(new_account_data[0], new_account_data[1],
		                      0, 0, 0, 0, "4d784e", "00/00/0000")
		if not is_admin_command:
			new_account.set_status("Online")
		self.__accounts_list.append(new_account)
		self.__accounts_list.sort(reverse=True, key=lambda x: x.get_points())
		return new_account
	
	def player_login(self, client, user_password, encryption):
		"""Handles the different login to account cases and send a respond to client:
		T -> account is taken but another client
		B -> account is banned
		F -> account isn't exist
		O -> login succeeded
		parameter:
			client: type socket, the socket of the client
			user_password: type string, the packet from client that include the detail about the asked account
			encryption: type RSA encryption, the encryption of the connection with client
		"""
		account_to_check = user_password.split(",")
		exist = False
		for account in self.__accounts_list:
			if account.get_username() == account_to_check[0] and account.get_password() == account_to_check[1]:
				# found match
				exist = True
				if account.get_status() == "Online":  # this account is already taken
					self.send_to_client(client, encryption, "T")
				elif account.get_status() == "Banned":
					self.send_to_client(client, encryption, "B")
					self.send_to_client(client, encryption, account.get_ban_date())
				else:
					self.send_to_client(client, encryption, "O")  # can use this account
					account.set_status("Online")
					return account
		if not exist:
			self.send_to_client(client, encryption, "F")  # desired account does not exist
	
	def find_next_battlefield(self, battle_mode):
		"""finds the next available battlefield id and returns it
		for life mode -> odd numbers (minimum 1)
		for time mode -> even numbers (minimum 2)
		parameters:
			battle_mode: type int, the mode that need to find for it a new battle id"""
		if battle_mode == LIFE_MODE:
			my_battlefield_ids = [x.get_battle_id() for x in self.__accounts_list
			                      if x.get_battle_id() >= 1 and x.get_battle_id() % 2]
			if my_battlefield_ids != []:
				return max(my_battlefield_ids) + 2 if min(my_battlefield_ids) == 1 else min(my_battlefield_ids) -2
			else:
				return 1
		else: # TIME_MODE
			my_battlefield_ids = [x.get_battle_id() for x in self.__accounts_list
			                      if x.get_battle_id() >= 1 and not (x.get_battle_id() % 2)]
			if my_battlefield_ids != []:
				return max(my_battlefield_ids) + 2 if min(my_battlefield_ids) == 2 else min(my_battlefield_ids) -2
			else:
				return 2


def main():
	server = Server()
	server.activate()


if __name__ == '__main__':
	main()
