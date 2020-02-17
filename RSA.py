import random


class RsaEncryption:
	def __init__(self):
		self.__p = random.randint(2, 409)
		while not self.is_prime(self.__p):
			self.__p = random.randint(2, 409)

		self.__q = random.randint(2, 409)
		while (not self.is_prime(self.__q)) and (self.__q != self.__p and self.__q * self.__p < 1000):
			self.__q = random.randint(2, 409)

		self.__public_key = None
		self.__private_key = None
		self.generate_keypair()
	

	def get_p(self):
		return self.__p

	def get_q(self):
		return self.__q

	def get_public(self):
		return self.__public_key

	def get_private(self):
		return self.__private_key

	def generate_keypair(self):
		n = self.__p * self.__q
		phi = (self.__p - 1) * (self.__q - 1)

		e = random.randrange(2, phi)
		g = self.gcd(e, phi)
		while g != 1:  # confirm e is approved option
			e = random.randrange(2, phi)
			g = self.gcd(e, phi)
		d = self.multiplicative_inverse(e, phi)  # find d
		self.__public_key = (e, n)
		self.__private_key = (d, n)

	@staticmethod
	def is_prime(num):
		if num == 2:
			return True
		if num < 2 or num % 2 == 0:
			return False
		for n in range(3, int(num ** 0.5) + 2, 2):
			if num % n == 0:
				return False
		return True

	@staticmethod
	def gcd(a, b):
		"""return 1 if e and phi(n) are a coprimes"""
		while b != 0:
			a, b = b, a % b
		return a

	@staticmethod
	def multiplicative_inverse(e, phi):
		d = 1
		while True:
			if (d * e) % phi == 1:
				return d
			d += 1

	def encrypt(self, message):
		key, n = self.__public_key
		encrypted_message = []
		for char in message:
			encrypted_message.append(str(ord(char) ** key % n))
		return ' '.join(encrypted_message)

	def decrypt(self, ciphertext):
		key, n = self.__private_key
		message = [int(num) for num in ciphertext.split(" ")]
		return ''.join([chr(num ** key % n) for num in message])


def main():
	pass


if __name__ == '__main__':
	main()
