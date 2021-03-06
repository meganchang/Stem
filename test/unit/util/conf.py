"""
Unit tests for the stem.util.conf class and functions.
"""

import unittest
import stem.util.conf

class TestConf(unittest.TestCase):
  def tearDown(self):
    # clears the config contents
    test_config = stem.util.conf.get_config("unit_testing")
    test_config.clear()
    test_config.clear_listeners()
  
  def test_config_dict(self):
    """
    Tests the config_dict function.
    """
    
    my_config = {
      "bool_value": False,
      "int_value": 5,
      "str_value": "hello",
      "list_value": [],
    }
    
    test_config = stem.util.conf.get_config("unit_testing")
    
    # checks that sync causes existing contents to be applied
    test_config.set("bool_value", "true")
    my_config = stem.util.conf.config_dict("unit_testing", my_config)
    self.assertEquals(True, my_config["bool_value"])
    
    # check a basic synchronize
    test_config.set("str_value", "me")
    self.assertEquals("me", my_config["str_value"])
    
    # synchronize with a type mismatch, should keep the old value
    test_config.set("int_value", "7a")
    self.assertEquals(5, my_config["int_value"])
    
    # changes for a collection
    test_config.set("list_value", "a", False)
    self.assertEquals(["a"], my_config["list_value"])
    
    test_config.set("list_value", "b", False)
    self.assertEquals(["a", "b"], my_config["list_value"])
    
    test_config.set("list_value", "c", False)
    self.assertEquals(["a", "b", "c"], my_config["list_value"])
  
  def test_clear(self):
    """
    Tests the clear method.
    """
    
    test_config = stem.util.conf.get_config("unit_testing")
    self.assertEquals([], test_config.keys())
    
    # tests clearing when we're already empty
    test_config.clear()
    self.assertEquals([], test_config.keys())
    
    # tests clearing when we have contents
    test_config.set("hello", "world")
    self.assertEquals(["hello"], test_config.keys())
    
    test_config.clear()
    self.assertEquals([], test_config.keys())
  
  def test_synchronize(self):
    """
    Tests the synchronize method.
    """
    
    my_config = {
      "bool_value": False,
      "int_value": 5,
      "str_value": "hello",
      "list_value": [],
      "map_value": {},
    }
    
    test_config = stem.util.conf.get_config("unit_testing")
    test_config.set("bool_value", "true")
    test_config.set("int_value", "11")
    test_config.set("str_value", "world")
    test_config.set("list_value", "a", False)
    test_config.set("list_value", "b", False)
    test_config.set("list_value", "c", False)
    test_config.set("map_value", "foo => bar")
    
    test_config.synchronize(my_config)
    self.assertEquals(True, my_config["bool_value"])
    self.assertEquals(11, my_config["int_value"])
    self.assertEquals("world", my_config["str_value"])
    self.assertEquals(["a", "b", "c"], my_config["list_value"])
    self.assertEquals({"foo": "bar"}, my_config["map_value"])
  
  def test_synchronize_type_mismatch(self):
    """
    Tests the synchronize method when the config file has missing entries or
    the wrong types.
    """
    
    my_config = {
      "bool_value": False,
      "int_value": 5,
      "str_value": "hello",
      "list_value": [],
      "map_value": {},
    }
    
    test_config = stem.util.conf.get_config("unit_testing")
    test_config.set("bool_value", "hello world")
    test_config.set("int_value", "11a")
    test_config.set("map_value", "foo bar")
    
    test_config.synchronize(my_config)
    self.assertEquals(False, my_config["bool_value"])
    self.assertEquals(5, my_config["int_value"])
    self.assertEquals("hello", my_config["str_value"])
    self.assertEquals([], my_config["list_value"])
    self.assertEquals({}, my_config["map_value"])
  
  def test_listeners(self):
    """
    Tests the add_listener and clear_listeners methods.
    """
    
    listener_received_keys = []
    
    def test_listener(config, key):
      self.assertEquals(config, stem.util.conf.get_config("unit_testing"))
      listener_received_keys.append(key)
    
    test_config = stem.util.conf.get_config("unit_testing")
    test_config.add_listener(test_listener)
    
    self.assertEquals([], listener_received_keys)
    test_config.set("hello", "world")
    self.assertEquals(["hello"], listener_received_keys)
    
    test_config.clear_listeners()
    
    test_config.set("foo", "bar")
    self.assertEquals(["hello"], listener_received_keys)
  
  def test_unused_keys(self):
    """
    Tests the unused_keys method.
    """
    
    test_config = stem.util.conf.get_config("unit_testing")
    test_config.set("hello", "world")
    test_config.set("foo", "bar")
    test_config.set("pw", "12345")
    
    test_config.get("hello")
    test_config.get_value("foo")
    
    self.assertEquals(set(["pw"]), test_config.unused_keys())
    
    test_config.get("pw")
    self.assertEquals(set(), test_config.unused_keys())
  
  def test_get(self):
    """
    Tests the get and get_value methods.
    """
    
    test_config = stem.util.conf.get_config("unit_testing")
    test_config.set("bool_value", "true")
    test_config.set("int_value", "11")
    test_config.set("float_value", "11.1")
    test_config.set("str_value", "world")
    test_config.set("list_value", "a", False)
    test_config.set("list_value", "b", False)
    test_config.set("list_value", "c", False)
    test_config.set("map_value", "foo => bar")
    
    # check that we get the default for type mismatch or missing values
    
    self.assertEquals(5, test_config.get("foo", 5))
    self.assertEquals(5, test_config.get("bool_value", 5))
    
    # checks that we get a string when no default is supplied
    
    self.assertEquals("11", test_config.get("int_value"))
    
    # exercise type casting for each of the supported types
    
    self.assertEquals(True, test_config.get("bool_value", False))
    self.assertEquals(11, test_config.get("int_value", 0))
    self.assertEquals(11.1, test_config.get("float_value", 0.0))
    self.assertEquals("world", test_config.get("str_value", ""))
    self.assertEquals(["a", "b", "c"], test_config.get("list_value", []))
    self.assertEquals(("a", "b", "c"), test_config.get("list_value", ()))
    self.assertEquals({"foo": "bar"}, test_config.get("map_value", {}))
    
    # the get_value is similar, though only provides back a string or list
    
    self.assertEquals("c", test_config.get_value("list_value"))
    self.assertEquals(["a", "b", "c"], test_config.get_value("list_value", multiple = True))
    
    self.assertEquals(None, test_config.get_value("foo"))
    self.assertEquals("hello", test_config.get_value("foo", "hello"))
  
  def test_csv(self):
    """
    Tests the get_str_csv and get_int_csv methods.
    """
    
    test_config = stem.util.conf.get_config("unit_testing")
    test_config.set("str_csv_value", "hello, world")
    test_config.set("int_csv_value", "1, 2, 3")
    test_config.set("not_a_csv_value", "blarg I say!")
    
    self.assertEquals(["hello", "world"], test_config.get_str_csv("str_csv_value"))
    self.assertEquals(["1", "2", "3"], test_config.get_str_csv("int_csv_value"))
    self.assertEquals(["blarg I say!"], test_config.get_str_csv("not_a_csv_value"))
    self.assertEquals(None, test_config.get_str_csv("not_a_csv_value", count = 5))
    
    self.assertEquals(None, test_config.get_int_csv("str_csv_value"))
    self.assertEquals([1, 2, 3], test_config.get_int_csv("int_csv_value"))
    self.assertEquals(None, test_config.get_int_csv("int_csv_value", min_value = 4))
    self.assertEquals(None, test_config.get_int_csv("not_a_csv_value"))

