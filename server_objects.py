class Account:
	"""The class used by the server to organize the player's data and manage them, also used
		for providing another security layer against SQL injections when getting requests from clients"""
	def __init__(self, username, password, wins, loses, draws, points, color,
	             bandate, firebase_token):
		self.__username = username  # account's username
		self.__password = password  # account's password
		self.__wins = wins  # number of wins
		self.__loses = loses  # number of loses
		self.__draws = draws  # number of ties
		self.__points = points  # all the points the account gathers
		self.__favorite_color = color  # tank's color
		self.__battlefield_id = 0  # the number of the arena the player fights in
		self.__ban_date = bandate  # until then account is banned
		self.__firebase_token = firebase_token
		if self.__ban_date != "00/00/0000":  # account is banned
			self.__client_status = "Ban"
		else:  # account isn't banned
			self.__client_status = "Offline"
	
	def player_online(self):
		self.__client_status = "Online"
	
	def player_offline(self):
		self.__client_status = "Offline"
	
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
		"""Clean the data of the account to default settings"""
		self.__wins = 0
		self.__loses = 0
		self.__draws = 0
		self.__points = 0
		self.__favorite_color = "4d784e"
		self.__ban_date = "00/00/0000"
		if self.__client_status == "Ban":
			self.__client_status = "Offline"
	
	def set_ban_until(self, new_date):
		"""set a new ban date
		parameters:
			new_date: type string, the new date to set
		"""
		self.__ban_date = new_date
		self.__client_status = "Ban"
	
	def free(self):
		"""free the account from being banned"""
		self.__ban_date = "00/00/0000"
		self.__client_status = "Offline"
	
	def get_bonus(self, bonus):
		"""account receive a bonus by kill of the 3 best players"""
		self.__points += bonus
	
	def add_win(self):
		self.__wins += 1
		self.__points += 2
	
	def add_lose(self):
		self.__loses += 1
	
	def add_draws(self):
		self.__draws += 1
		self.__points += 1
	
	def update_color(self, newcolor):
		self.__favorite_color = newcolor
	
	def __str__(self):
		"""make a string to describe all the account members"""
		return f"{self.__username} {self.__password} " \
		       f"{self.__wins} {self.__loses} {self.__draws} {self.__points} " \
		       f"{self.__favorite_color} {self.__client_status} " \
		       f"{self.__ban_date} {self.__battlefield_id}"


class Map:
	"""As the Account class, organizes the maps data for the server to access and manage them
	in this version of the project there is only one creator - the admin.
	However, the foundation for multiple creators (like players) already exist"""
	def __init__(self, creator, map_name, map_id, walls, players_locations, netoken):
		self.__creator = creator  # the creator of the map, for now there is only "<admin>"
		self.__map_name = map_name  # also the map image's file name
		self.__map_id = map_id  # the primary value of each map, (for identify)
		self.__walls = walls
		self.__players_locations = players_locations
		self.__firebase_token = netoken  # the token of firebase
	
	def __str__(self):
		"""generates a string of the relevant information about the map to sending to players"""
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
