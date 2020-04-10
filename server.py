import threading
import socket
import time
import string
import datetime
from server_objects import Account, Map
from builder import MapBuilder
from RSA import RsaEncryption
from subprocess import Popen, PIPE
from re import findall
from os import system, remove
from pyperclip import copy
from random import choice
from firebase import firebase
from select import select
from tkinter import *
from tkinter.font import *
from tkinter.ttk import Combobox, Treeview
from sqlite3 import *
from requests.exceptions import ConnectionError
from codecs import encode, decode

FONT = ("Arial", 10, NORMAL)
API_SIZE = '1050x600'

INSTALLER_FILE = "game installer.exe"

FIREBASE_URL = "https://my-project-b9bb8.firebaseio.com/"


# maybe move the control of ban refresh to clients adder and do it every 24 (with clock and datetime)
class Server:
	LIFE_MODE = 0
	TIME_MODE = 1
	
	def __init__(self):
		self.__ip = socket.gethostbyname(socket.gethostname())
		self.__server_socket = socket.socket()
		self.__server_socket.bind((self.__ip, 2020))
		self.__server_socket.listen(1)
		self.__firebase = firebase.FirebaseApplication(FIREBASE_URL, None)
		self.__is_online_database = False
		self.__n_cryption = []
		self.__players_label = None
		self.__accounts_list = []
		self.__maps_list = []
		self.__maps_display_index = 0
		self.__accounts_updates_to_table = []
		self.__stop_running = False
		self.__open_connections = None  # boolean var for connections switch
		self.__open_battlefields = None  # boolean var for battlefields switch
		
		self.__life_map_data = ""
		self.__life_battle_ip = ""
		self.__new_life_battlefield_id = 0
		
		self.__time_map_data = ""
		self.__time_battle_ip = ""
		self.__new_time_battlefield_id = 0
	
	def sync_data(self):
		"""
		make sure the databases are sync
		if firebase inevitable the default become the local database
		"""
		try:
			global_accounts = self.__firebase.get('Accounts/', '')
			if global_accounts is None:
				global_accounts_tokens = set()
			else:
				global_accounts_tokens = set(global_accounts.keys())
			global_maps_tokens = set(self.__firebase.get('Maps/', '').keys())
			self.__is_online_database = True
		except ConnectionError:  # cant access firebase
			print("cant get access to online firebase")
			return
		conn = connect("my database.db")
		curs = conn.cursor()
		curs.execute("SELECT IsOfflineUpdated FROM Flags")
		is_offline_updated = bool(curs.fetchall()[0][0])  # if need to sync data from last time
		if is_offline_updated:
			self.sync_accounts_data(curs, global_accounts_tokens)
			self.sync_maps_data(curs, global_maps_tokens)
			curs.execute("UPDATE Flags set IsOfflineUpdated = 0")  # finish sync data
			conn.commit()
		conn.close()
	
	def sync_accounts_data(self, curs, global_tokens):
		curs.execute("SELECT * FROM Accounts")
		local_accounts = curs.fetchall()
		local_tokens = set([x[8] for x in local_accounts])
		deleted_accounts = list(global_tokens - local_tokens)
		for element in deleted_accounts:
			self.__firebase.delete("Accounts/", element)
		for element in local_accounts:
			if element[8] == "":  # if account need to be posting in firebase
				token = self.__firebase.post("Accounts/",
				                             {"Username": element[0], "Password": element[1],
				                              "Wins": element[2], "Loses": element[3],
				                              "Draws": element[4], "Points": element[5], "Color": element[6],
				                              "Bandate": element[7]})['name']
				curs.execute("UPDATE Accounts SET Netoken = (?) WHERE Username = (?)", (token, element[0]))
			else:  # make sure the account in firebase are updated
				self.__firebase.patch(f"Accounts/{element[8]}",
				                      {"Wins": element[2], "Loses": element[3], "Draws": element[4],
				                       "Points": element[5], "Color": element[6], "Bandate": element[7]})
	
	def sync_maps_data(self, curs, global_tokens):
		curs.execute("SELECT * FROM Maps")
		local_maps = curs.fetchall()
		local_tokens = set(x[5] for x in local_maps)
		deleted_maps = list(global_tokens - local_tokens)
		for element in deleted_maps:
			self.__firebase.delete("Maps/", element)
		for element in local_maps:
			if element[5] == "":  # if map need to be posting in firebase
				token = self.__firebase.post("Maps/", {"Creator": element[0],
				                                       "Name": element[1], "MapId": element[2],
				                                       "Walls": element[3], "PlayersLocations": element[4]})
				curs.execute("UPDATE Maps SET Netoken = (?) WHERE MapId = (?)", (token, element[2]))
	
	def build_my_accounts(self):
		"""
		get the accounts data from the default and storage them in account instance
		"""
		if self.__is_online_database:
			accounts_data = self.__firebase.get('Accounts', '')
			if accounts_data is None:
				return
			data = [x for x in accounts_data.items()]
			for element in data:
				firebase_token = element[0]
				username, password, wins = element[1]['Username'], element[1]['Password'], element[1]['Wins']
				loses, draws, points = element[1]['Loses'], element[1]['Draws'], element[1]['Points']
				color, bandate = element[1]['Color'], element[1]['Bandate']
				self.__accounts_list.append(Account(username, password, wins, loses,
				                                    draws, points, color, bandate, firebase_token))
				self.__accounts_list.sort(reverse=True, key=lambda x: x.get_points())
			return
		conn = connect("my database.db")
		curs = conn.cursor()
		curs.execute("UPDATE Flags set IsOfflineUpdated = 1")
		conn.commit()
		curs.execute("SELECT * FROM Accounts")
		conn.close()
		data = [list(x) for x in curs.fetchall()]
		for acc in data:
			self.__accounts_list.append(Account(acc[0], acc[1], acc[2],
			                                    acc[3], acc[4], acc[5], acc[6], acc[7], acc[8]))
		self.__accounts_list.sort(reverse=True, key=lambda x: x.get_points())
	
	def build_my_maps(self):
		if self.__is_online_database:
			maps_data = self.__firebase.get("Maps", '')
			maps_keys = [x for x in maps_data.keys()]
			for key in maps_keys:
				m = maps_data[key]
				self.__maps_list.append(Map(m['Creator'], m['Name'], m['MapId'],
				                            m['Walls'], m['PlayersLocations'], key))
		else:
			conn = connect("my database.db")
			curs = conn.cursor()
			curs.execute("SELECT * FROM Maps")
			for m in curs.fetchall():
				self.__maps_list.append(Map(m[0], m[1], m[2], m[3], m[4], m[5]))
	
	def active(self):
		"""
		active all the functions of the server
		"""
		self.sync_data()
		self.build_my_accounts()
		self.build_my_maps()
		threading.Thread(target=self.update_users_data).start()
		threading.Thread(target=self.clients_adder).start()
		threading.Thread(target=self.refresh_bans).start()
		threading.Thread(target=lambda:
		system(f"python web/manage.py runserver {self.__ip}:8000")).start()
		self.server_screen()
		# kill django server using PID
		result = Popen("netstat -ano | findstr :8000", stdout=PIPE, shell=True)
		available_django_processes = result.communicate()[0].decode().split("\r\n")
		for element in available_django_processes:
			if "LISTENING" in element:
				process_id = findall(r'\d+', element)[-1]
				system(f"taskkill /PID {process_id} /F")
				break
		self.__stop_running = True
		self.__server_socket.close()
	
	@staticmethod
	def documentation_window(window):
		new_window = Toplevel(window)
		new_window.geometry('600x400')
		new_window.title("Documentation")
		new_window.config(bg='gray79')
		new_window.resizable(False, False)
		scroll = Scrollbar(new_window, orient=VERTICAL)
		t = Text(new_window, yscrollcommand=scroll.set, wrap=WORD)
		scroll.config(command=t.yview)
		with open("doc.txt", "r") as file_handler:
			data = file_handler.read()
		t.insert(END, data)
		t.config(state=DISABLED)
		t.place(y=10, x=10, height=380, width=450)
		scroll.place(x=460, y=10, height=380, width=18)
		new_window.grab_set()
	
	def map_builder_window(self, root):
		root.withdraw()
		mb = MapBuilder(self.__firebase, self.__maps_list)
		mb.start()
		root.deiconify()
	
	def maps_display_window(self, root):
		minor_window = Toplevel(root)
		minor_window.geometry("1000x600")
		minor_window.resizable(False, False)
		minor_window.title("Maps display")
		self.__maps_display_index = 0
		my_displayed_map = self.__maps_list[self.__maps_display_index]
		photo = PhotoImage(file="Maps/" + my_displayed_map.get_name() + ".Png")
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
		if self.__maps_display_index < len(self.__maps_list) - 1:
			self.__maps_display_index += 1
			self.update_map_display_window(details_label, index_label, canvas)
	
	def previous_map(self, details_label, index_label, canvas):
		if self.__maps_display_index > 0:
			self.__maps_display_index -= 1
			self.update_map_display_window(details_label, index_label, canvas)
	
	def update_map_display_window(self, details_label, index_label, canvas):
		my_displayed_map = self.__maps_list[self.__maps_display_index]
		photo = PhotoImage(file="Maps/" + my_displayed_map.get_name() + ".Png")
		canvas.create_image((0, 0), anchor=NW, image=photo)
		canvas.image = photo
		details_label.config(text="Creator: " + my_displayed_map.get_creator()
		                          + "\nName: " + my_displayed_map.get_name())
		index_label.config(text=f"{self.__maps_display_index + 1}/{len(self.__maps_list)}")
	
	def delete_map(self, details_label, index_label, canvas):
		if self.__maps_list[self.__maps_display_index].get_name() != "Map1":
			# delete from local database
			conn = connect("my database.db")
			curs = conn.cursor()
			curs.execute("DELETE FROM Maps WHERE MapId = (?)",
			             (self.__maps_list[self.__maps_display_index].get_map_id(),))
			conn.commit()
			# delete from firebase
			if self.__is_online_database:
				self.__firebase.delete("Maps/", self.__maps_list[self.__maps_display_index].get_token())
			# delete map's image
			remove(f"Maps/{self.__maps_list[self.__maps_display_index].get_name()}.png")
			self.__maps_list.pop(self.__maps_display_index)
			if self.__maps_display_index == len(self.__maps_list):
				self.__maps_display_index -= 1
			self.update_map_display_window(details_label, index_label, canvas)
			print(len(self.__maps_list))
	
	def server_screen(self):
		"""
		create the API of the admin
		"""
		window = Tk()
		window.geometry(API_SIZE)
		window.title("My admin interface")
		window.resizable(OFF, OFF)
		window.configure(background='azure')
		Label(window, text="My IP is: " + self.__ip, fg='blue',
		      bg='white', borderwidth=5, relief=SUNKEN).place(x=850, y=30)
		self.__players_label = Label(window, text="0 players are online", fg='blue',
		                             bg='white', borderwidth=5, relief=SUNKEN)
		self.__players_label.place(x=850, y=70)
		
		# Switches
		self.__open_connections = BooleanVar(value=True)
		self.__open_battlefields = BooleanVar(value=True)
		connections_lf = LabelFrame(window, font=FONT, text="New Connections")
		connections_lf.place(x=0, y=215, width=120, height=130)
		Radiobutton(connections_lf, text="On", variable=self.__open_connections,
		            value=True).place(x=10, y=20)
		Radiobutton(connections_lf, text="Off", variable=self.__open_connections,
		            value=False).place(x=10, y=60)
		
		battlefields_lf = LabelFrame(window, font=FONT, text="New Battlefields")
		battlefields_lf.place(x=121, y=215, width=120, height=130)
		Radiobutton(battlefields_lf, text="On", variable=self.__open_battlefields,
		            value=True).place(x=10, y=20)
		Radiobutton(battlefields_lf, text="Off", variable=self.__open_battlefields,
		            value=False).place(x=10, y=60)
		
		# Maps Controllers
		Button(window, command=lambda: self.map_builder_window(window), text="Make new map", font=FONT,
		       borderwidth=6, width=15, height=2, relief=RAISED, bg="light gray").place(x=320, y=220)
		Button(window, command=lambda: self.maps_display_window(window), height=2, width=15,
		       borderwidth=6, bg="light gray", relief=RAISED, text="Display maps", font=FONT).place(x=320, y=300)
		
		lf = LabelFrame(window, font=FONT, text="Accounts manage interface")
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
		         values=["year"] + [str(x) for x in range(2020, 2024)]).place(x=515, y=10)
		
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
		       command=lambda: threading.Thread(target=self.reset_all_accounts_command).start()).place(x=585, y=10)
		
		Button(lf, text='Open documentation', bg='dodger blue', height=2, width=16,
		       command=lambda: self.documentation_window(window)).place(x=585, y=60)
		
		Button(lf, text='Exit', bg='dodger blue', height=2, width=16,
		       command=lambda: window.destroy()).place(x=585, y=110)
		
		# Accounts data display
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
		window.bind("<FocusIn>", lambda event: self.show_account_data(tree))
		window.bind("<Enter>", lambda event: self.show_account_data(tree))
		tree.bind("<FocusIn>", lambda event: self.show_account_data(tree))
		tree.bind("<Enter>", lambda event: self.show_account_data(tree))
		tree.bind("<Control-c>", lambda event: self.get_username_from_tree(tree))
		window.mainloop()
		self.__open_connections = None
		self.__open_battlefields = None
		self.__players_label = None
	
	def show_account_data(self, tree):
		"""
		print the data of all the accounts
		tree - Treeview, the widget of the accounts data
		"""
		for i in tree.get_children():
			tree.delete(i)
		for account in self.__accounts_list:
			tree.insert("", END, values=str(account).split(' '))
	
	@staticmethod
	def get_username_from_tree(tree):
		line = tree.focus()
		username = tree.item(line)['values'][0]
		copy(username)
	
	@staticmethod
	def is_valid_username(username):
		"""
		filter for username buffer, returns true if up to 10 chars, first must be letter
		and others must be letters or digits, otherwise returns false
		arguments:
			username - string, the username to check
		"""
		return (0 < len(username) <= 10) and username[0] in string.ascii_letters and \
		       all([letter in string.ascii_letters
		            or letter.isdigit() for letter in username[1:]])
	
	@staticmethod
	def is_valid_password(password):
		"""
		filter for password buffer, returns true if up to 10 chars, all digits or letters
		otherwise returns false
		arguments:
			username - string, the username to check
		"""
		return (0 < len(password) <= 10) and all([letter in string.ascii_letters or
		                                          letter.isdigit() for letter in password])
	
	def signup_command(self, username_entry, password_entry, tree):
		"""
		the admin registers a new player, if already exist ignore
		parameters:
			new_username - Entry widget, username to register
			new_password - Entry widget, password to register
			window - Treeview, the widget of the accounts data
		"""
		if self.is_valid_username(username_entry.get()) and self.is_valid_password(password_entry.get()):
			if username_entry.get() not in [element.get_username() for element in self.__accounts_list]:
				self.register_new_player([username_entry.get(), password_entry.get()], is_admin_command=True)
		tree.focus_set()
		tree.master.focus_set()
		password_entry.set("")
		username_entry.set("")
	
	def ban_command(self, username_entry, ban_date, tree):
		"""
		the admin ban a player, if username/password incorrect ignore
		same if the ban date is wrong
		arguments:
		username - Entry widget, username to ban
		password - Entry widget, password to ban
		ban_date - list, the widgets of ban date
		window - Treeview, the widget of the accounts data
		"""
		if self.is_valid_username(username_entry.get()):
			try:
				day, month, year = [int(element.get()) for element in ban_date]
				_ = datetime.datetime(day=day, year=year, month=month)
				for account in self.__accounts_list:
					if account.get_username() == username_entry.get():
						ban_player_until = "/".join(element.get() for element in ban_date)
						account.set_ban_until(ban_player_until)
						self.__accounts_updates_to_table.append([account, "B"])
						break
			except ValueError:
				pass
		tree.focus_set()
		tree.master.focus_set()
		username_entry.set("")
		ban_date[0].set("day")
		ban_date[1].set("month")
		ban_date[2].set("year")
	
	def free_command(self, username_entry, tree):
		"""
		the admin deletes a player, if username/password incorrect ignore
		arguments:
			username - Entry widget, username to free
			password - Entry widget, password to free
			window - Treeview, the widget of the accounts data
		"""
		if self.is_valid_username(username_entry.get()):
			for acc in self.__accounts_list:
				if acc.get_username() == username_entry.get():
					acc.free()
					self.__accounts_updates_to_table.append([acc, "B"])
					break
		tree.focus_set()
		tree.master.focus_set()
		username_entry.set("")
	
	def delete_command(self, username_entry, tree):
		"""
		the admin deletes a player, if username/password incorrect ignore
		arguments:
			username - Entry widget, username to ban
			password - Entry widget, password to ban
			window - Treeview, the widget of the accounts data
		"""
		if self.is_valid_username(username_entry.get()):
			for acc in self.__accounts_list:
				if acc.get_username() == username_entry.get():
					self.__accounts_list.remove(acc)
					self.delete_account(acc)
					break
		tree.focus_set()
		tree.master.focus_set()
		username_entry.set("")
	
	def reset_command(self, username_entry, tree):
		if self.is_valid_username(username_entry.get()):
			for account in self.__accounts_list:
				if account.get_username() == username_entry.get():
					self.reset_account(account)
		tree.focus_set()
		tree.master.focus_set()
		username_entry.set("")
	
	@staticmethod
	def clear_input_command(username_entry, password_entry, day, month, year, window):
		username_entry.set("")
		password_entry.set("")
		day.set("day")
		month.set("month")
		year.set("year")
		window.focus_set()
	
	def reset_all_accounts_command(self):
		"""
		clean the data of all the accounts and set it to default
		parameters:
			window - Treeview, the widget of the accounts data
		"""
		for account in self.__accounts_list.copy():
			self.reset_account(account)
	
	def delete_account(self, account):
		"""
		delete the account from the databases (if firebase is inevitable skip it)
		parameters:
			account - Account, the account to delete
		"""
		if self.__is_online_database:
			self.__firebase.delete("Accounts/", account.get_firebase_token())
		conn = connect("my database.db")
		curs = conn.cursor()
		curs.execute("DELETE FROM Accounts WHERE Username = ?", (account.get_username(),))
		conn.commit()
		conn.close()
	
	def reset_account(self, account):
		account.clean_data()
		conn = connect('my database.db')
		curs = conn.cursor()
		curs.execute(f"UPDATE ACCOUNTS SET Wins = 0, Loses = 0,"
		             f" Draws = 0, Points = 0, Color = '4d784e', Bandate = '00/00/0000'"
		             f" WHERE Username = (?)", (account.get_username(),))
		conn.commit()
		conn.close()
		if self.__is_online_database:
			self.__firebase.patch(f"Accounts/{account.get_firebase_token()}/",
			                      {"Wins": 0, "Loses": 0, "Draws": 0, "Points": 0,
			                       "Color": "4d784e", "Bandate": "00/00/0000"})
	
	def update_users_data(self):
		"""
		update the changes of all the accounts such as wins, loses, color
		etc' in the databases
		"""
		print("Accounts updater start...")
		conn = connect('my database.db')
		curs = conn.cursor()
		while self.__stop_running is False:
			
			for update in self.__accounts_updates_to_table:
				account, act = update[0], update[1]
				if act == "W":
					curs.execute("UPDATE Accounts SET Wins = (?), Points = (?) WHERE Username = (?)",
					             (account.get_wins(), account.get_points(), account.get_username()))
					if self.__is_online_database:
						self.__firebase.patch(f'Accounts/{account.get_firebase_token()}/',
						                      {"Wins": account.get_wins(), "Points": account.get_points()})
				elif act == "L":
					curs.execute("UPDATE Accounts SET Loses = (?) WHERE Username = (?)",
					             (account.get_loses(), account.get_username()))
					if self.__is_online_database:
						self.__firebase.put(f'Accounts/{account.get_firebase_token()}/', 'Loses', account.get_loses())
				elif act == "E":
					curs.execute("UPDATE Accounts SET Draws = (?), Points = (?) WHERE Username = (?)",
					             (account.get_loses(), account.get_points(), account.get_username()))
					if self.__is_online_database:
						self.__firebase.patch(f'Accounts/{account.get_firebase_token()}/',
						                      {'Draws': account.get_draws(), "Points": account.get_points()})
				elif act == "C":
					curs.execute("UPDATE Accounts SET Color = (?) WHERE Username = (?)",
					             (account.get_color(), account.get_username()))
					if self.__is_online_database:
						self.__firebase.put(f'Accounts/{account.get_firebase_token()}/',
						                    'Color', account.get_color())
				elif act == "B":
					curs.execute("UPDATE Accounts SET Bandate = (?) WHERE Username = (?)",
					             (account.get_ban_date(), account.get_username()))
					if self.__is_online_database:
						self.__firebase.put(f"Accounts/{account.get_firebase_token()}/",
						                    "Bandate", account.get_ban_date())
				self.__accounts_updates_to_table.remove(update)
			conn.commit()
			time.sleep(2)
			
			self.__accounts_list.sort(reverse=True, key=lambda x: x.get_points())
		print("Accounts updater shut down...")
	
	def refresh_bans(self):
		print("Refresh bans run...")
		while not self.__stop_running:
			today = datetime.datetime.replace(datetime.datetime.now(), hour=0, minute=0, second=0)
			banned_list = list(filter(lambda x: x.get_client_status() == "Ban", self.__accounts_list))
			for acc in banned_list:
				day, month, year = [int(x) for x in acc.get_ban_date().split("/")]
				ban_date = datetime.datetime(day=day, month=month, year=year)
				if ban_date <= today:
					acc.free()
			time.sleep(5)
		print("Refresh ban shut down...")
	
	def clients_adder(self):
		"""check if any account should be release from ban"""
		print("Clients adder run...")
		while self.__stop_running is False:
			rlist, _, _ = select([self.__server_socket], [], [], 0)
			if self.__server_socket in rlist and (self.__open_connections is None or
			                                      self.__open_connections.get()):
				new_player_socket, player_address = self.__server_socket.accept()
				threading.Thread(target=self.player_services, args=(new_player_socket, player_address)).start()
		print("Client adder shut down...")
	
	def send_to_client(self, client, encryption, data, account=None):
		encrypted_packet = encryption.encrypt(data)
		try:
			client.send(encrypted_packet)
		except socket.error:
			self.release_client(encryption, client, account)
	
	def receive_from_client(self, client, encryption, account=None):
		try:
			length = client.recv(1)
			if length == b"":
				raise socket.error
			length = ord(length)
			data = encryption.decrypt(client.recv(length).decode())
			return data
		except socket.error:
			self.release_client(encryption, client, account)
	
	def release_client(self, encryption, client, account=None):
		if account is not None:
			account.player_offline()
		client.close()
		self.__n_cryption.remove(encryption.get_n())
		self.__players_label['text'] = \
			f"{int(self.__players_label['text'].split(' ')[0]) - 1} player are online"
		exit()
	
	def player_services(self, client, address):
		"""
		all the services to the clients of the game
		after it gets action code reply accordingly and asked data
		@ - a signal to the client that his account has been deleted
		"""
		encryption = RsaEncryption()
		while encryption.get_n() in self.__n_cryption:
			encryption = RsaEncryption()
		self.__n_cryption.append(encryption.get_n())
		pk_to_send = encode(','.join([str(i) for i in encryption.get_public()]).encode(), 'base64')[::-1]
		pk_to_send = chr(len(pk_to_send)).encode() + pk_to_send
		client.send(pk_to_send)
		
		key_length = ord(client.recv(1))
		encryption.set_partner_public_key([int(x) for x in decode
		(client.recv(key_length)[::-1], 'base64').decode().split(',')])
		
		account = self.allocate_account(client, encryption)
		if account is None:
			client.close()
			return
		self.__players_label['text'] = \
			f"{int(self.__players_label['text'].split(' ')[0]) + 1} players are online"
		while not self.__stop_running:
			if account not in self.__accounts_list:  # account deleted
				self.send_to_client(client, encryption, "@")
				self.__n_cryption.remove(encryption.get_n())
				self.__players_label['text'] = \
					f"{int(self.__players_label['text'].split(' ')[0]) - 1} player are online"
				break
			elif account.get_client_status() == "Ban":
				self.send_to_client(client, encryption, "!")
				self.send_to_client(client, encryption, account.get_ban_date())
				self.__n_cryption.remove(encryption.get_n())
				self.__players_label['text'] = \
					f"{int(self.__players_label['text'].split(' ')[0]) - 1} player are online"
				break
			rlist, _, _ = select([client], [], [], 0)
			if client in rlist:
				request = self.receive_from_client(client, encryption, account).split(" ")
				if request[0] == "exit":
					self.release_client(encryption, client, account)
				
				elif request[0] == "GetColor":
					self.send_to_client(client, encryption, account.get_color(), account)
				
				elif request[0] == "SetColor":
					account.update_color(request[1])
					self.__accounts_updates_to_table.append([account, "C"])
				
				elif request[0] == "rating":
					rating = self.get_player_and_champ_rate(account)
					self.send_to_client(client, encryption, rating, account)
				
				elif request[0] == "game":
					mode_code = int(request[1])
					self.make_battle(account, client, mode_code, address, encryption)
		client.close()
	
	def allocate_account(self, player_socket, encryption):
		account = None
		while not self.__stop_running:
			rlist, _, _ = select([player_socket], [], [], 0)
			if player_socket in rlist:
				request = self.receive_from_client(player_socket, encryption).split(" ")
				if request[0] == "exit":
					return None
				#  sending the data from client for identification
				elif request[0] == "Signup":
					account = self.confirm_register(player_socket, request[1], encryption)
				elif request[0] == "login":
					account = self.player_login(player_socket, request[1], encryption)
				if account is not None:
					return account
	
	def get_player_and_champ_rate(self, account):
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
			               f" {self.__accounts_list.index(account)}"
		return information
	
	def calculate_bonus_points(self, enemy_username):
		if enemy_username == self.__accounts_list[0].get_username():
			return 3
		elif enemy_username == self.__accounts_list[1].get_username():
			return 2
		elif len(self.__accounts_list) >= 3 and enemy_username == self.__accounts_list[2].get_usermame():
			return 1
		return 0
	
	def make_battle(self, account, player, mode_code, address, encryption):
		if not self.__open_battlefields.get():  # Battlefields are locked
			self.send_to_client(player, encryption, "#", account)
			return
		elif self.__open_battlefields is not None:
			self.send_to_client(player, encryption, "$", account)
		if mode_code == self.LIFE_MODE:
			is_need_release = self.life_battle_request(address, player, account, encryption)
		else:
			is_need_release = self.time_battle_request(address, player, account, encryption)
		if is_need_release is True:  # player disconnect
			self.release_client(encryption, player, account)
		elif is_need_release is False:  # clients backs to menu screen
			return
		while True:
			if self.__stop_running:
				player.close()
				exit()  # server shut down
			if account not in self.__accounts_list:
				account.set_battlefield_id(0)
				self.send_to_client(player, encryption, "@")  # account deleted
				self.__n_cryption.remove(encryption.get_n())
				self.__players_label['text'] = \
					f"{int(self.__players_label['text'].split(' ')[0]) - 1} player are online"
				break
			if account.get_client_status() == "Ban":
				account.set_battlefield_id(0)
				self.send_to_client(player, encryption, "!")
				self.send_to_client(player, encryption, account.get_ban_date())
				self.__n_cryption.remove(encryption.get_n())
				self.__players_label['text'] = \
					f"{int(self.__players_label['text'].split(' ')[0]) - 1} player are online"
				break
			rlist, _, _ = select([player], [], [], 0)
			if player in rlist:
				outcome = ""
				try:
					outcome = player.recv(1)
					if outcome == b"":
						raise socket.error
					outcome = encryption.decrypt(player.recv(ord(outcome)).decode())
				except socket.error:
					account.set_battlefield_id(0)
					account.add_lose()
					self.release_client(encryption, player, account)
				act = None
				account.set_battlefield_id(0)
				if outcome == "exit":  # client exit the game
					self.__accounts_updates_to_table.append([account, "L"])
					player.close()
					account.add_lose()
					account.player_offline()
					return True
				elif outcome == "Victory":
					act = "W"
					account.add_win()
					enemy_username = self.receive_from_client(player, encryption, account)
					account.get_bonus(self.calculate_bonus_points(enemy_username))
				elif outcome == "Defeat":
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
	
	def life_battle_request(self, address, client_socket, account, encryption):
		"""
		handle the request of the client for making a new life match
		"""
		if self.__life_battle_ip == "":  # player create connection
			self.send_to_client(client_socket, encryption, "T", account)
			self.__life_map_data = str(choice(self.__maps_list))
			battle_id = self.__new_life_battlefield_id = self.find_next_battlefield(self.LIFE_MODE)
			self.__life_battle_ip = address[0]
			while self.__new_life_battlefield_id != 0:  # another player has been found
				rlist, _, _ = select([client_socket], [], [], 0)
				if client_socket in rlist:
					try:
						message = client_socket.recv(1)
						if message == b"":
							raise socket.error
						message = encryption.decrypt(client_socket.recv(ord(message)).decode())
					except socket.error:
						self.__life_battle_ip = ""
						return True
					if message == "exit":  # player disconnect
						self.__life_battle_ip = ""
						return True
					elif message == "%":  # player doesn't wait for match anymore
						self.__life_battle_ip = ""
						return False
				if not self.__open_battlefields.get():
					client_socket.send(b"##")  # New battles are close
					self.__life_battle_ip = ""
					return False
				if self.__stop_running:
					client_socket.close()
					exit()
			account.set_battlefield_id(battle_id)
			try:
				if not self.__open_battlefields.get():
					client_socket.send(b"##")  # New battles are close
					self.__life_battle_ip = ""
					return False
				client_socket.send(encryption.encrypt_map_data(self.__life_map_data))
			except socket.error:
				account.set_battlefield_id(0)
				self.release_client(encryption, client_socket, account)
		
		else:  # second player
			ip = self.__life_battle_ip
			self.__life_battle_ip = ""  # players make communication, can start another battle
			account.set_battlefield_id(self.__new_life_battlefield_id)
			self.__new_life_battlefield_id = 0
			try:
				client_socket.send(encryption.encrypt("F"))
				if not self.__open_battlefields.get():  # New battles are close
					client_socket.send(encryption.encrypt("0.0.0.0"))  # indefinite ip address
					client_socket.send(b"##")
					return False
				client_socket.send(encryption.encrypt(ip))
				client_socket.send(encryption.encrypt_map_data(self.__life_map_data))
			except socket.error:
				self.__life_battle_ip = ""
				account.set_battlefield_id(0)
				self.release_client(encryption, client_socket, account)
	
	def time_battle_request(self, address, client_socket, account, encryption):
		"""
		handle the request of the client for making a new time match
		"""
		if self.__time_battle_ip == "":  # player create connection
			self.send_to_client(client_socket, encryption, "T", account)
			self.__time_map_data = str(choice(self.__maps_list))
			battle_id = self.__new_time_battlefield_id = self.find_next_battlefield(self.TIME_MODE)
			self.__time_battle_ip = address[0]
			while self.__new_time_battlefield_id != 0:  # another player has been found
				rlist, _, _ = select([client_socket], [], [], 0)
				if client_socket in rlist:
					try:
						message = client_socket.recv(1)
						if message == b"":
							raise socket.error
						message = encryption.decrypt(client_socket.recv(ord(message)).decode())
					except socket.error:
						self.__time_battle_ip = ""
						return True
					if message == "exit":  # player disconnect
						self.__time_battle_ip = ""
						return True
					elif message == "%":  # player doesn't wait for match anymore
						self.__time_battle_ip = ""
						return False
				if not self.__open_battlefields.get():
					client_socket.send(b"##")  # New battles are close
					self.__time_battle_ip = ""
					return False
				if self.__stop_running:
					client_socket.close()
					exit()
			account.set_battlefield_id(battle_id)
			try:
				if not self.__open_battlefields.get():
					client_socket.send(b"##")  # New battles are close
					self.__time_battle_ip = ""
					return False
				client_socket.send(encryption.encrypt_map_data(self.__time_map_data))
			except socket.error:
				account.set_battlefield_id(0)
				self.release_client(encryption, client_socket, account)
		
		else:  # second player
			ip = self.__time_battle_ip
			self.__time_battle_ip = ""  # players make communication, can start another battle
			account.set_battlefield_id(self.__new_time_battlefield_id)
			self.__new_time_battlefield_id = 0
			try:
				client_socket.send(encryption.encrypt("F"))
				if not self.__open_battlefields.get():  # New battles are close
					client_socket.send(encryption.encrypt("0.0.0.0"))  # indefinite ip address
					client_socket.send(b"##")
					return False
				client_socket.send(encryption.encrypt(ip))
				client_socket.send(encryption.encrypt_map_data(self.__time_map_data))
			except socket.error:
				self.__time_battle_ip = ""
				account.set_battlefield_id(0)
				self.release_client(encryption, client_socket, account)
	
	def confirm_register(self, client, account, encryption):
		"""
		check if the asked username and password doesn't exist in the accounts list
		if they don't, send Y to client and register the new player
		if there is already an account, send N to the client
		parameters:
			client - socket, the socket which used for communicate with the client
		"""
		new_player_data = account.split(",")
		exist = False
		for acc in self.__accounts_list:
			if acc.get_username() == new_player_data[0]:
				exist = True
		if exist:
			self.send_to_client(client, encryption, "N")
		else:
			self.send_to_client(client, encryption, "Y")
			new_account = self.register_new_player(new_player_data)
			print("A new player signed up, is username is: " + new_player_data[0])
			return new_account
	
	def register_new_player(self, new_account_data, is_admin_command=False):
		"""add the new account to the list and insert it to the databases
		if the request is from the client, automatically set his status to online
		parameters:
			new_account_data - list, the username and the password
			is_online - bool, tells if the player connected now
		"""
		firebase_token = ""
		if self.__is_online_database:
			data = {"Username": new_account_data[0], "Password": new_account_data[1],
			        "Wins": 0, "Loses": 0, "Draws": 0, "Points": 0, "Color": "4d784e", "Bandate": "00/00/0000"}
			firebase_token = self.__firebase.post("Accounts", data)['name']
		
		conn = connect("my database.db")
		cursor = conn.cursor()
		cursor.execute("INSERT INTO Accounts VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
		               (new_account_data[0], new_account_data[1], 0, 0, 0, 0,
		                "4d784e", "00/00/0000", firebase_token))
		conn.commit()
		conn.close()
		new_account = Account(new_account_data[0], new_account_data[1],
		                      0, 0, 0, 0, "4d784e", "00/00/0000", firebase_token)
		if not is_admin_command:
			new_account.player_online()
		self.__accounts_list.append(new_account)
		self.__accounts_list.sort(reverse=True, key=lambda x: x.get_points())
		return new_account
	
	def player_login(self, client, account, encryption):
		""""
		handle to signing in of the client and send:
		T - if taken    B - if Banned
		O - if ok       F - if doesn't exist
		arguments:
			client - socket, the socket which used to communicate with client
		"""
		account_to_check = account.split(",")
		exist = False
		for account in self.__accounts_list:
			if account.get_username() == account_to_check[0] and account.get_password() == account_to_check[1]:
				# found match
				exist = True
				if account.get_client_status() == "On":  # this account is already taken
					self.send_to_client(client, encryption, "T")
				elif account.get_client_status() == "Ban":
					self.send_to_client(client, encryption, "B")
					self.send_to_client(client, encryption, account.get_ban_date())
				else:
					self.send_to_client(client, encryption, "O")  # can use this account
					account.player_online()
					return account
		if not exist:
			self.send_to_client(client, encryption, "F")  # desired account does not exist
	
	def find_next_battlefield(self, battle_mode_id):
		"""
		finds the next first available battlefield and return it's number
		arguments:
			mode_code - int, for determine for which mode need to find
		"""
		if battle_mode_id == self.LIFE_MODE:
			my_battlefield_ids = [x.get_battlefield_id() for x in self.__accounts_list
			                      if x.get_battlefield_id() >= 1 and x.get_battlefield_id() % 2]
			if my_battlefield_ids:  # not empty list
				min_id = min(my_battlefield_ids)
				if min_id == 1:
					return max(my_battlefield_ids) + 2
				else:
					return min_id - 2
			else:
				return 1
		else:
			my_battlefield_ids = [x.get_battlefield_id() for x in self.__accounts_list
			                      if x.get_battlefield_id() >= 1 and not (x.get_battlefield_id() % 2)]
			if my_battlefield_ids:  # not empty list
				min_id = min(my_battlefield_ids)
				if min_id == 2:
					return max(my_battlefield_ids) + 2
				else:
					return min_id - 2
			else:
				return 2


def main():
	server = Server()
	server.active()


if __name__ == '__main__':
	main()
