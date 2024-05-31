import random
from re import findall


class RsaEncryption:
	"""The encryption and decryption of server-client communication, using simple
	principles and logic of RSA, (uses small prime numbers)
	the characters are encrypted by their ASCII value A-65, B-66 etc'
	except the map coordinates that the server sends, the format is
	the same but the encryption changes the coordinates themselves
	"""
	def __init__(self):
		"""generates prime numbers q and p and build a public and private key
		p and q are between 2-409 for avoid of slowing down the game
		"""
		self.__p = random.randint(2, 409)
		while not self._is_prime(self.__p):
			self.__p = random.randint(2, 409)
		
		self.__q = random.randint(2, 409)
		while self.__q == self.__p or not (1000 < self.__q * self.__p < 3000) \
			or not self._is_prime(self.__q):
			self.__q = random.randint(2, 409)
		#  p * q need to be bigger than 1000 for encrypt the map coordinates
		
		self.__n = self.__q * self.__p
		
		self.__public_key = None
		self.__private_key = None
		self._generate_keypair()
		
		self.__partner_public_key = None  # the public key of the other network entity
	
	def set_partner_public_key(self, new):
		"""sets the public key of the other entity in the communication"""
		self.__partner_public_key = new
	
	def get_p(self):
		return self.__p
	
	def get_q(self):
		return self.__q
	
	def get_n(self):
		return self.__n
	
	def get_public(self):
		return self.__public_key
	
	def get_private(self):
		return self.__private_key
	
	def _generate_keypair(self):
		"""generates the public and private key (e, n) (d, n)"""
		phi = (self.__p - 1) * (self.__q - 1)
		
		e = random.randrange(2, phi)
		g = self._gcd(e, phi)
		while g != 1:  # confirm e is approved option
			e = random.randrange(2, phi)
			g = self._gcd(e, phi)
		d = self._multiplicative_inverse(e, phi)  # find d
		self.__public_key = (e, self.__n)
		self.__private_key = (d, self.__n)
	
	@staticmethod
	def _is_prime(num):
		if num == 2:
			return True
		if num < 2 or num % 2 == 0:
			return False
		for n in range(3, int(num ** 0.5) + 2, 2):
			if num % n == 0:
				return False
		return True
	
	@staticmethod
	def _gcd(e, phi):
		"""returns 1 if e and phi(n) are a coprimes relied on Euler's theorem"""
		while phi != 0:
			e, phi = phi, e % phi
		return e
	
	@staticmethod
	def _multiplicative_inverse(e, phi):
		"""returns d such that -> d * e (mod phi(n)) = 1"""
		d = 1
		while True:
			if (d * e) % phi == 1:
				return d
			d += 1
	
	def encrypt(self, message):
		"""encrypts the message to ciphertext (using the partner's public key)
		parameters:
			message: type string, the message to encrypt
		returns:
			bytes, the length of the ciphertext + the ciphertext itself
		"""
		key, n = self.__partner_public_key
		encrypted_message = []
		for char in message:
			encrypted_message.append(str(ord(char) ** key % n))
		encrypted_message = ' '.join(encrypted_message)
		return bytes([len(encrypted_message)]) + encrypted_message.encode()
	
	def decrypt(self, ciphertext):
		"""decrypts the ciphertext to the original message (using the private key)
		parameters:
			ciphertext: type string, the ciphertext to decrypt
		returns:
			string, the original message
		"""
		key, n = self.__private_key
		message = [int(num) for num in ciphertext.split(" ")]
		return ''.join([chr(num ** key % n) for num in message])
	
	def encrypt_map_data(self, map_data):
		"""like the encrypt function but for maps data
		parameters:
			map_data: type string, the information of the map (walls and player positions)
		returns:
			bytes, the length of the ciphertext + the ciphertext itself
		"""
		key, n = self.__partner_public_key
		encrypted_map = []
		walls, players_pos = map_data.split("+")
		
		for wall in walls.split("\n"):  # the walls of the map
			coordinates = findall(r'\d+', wall)
			encrypted_wall = []
			for c in coordinates:
				encrypted_wall.append(str(int(c) ** key % n))
			x = f"{encrypted_wall[0]},{encrypted_wall[1]} {encrypted_wall[2]}" \
				f",{encrypted_wall[3]}"
			encrypted_map.append(x)
			
		coordinates_list = []
		for x in findall(r'\d+', players_pos):  # the players coordinates
			coordinates_list.append(str(int(x) ** key % n))
		players_coordinates = f"{coordinates_list[0]},{coordinates_list[1]}" \
			f" {coordinates_list[2]},{coordinates_list[3]}"
		encrypted_map = ("\n".join(encrypted_map) + "+" + players_coordinates).encode()
		return len(encrypted_map).to_bytes(2, 'little') + encrypted_map
	
	def decrypt_map_data(self, map_ciphertext):
		"""like the encrypt function but for maps data
		parameters:
			map_ciphertext: type string, the ciphertext of the map to decrypt
		returns:
			string, the original map information
		"""
		key, n = self.__private_key
		encrypted_map = []
		walls, players_pos = map_ciphertext.split("+")
		for wall in walls.split("\n"):
			coordinates_list = findall(r'\d+', wall)
			encrypted_wall = []
			for c in coordinates_list:
				encrypted_wall.append(str(int(c) ** key % n))
			walls_coordinates = f"{encrypted_wall[0]},{encrypted_wall[1]}" \
				f" {encrypted_wall[2]},{encrypted_wall[3]}"
			encrypted_map.append(walls_coordinates)
		
		coordinates_list = []
		for x in findall(r'\d+', players_pos):
			coordinates_list.append(str(int(x) ** key % n))
		players_coordinates = f"{coordinates_list[0]},{coordinates_list[1]}" \
			f" {coordinates_list[2]},{coordinates_list[3]}"
		return "\n".join(encrypted_map), players_coordinates


def main():
	X = RsaEncryption()
 

if __name__ == '__main__':
	main()
