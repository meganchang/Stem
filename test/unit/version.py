"""
Unit tests for the stem.version.Version parsing and class.
"""

import unittest
import stem.version
import stem.util.system

import test.mocking as mocking

TOR_VERSION_OUTPUT = """Mar 22 23:09:37.088 [notice] Tor v0.2.2.35 \
(git-73ff13ab3cc9570d). This is experimental software. Do not rely on it for \
strong anonymity. (Running on Linux i686)
Tor version 0.2.2.35 (git-73ff13ab3cc9570d)."""

class TestVersion(unittest.TestCase):
  def tearDown(self):
    mocking.revert_mocking()
  
  def test_get_system_tor_version(self):
    # Clear the version cache both before and after the test. Without this
    # prior results short circuit the system call, and future calls will
    # provide this mocked value.
    
    stem.version.VERSION_CACHE = {}
    
    def _mock_call(command):
      if command == "tor --version":
        return TOR_VERSION_OUTPUT.splitlines()
      else:
        raise ValueError("stem.util.system.call received an unexpected command: %s" % command)
    
    mocking.mock(stem.util.system.call, _mock_call)
    version = stem.version.get_system_tor_version()
    self.assert_versions_match(version, 0, 2, 2, 35, None)
    
    stem.version.VERSION_CACHE = {}
  
  def test_parsing(self):
    """
    Tests parsing by the Version class constructor.
    """
    
    # valid versions with various number of compontents to the version
    
    version = stem.version.Version("0.1.2.3-tag")
    self.assert_versions_match(version, 0, 1, 2, 3, "tag")
    
    version = stem.version.Version("0.1.2.3")
    self.assert_versions_match(version, 0, 1, 2, 3, None)
    
    version = stem.version.Version("0.1.2-tag")
    self.assert_versions_match(version, 0, 1, 2, None, "tag")
    
    version = stem.version.Version("0.1.2")
    self.assert_versions_match(version, 0, 1, 2, None, None)
    
    # checks an empty tag
    version = stem.version.Version("0.1.2.3-")
    self.assert_versions_match(version, 0, 1, 2, 3, "")
    
    version = stem.version.Version("0.1.2-")
    self.assert_versions_match(version, 0, 1, 2, None, "")
    
    # checks invalid version strings
    self.assertRaises(ValueError, stem.version.Version, "")
    self.assertRaises(ValueError, stem.version.Version, "1.2.3.4nodash")
    self.assertRaises(ValueError, stem.version.Version, "1.2.3.a")
    self.assertRaises(ValueError, stem.version.Version, "1.2.a.4")
    self.assertRaises(ValueError, stem.version.Version, "1x2x3x4")
    self.assertRaises(ValueError, stem.version.Version, "12.3")
    self.assertRaises(ValueError, stem.version.Version, "1.-2.3")
  
  def test_comparison(self):
    """
    Tests comparision between Version instances.
    """
    
    # check for basic incrementing in each portion
    self.assert_version_is_greater("1.1.2.3-tag", "0.1.2.3-tag")
    self.assert_version_is_greater("0.2.2.3-tag", "0.1.2.3-tag")
    self.assert_version_is_greater("0.1.3.3-tag", "0.1.2.3-tag")
    self.assert_version_is_greater("0.1.2.4-tag", "0.1.2.3-tag")
    self.assert_version_is_equal("0.1.2.3-ugg", "0.1.2.3-tag")
    self.assert_version_is_equal("0.1.2.3-tag", "0.1.2.3-tag")
    
    # checks that a missing patch level equals zero
    self.assert_version_is_equal("0.1.2", "0.1.2.0")
    self.assert_version_is_equal("0.1.2-tag", "0.1.2.0-tag")
    
    # checks for missing patch or status
    self.assert_version_is_equal("0.1.2.3-tag", "0.1.2.3")
    self.assert_version_is_greater("0.1.2.3-tag", "0.1.2-tag")
    self.assert_version_is_greater("0.1.2.3-tag", "0.1.2")
    
    self.assert_version_is_equal("0.1.2.3", "0.1.2.3")
    self.assert_version_is_equal("0.1.2", "0.1.2")
  
  def test_nonversion_comparison(self):
    """
    Checks that we can be compared with other types.
    """
    
    test_version = stem.version.Version("0.1.2.3")
    self.assertNotEqual(test_version, None)
    self.assertTrue(test_version > None)
    
    self.assertNotEqual(test_version, 5)
    self.assertTrue(test_version > 5)
  
  def test_string(self):
    """
    Tests the Version -> string conversion.
    """
    
    # checks conversion with various numbers of arguments
    self.assert_string_matches("0.1.2.3-tag")
    self.assert_string_matches("0.1.2.3")
    self.assert_string_matches("0.1.2")
  
  def assert_versions_match(self, version, major, minor, micro, patch, status):
    """
    Asserts that the values for a types.Version instance match the given
    values.
    """
    
    self.assertEqual(version.major, major)
    self.assertEqual(version.minor, minor)
    self.assertEqual(version.micro, micro)
    self.assertEqual(version.patch, patch)
    self.assertEqual(version.status, status)
  
  def assert_version_is_greater(self, first_version, second_version):
    """
    Asserts that the parsed version of the first version is greate than the
    second (also checking the inverse).
    """
    
    version1 = stem.version.Version(first_version)
    version2 = stem.version.Version(second_version)
    self.assertEqual(version1 > version2, True)
    self.assertEqual(version1 < version2, False)
  
  def assert_version_is_equal(self, first_version, second_version):
    """
    Asserts that the parsed version of the first version equals the second.
    """
    
    version1 = stem.version.Version(first_version)
    version2 = stem.version.Version(second_version)
    self.assertEqual(version1, version2)
  
  def assert_string_matches(self, version):
    """
    Parses the given version string then checks that its string representation
    matches the input.
    """
    
    self.assertEqual(version, str(stem.version.Version(version)))

