class Account:
	def __init__(self, username, password, wins, loses, draws, points, color,
	             bandate, firebase_token):
		"""
		The class used to organize the static accounts data so as the dynamic, also used
		to make kind of defending layer for preventing SQL injection
		argument:
			username - string, the username of the user
			password - string, the password of the user
			wins - int, the number of wining of the user
			loses - int, the number of losing of the user
			draws - int, the number of drawing of the user
			color - string. the color of the user
			bandate - string, the date of ban
			firebase_token - string, the token of the account in the online database
		"""
		self.__username = username
		self.__password = password
		self.__wins = wins
		self.__loses = loses
		self.__draws = draws
		self.__points = points
		self.__favorite_color = color
		self.__battlefield_id = 0
		self.__ban_date = bandate
		self.__firebase_token = firebase_token
		if self.__ban_date != "00/00/0000":
			self.__client_status = "Ban"
		else:
			self.__client_status = "Off"
	
	def player_online(self):
		self.__client_status = "On"
	
	def player_offline(self):
		self.__client_status = "Off"
	
	def get_client_status(self):
		return self.__client_status
	
	def get_username(self):
		return self.__username
	
	def get_password(self):
		return self.__password
	
	def get_wins(self):
		return self.__wins
	
	def get_loses(self):
		return self.__loses
	
	def get_draws(self):
		return self.__draws
	
	def get_color(self):
		return self.__favorite_color
	
	def get_battlefield_id(self):
		return self.__battlefield_id
	
	def get_ban_date(self):
		return self.__ban_date
	
	def get_firebase_token(self):
		return self.__firebase_token
	
	def get_points(self):
		return self.__points
	
	def set_battlefield_id(self, new_battlefield_id):
		self.__battlefield_id = new_battlefield_id
	
	def clean_data(self):
		"""
		Clean the data of the account to default settings
		"""
		self.__wins = 0
		self.__loses = 0
		self.__draws = 0
		self.__points = 0
		self.__favorite_color = "4d784e"
		self.__ban_date = "00/00/0000"
		if self.__client_status == "Ban":
			self.__client_status = "Off"
	
	def set_ban_until(self, new_date):
		"""
		set a new ban date
		argument:
			new_date - string, the new date to set
		"""
		self.__ban_date = new_date
		self.__client_status = "Ban"
	
	def free(self):
		"""
		delete to current ban date and set it to default
		"""
		self.__ban_date = "00/00/0000"
		self.__client_status = "Off"
	
	def get_bonus(self, bonus):
		self.__points += bonus
	
	def add_win(self):
		self.__wins += 1
		self.__points += 2
	
	def add_lose(self):
		self.__loses += 1
	
	def add_draws(self):
		self.__draws += 1
		self.__points += 1
	
	def change_color(self, newcolor):
		"""
		change the current color
		argument:
			newcolor - string, the new color to set
		"""
		self.__favorite_color = newcolor
	
	def __str__(self):
		"""make a string to describe all the account headers"""
		return f"{self.__username} {self.__password} " \
		       f"{self.__wins} {self.__loses} {self.__draws} {self.__points} " \
		       f"{self.__favorite_color} {self.__client_status} " \
		       f"{self.__ban_date} {self.__battlefield_id}"


class Map:
	def __init__(self, creator, map_name, map_id, walls, players_locations, netoken):
		self.__creator = creator
		self.__map_name = map_name
		self.__map_id = map_id
		self.__walls = walls
		self.__players_locations = players_locations
		self.__firebase_token = netoken
	
	def __str__(self):
		s = f"{self.__walls}+{self.__players_locations}"
		return s
	
	def get_name(self):
		return self.__map_name
	
	def get_creator(self):
		return self.__creator
	
	def get_map_id(self):
		return self.__map_id
	
	def get_token(self):
		return self.__firebase_token


def main():
	pass


if __name__ == '__main__':
	main()
