import pickle
import unittest
import os
import tempfile
from pathlib import Path

from . import FileSessionStorage, PathError, UserSession

class TestFileSessionStorage(unittest.TestCase):
	def setUp(self):
		self.directory_obj = tempfile.TemporaryDirectory()
		self.dir = self.directory_obj.name
	
	def tearDown(self):
		self.directory_obj.cleanup()
	
	def test_path_is_dir_error(self):
		path = Path(os.getcwd())

		act = lambda : FileSessionStorage(path)

		self.assertRaises(PathError, act)
	
	def test_path_dir_exists(self):
		path = Path("/an/insane/path")

		act = lambda : FileSessionStorage(path)

		self.assertRaises(PathError, act)

	def test_save(self):
		path = Path(self.dir, ".pkl")
		storage = FileSessionStorage(path)
		session = UserSession("hostname", "username", "token")

		storage.save(session)

		with open(path, "rb") as file:
			have = pickle.load(file)
			self.assertIsInstance(have, UserSession)
			self.assertEqual(have, session)

	def test_read_none(self):
		path = Path(self.dir, ".pkl")
		storage = FileSessionStorage(path)

		have = storage.read()

		self.assertEqual(have, None)
	
	def test_read(self):
		path = Path(self.dir, ".pkl")
		session = UserSession("hostname", "username", "token")
		with open(path, "wb") as file:
			pickle.dump(session, file)
		storage = FileSessionStorage(path)

		have = storage.read()

		self.assertIsInstance(have, UserSession)
		self.assertEqual(have, session)
	
	def test_drop(self):
		path = Path(self.dir, ".pkl")
		path.unlink(missing_ok = True)
		path.touch()
		storage = FileSessionStorage(path)

		storage.drop()

		self.assertFalse(path.exists())

if __name__ == '__main__':
    unittest.main()