import random

# 97.5% probability of matching numbers


def is_prime(num):
	if num == 2:
		return True
	if num < 2 or num % 2 == 0:
		return False
	for n in range(3, int(num ** 0.5) + 2, 2):
		if num % n == 0:
			return False
	return True


def gcd(a, b):
	"""return 1 if e and phi(n) are a coprimes"""
	while b != 0:
		a, b = b, a % b
	return a


def multiplicative_inverse(e, phi):
	d = 1
	while True:
		if (d * e) % phi == 1:
			return d
		d += 1


def generate_keypair(p, q):
	if not (is_prime(p) and is_prime(q)):
		raise ValueError('Both numbers must be prime.')
	elif p == q:
		raise ValueError('p and q cannot be equal')

	n = p * q
	phi = (p - 1) * (q - 1)

	e = random.randrange(2, phi)
	g = gcd(e, phi)
	while g != 1:
		e = random.randrange(2, phi)
		g = gcd(e, phi)
	d = multiplicative_inverse(e, phi)
	return (e, n), (d, n)


def encrypt(pk, message):
	key, n = pk
	encrypted_message = []
	for char in message:
		encrypted_message.append(str(ord(char) ** key % n))
	return ' '.join(encrypted_message)


def decrypt(pk, ciphertext):
	key, n = pk
	message = [int(num) for num in ciphertext.split(" ")]
	return ''.join([chr(num ** key % n) for num in message])


def main():
	p, q = 2, 409  # Top prime numbers
	public, private = generate_keypair(p, q)
	print(public, private)
	message = "hello world"
	en = encrypt(public, message)
	dec = decrypt(private, en)
	print(f"the message is: {message}")
	print(f"the encrypted message is: {en}")
	print(f"the decrypted message is: {dec}")


if __name__ == '__main__':
	main()
