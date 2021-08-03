import os
import pickle

from unittest import TestCase
from test_utils import test_setup

from config_dir import config

class PersistentCoachProcessor:
    def __init__(self, objects_file_path=None):
        self.object_file_exists = None
        self.objects_file_path = objects_file_path

        self.is_initialized()

        if self.object_file_exists:
            self.objects_dict = self._get_existing_objects()

    def is_initialized(self):
        if self.object_file_exists is None:
            self.object_file_exists = os.path.isfile(self.objects_file_path)
        return self.object_file_exists

    def initialize(self, objects):
        if self.object_file_exists:
            raise RuntimeError("Objects have already been initialized, to reset delete the associated file and flag.")

        if not isinstance(objects, dict):
            raise ValueError("Objects should be a dict.")

        self.objects_dict = objects
        self._persist_objects()

    def object_processed(self, key):
        del self.objects_dict[key]
        self._persist_objects()

    def _persist_objects(self):
        temp_file_path = self.objects_file_path + ".temp"
        with open(temp_file_path, "wb+") as temp_file:
            pickle.dump(self.objects_dict, temp_file, protocol=pickle.HIGHEST_PROTOCOL)
        os.replace(temp_file_path, self.objects_file_path)

    def _get_existing_objects(self):
        if not os.path.isfile(self.objects_file_path):
            raise RuntimeError("Get existing objects should never be called when objects haven't been created.")

        with open(self.objects_file_path, "rb+") as objects_file:
            return pickle.load(objects_file)


class _TestPersistentCoachProcessor(TestCase):
    def setUp(self):
        test_setup()
        objects_file_path = config.read("TEST", "TEST_OBJECTS_PATH")
        if os.path.exists(objects_file_path):
            os.remove(objects_file_path)

    def test_construct(self):
        objects_file_path = config.read("TEST", "TEST_OBJECTS_PATH")

        self.assertEqual(os.path.isfile(objects_file_path), False)
        lcs_pp = PersistentCoachProcessor(
            objects_file_path=objects_file_path
        )
        lcs_pp.initialize({"hi": "hi", "there": "there"})
        self.assertEqual(os.path.isfile(objects_file_path), True)

        with open(objects_file_path, "rb") as objects_file:
            objects_dict = pickle.load(objects_file)
            self.assertTrue("hi" in objects_dict)
            self.assertTrue("there" in objects_dict)

    def test_process(self):
        objects_file_path = config.read("TEST", "TEST_OBJECTS_PATH")
        pp = PersistentCoachProcessor(
            objects_file_path=objects_file_path,
        )
        pp.initialize({"hi": "hi", "there": "there"})
        pp.object_processed("hi")
        with open(objects_file_path, "rb") as objects_file:
            objects_dict = pickle.load(objects_file)
            self.assertTrue("hi" not in objects_dict)
            self.assertTrue("there" in objects_dict)

        pp2 = PersistentCoachProcessor(
            objects_file_path=objects_file_path
        )
        self.assertEqual(pp2.is_initialized(), True)
        with open(objects_file_path, "rb") as objects_file:
            objects_dict = pickle.load(objects_file)
            self.assertTrue("hi" not in objects_dict)
            self.assertTrue("there" in objects_dict)
