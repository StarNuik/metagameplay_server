import unittest

from . import UserSession

class TestUserSession(unittest.TestCase):
	def test_fields(self):
		args = ["hostname", "username", "token"]
		session = UserSession(args[0], args[1], args[2])

		self.assertEqual(session.hostname, args[0])
		self.assertEqual(session.username, args[1])
		self.assertEqual(session.token, args[2])

if __name__ == '__main__':
    unittest.main()