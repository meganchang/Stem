"""
Unit tests for stem.descriptor.extrainfo_descriptor.
"""

import datetime
import unittest
from stem.descriptor.extrainfo_descriptor import ExtraInfoDescriptor, DirResponses, DirStats

CRYPTO_BLOB = """
K5FSywk7qvw/boA4DQcqkls6Ize5vcBYfhQ8JnOeRQC9+uDxbnpm3qaYN9jZ8myj
k0d2aofcVbHr4fPQOSST0LXDrhFl5Fqo5um296zpJGvRUeO6S44U/EfJAGShtqWw
7LZqklu+gVvhMKREpchVqlAwXkWR44VENm24Hs+mT3M=
"""

EXTRAINFO_DESCRIPTOR_ATTR = (
  ("extra-info", "ninja B2289C3EAB83ECD6EB916A2F481A02E6B76A0A48"),
  ("published", "2012-05-05 17:03:50"),
  ("router-signature", "\n-----BEGIN SIGNATURE-----%s-----END SIGNATURE-----" % CRYPTO_BLOB),
)

def _make_descriptor(attr = None, exclude = None):
  """
  Constructs a minimal extrainfo descriptor with the given attributes.
  
  Arguments:
    attr (dict)     - keyword/value mappings to be included in the descriptor
    exclude (list)  - mandatory keywords to exclude from the descriptor
  
  Returns:
    str with customized descriptor content
  """
  
  descriptor_lines = []
  if attr is None: attr = {}
  if exclude is None: exclude = []
  attr = dict(attr) # shallow copy since we're destructive
  
  for keyword, value in EXTRAINFO_DESCRIPTOR_ATTR:
    if keyword in exclude: continue
    elif keyword in attr:
      value = attr[keyword]
      del attr[keyword]
    
    # if this is the last entry then we should dump in any unused attributes
    if keyword == "router-signature":
      for attr_keyword, attr_value in attr.items():
        descriptor_lines.append("%s %s" % (attr_keyword, attr_value))
    
    descriptor_lines.append("%s %s" % (keyword, value))
  
  return "\n".join(descriptor_lines)

class TestExtraInfoDescriptor(unittest.TestCase):
  def test_minimal_extrainfo_descriptor(self):
    """
    Basic sanity check that we can parse an extrainfo descriptor with minimal
    attributes.
    """
    
    desc_text = _make_descriptor()
    desc = ExtraInfoDescriptor(desc_text)
    
    self.assertEquals("ninja", desc.nickname)
    self.assertEquals("B2289C3EAB83ECD6EB916A2F481A02E6B76A0A48", desc.fingerprint)
    self.assertTrue(CRYPTO_BLOB in desc.signature)
  
  def test_unrecognized_line(self):
    """
    Includes unrecognized content in the descriptor.
    """
    
    desc_text = _make_descriptor({"pepperjack": "is oh so tasty!"})
    desc = ExtraInfoDescriptor(desc_text)
    self.assertEquals(["pepperjack is oh so tasty!"], desc.get_unrecognized_lines())
  
  def test_proceeding_line(self):
    """
    Includes a line prior to the 'extra-info' entry.
    """
    
    desc_text = "exit-streams-opened port=80\n" + _make_descriptor()
    self._expect_invalid_attr(desc_text)
  
  def test_trailing_line(self):
    """
    Includes a line after the 'router-signature' entry.
    """
    
    desc_text = _make_descriptor() + "\nexit-streams-opened port=80"
    self._expect_invalid_attr(desc_text)
  
  def test_extrainfo_line_missing_fields(self):
    """
    Checks that validation catches when the extra-info line is missing fields
    and that without validation both the nickname and fingerprint are left as
    None.
    """
    
    test_entries = (
      "ninja",
      "ninja ",
      "B2289C3EAB83ECD6EB916A2F481A02E6B76A0A48",
      " B2289C3EAB83ECD6EB916A2F481A02E6B76A0A48",
    )
    
    for entry in test_entries:
      desc_text = _make_descriptor({"extra-info": entry})
      desc = self._expect_invalid_attr(desc_text, "nickname")
      self.assertEquals(None, desc.nickname)
      self.assertEquals(None, desc.fingerprint)
  
  def test_geoip_db_digest(self):
    """
    Parses the geoip-db-digest line with valid and invalid data.
    """
    
    geoip_db_digest = "916A3CA8B7DF61473D5AE5B21711F35F301CE9E8"
    desc_text = _make_descriptor({"geoip-db-digest": geoip_db_digest})
    desc = ExtraInfoDescriptor(desc_text)
    self.assertEquals(geoip_db_digest, desc.geoip_db_digest)
    
    test_entries = (
      "",
      "916A3CA8B7DF61473D5AE5B21711F35F301CE9E",
      "916A3CA8B7DF61473D5AE5B21711F35F301CE9E88",
      "916A3CA8B7DF61473D5AE5B21711F35F301CE9EG",
      "916A3CA8B7DF61473D5AE5B21711F35F301CE9E-",
    )
    
    for entry in test_entries:
      desc_text = _make_descriptor({"geoip-db-digest": entry})
      self._expect_invalid_attr(desc_text, "geoip_db_digest", entry)
  
  def test_cell_circuits_per_decile(self):
    """
    Parses the cell-circuits-per-decile line with valid and invalid data.
    """
    
    test_entries = (
      ("0", 0),
      ("11", 11),
    )
    
    for entry in ("0", "11", "25"):
      desc_text = _make_descriptor({"cell-circuits-per-decile": entry})
      desc = ExtraInfoDescriptor(desc_text)
      self.assertEquals(int(entry), desc.cell_circuits_per_decile)
    
    test_entries = (
      "",
      " ",
      "-5",
      "blarg",
    )
    
    for entry in test_entries:
      desc_text = _make_descriptor({"cell-circuits-per-decile": entry})
      self._expect_invalid_attr(desc_text, "cell_circuits_per_decile")
  
  def test_dir_response_lines(self):
    """
    Parses the dirreq-v2-resp and dirreq-v3-resp lines with valid and invalid
    data.
    """
    
    for keyword in ("dirreq-v2-resp", "dirreq-v3-resp"):
      attr = keyword.replace('-', '_').replace('dirreq', 'dir').replace('resp', 'responses')
      unknown_attr = attr + "_unknown"
      
      test_value = "ok=0,unavailable=0,not-found=984,not-modified=0,something-new=7"
      desc_text = _make_descriptor({keyword: test_value})
      desc = ExtraInfoDescriptor(desc_text)
      self.assertEquals(0, getattr(desc, attr)[DirResponses.OK])
      self.assertEquals(0, getattr(desc, attr)[DirResponses.UNAVAILABLE])
      self.assertEquals(984, getattr(desc, attr)[DirResponses.NOT_FOUND])
      self.assertEquals(0, getattr(desc, attr)[DirResponses.NOT_MODIFIED])
      self.assertEquals(7, getattr(desc, unknown_attr)["something-new"])
      
      test_entries = (
        "ok=-4",
        "ok:4",
        "ok=4.not-found=3",
      )
      
      for entry in test_entries:
        desc_text = _make_descriptor({keyword: entry})
        desc = self._expect_invalid_attr(desc_text)
        self.assertEqual({}, getattr(desc, attr))
        self.assertEqual({}, getattr(desc, unknown_attr))
  
  def test_dir_stat_lines(self):
    """
    Parses the dirreq-v2-direct-dl, dirreq-v3-direct-dl, dirreq-v2-tunneled-dl,
    and dirreq-v3-tunneled-dl lines with valid and invalid data.
    """
    
    for keyword in ("dirreq-v2-direct-dl", "dirreq-v2-direct-dl", "dirreq-v2-tunneled-dl", "dirreq-v2-tunneled-dl"):
      attr = keyword.replace('-', '_').replace('dirreq', 'dir')
      unknown_attr = attr + "_unknown"
      
      test_value = "complete=2712,timeout=32,running=4,min=741,d1=14507,d2=22702,q1=28881,d3=38277,d4=73729,md=111455,d6=168231,d7=257218,q3=319833,d8=390507,d9=616301,something-new=11,max=29917857"
      desc_text = _make_descriptor({keyword: test_value})
      desc = ExtraInfoDescriptor(desc_text)
      self.assertEquals(2712, getattr(desc, attr)[DirStats.COMPLETE])
      self.assertEquals(32, getattr(desc, attr)[DirStats.TIMEOUT])
      self.assertEquals(4, getattr(desc, attr)[DirStats.RUNNING])
      self.assertEquals(741, getattr(desc, attr)[DirStats.MIN])
      self.assertEquals(14507, getattr(desc, attr)[DirStats.D1])
      self.assertEquals(22702, getattr(desc, attr)[DirStats.D2])
      self.assertEquals(28881, getattr(desc, attr)[DirStats.Q1])
      self.assertEquals(38277, getattr(desc, attr)[DirStats.D3])
      self.assertEquals(73729, getattr(desc, attr)[DirStats.D4])
      self.assertEquals(111455, getattr(desc, attr)[DirStats.MD])
      self.assertEquals(168231, getattr(desc, attr)[DirStats.D6])
      self.assertEquals(257218, getattr(desc, attr)[DirStats.D7])
      self.assertEquals(319833, getattr(desc, attr)[DirStats.Q3])
      self.assertEquals(390507, getattr(desc, attr)[DirStats.D8])
      self.assertEquals(616301, getattr(desc, attr)[DirStats.D9])
      self.assertEquals(29917857, getattr(desc, attr)[DirStats.MAX])
      self.assertEquals(11, getattr(desc, unknown_attr)["something-new"])
      
      test_entries = (
        "complete=-4",
        "complete:4",
        "complete=4.timeout=3",
      )
      
      for entry in test_entries:
        desc_text = _make_descriptor({keyword: entry})
        desc = self._expect_invalid_attr(desc_text)
        self.assertEqual({}, getattr(desc, attr))
        self.assertEqual({}, getattr(desc, unknown_attr))
  
  def test_conn_bi_direct(self):
    """
    Parses the conn-bi-direct line with valid and invalid data.
    """
    
    desc_text = _make_descriptor({"conn-bi-direct": "2012-05-03 12:07:50 (500 s) 277431,12089,0,2134"})
    desc = ExtraInfoDescriptor(desc_text)
    self.assertEquals(datetime.datetime(2012, 5, 3, 12, 7, 50), desc.conn_bi_direct_end)
    self.assertEquals(500, desc.conn_bi_direct_interval)
    self.assertEquals(277431, desc.conn_bi_direct_below)
    self.assertEquals(12089, desc.conn_bi_direct_read)
    self.assertEquals(0, desc.conn_bi_direct_write)
    self.assertEquals(2134, desc.conn_bi_direct_both)
    
    test_entries = (
      "",
      "2012-05-03 ",
      "2012-05-03",
      "2012-05-03 12:07:60 (500 s)",
      "2012-05-03 12:07:50 (500s)",
      "2012-05-03 12:07:50 (500 s",
      "2012-05-03 12:07:50 (500 )",
      "2012-05-03 12:07:50 (500 s)11",
      "2012-05-03 12:07:50 (500 s) 277431,12089,0",
      "2012-05-03 12:07:50 (500 s) 277431,12089,0a,2134",
      "2012-05-03 12:07:50 (500 s) -277431,12089,0,2134",
    )
    
    for entry in test_entries:
      desc_text = _make_descriptor({"conn-bi-direct": entry})
      desc = self._expect_invalid_attr(desc_text)
      self.assertEquals(None, desc.conn_bi_direct_end)
      self.assertEquals(None, desc.conn_bi_direct_interval)
      self.assertEquals(None, desc.conn_bi_direct_below)
      self.assertEquals(None, desc.conn_bi_direct_read)
      self.assertEquals(None, desc.conn_bi_direct_write)
      self.assertEquals(None, desc.conn_bi_direct_both)
  
  def test_percentage_lines(self):
    """
    Uses valid and invalid data to tests lines of the form...
    "<keyword>" num%
    """
    
    for keyword in ('dirreq-v2-share', 'dirreq-v3-share'):
      attr = keyword.replace('-', '_').replace('dirreq', 'dir')
      
      test_entries = (
        ("0.00%", 0.0),
        ("0.01%", 0.0001),
        ("50%", 0.5),
        ("100.0%", 1.0),
      )
      
      for test_value, expected_value in test_entries:
        desc_text = _make_descriptor({keyword: test_value})
        desc = ExtraInfoDescriptor(desc_text)
        self.assertEquals(expected_value, getattr(desc, attr))
      
      test_entries = (
        ("", None),
        (" ", None),
        ("100", None),
        ("100.1%", 1.001),
        ("-5%", -0.05),
      )
      
      for entry, expected in test_entries:
        desc_text = _make_descriptor({keyword: entry})
        self._expect_invalid_attr(desc_text, attr, expected)
  
  def test_number_list_lines(self):
    """
    Uses valid and invalid data to tests lines of the form...
    "<keyword>" num,...,num
    """
    
    for keyword in ('cell-processed-cells', 'cell-queued-cells', 'cell-time-in-queue'):
      attr = keyword.replace('-', '_')
      
      test_entries = (
        ("", []),
        (" ", []),
        ("0,0,0", [0.0, 0.0, 0.0]),
        ("2.3,-4.6,8.9,16.12,32.15", [2.3, -4.6, 8.9, 16.12, 32.15]),
      )
      
      for test_value, expected_value in test_entries:
        desc_text = _make_descriptor({keyword: test_value})
        desc = ExtraInfoDescriptor(desc_text)
        self.assertEquals(expected_value, getattr(desc, attr))
      
      test_entries = (
        (",,11", [11.0]),
        ("abc,5.7,def", [5.7]),
        ("blarg", []),
      )
      
      for entry, expected in test_entries:
        desc_text = _make_descriptor({keyword: entry})
        self._expect_invalid_attr(desc_text, attr, expected)
  
  def test_timestamp_lines(self):
    """
    Uses valid and invalid data to tests lines of the form...
    "<keyword>" YYYY-MM-DD HH:MM:SS
    """
    
    for keyword in ('published', 'geoip-start-time'):
      attr = keyword.replace('-', '_')
      
      desc_text = _make_descriptor({keyword: "2012-05-03 12:07:50"})
      desc = ExtraInfoDescriptor(desc_text)
      self.assertEquals(datetime.datetime(2012, 5, 3, 12, 7, 50), getattr(desc, attr))
      
      test_entries = (
        "",
        "2012-05-03 12:07:60",
        "2012-05-03 ",
        "2012-05-03",
      )
      
      for entry in test_entries:
        desc_text = _make_descriptor({keyword: entry})
        self._expect_invalid_attr(desc_text, attr)
  
  def test_timestamp_and_interval_lines(self):
    """
    Uses valid and invalid data to tests lines of the form...
    "<keyword>" YYYY-MM-DD HH:MM:SS (NSEC s)
    """
    
    for keyword in ('cell-stats-end', 'entry-stats-end', 'exit-stats-end', 'bridge-stats-end', 'dirreq-stats-end'):
      end_attr = keyword.replace('-', '_').replace('dirreq', 'dir')
      interval_attr = end_attr[:-4] + "_interval"
      
      desc_text = _make_descriptor({keyword: "2012-05-03 12:07:50 (500 s)"})
      desc = ExtraInfoDescriptor(desc_text)
      self.assertEquals(datetime.datetime(2012, 5, 3, 12, 7, 50), getattr(desc, end_attr))
      self.assertEquals(500, getattr(desc, interval_attr))
      
      test_entries = (
        "",
        "2012-05-03 ",
        "2012-05-03",
        "2012-05-03 12:07:60 (500 s)",
        "2012-05-03 12:07:50 (500s)",
        "2012-05-03 12:07:50 (500 s",
        "2012-05-03 12:07:50 (500 )",
      )
      
      for entry in test_entries:
        desc_text = _make_descriptor({keyword: entry})
        desc = self._expect_invalid_attr(desc_text)
        self.assertEquals(None, getattr(desc, end_attr))
        self.assertEquals(None, getattr(desc, interval_attr))
  
  def test_timestamp_interval_and_value_lines(self):
    """
    Uses valid and invalid data to tests lines of the form...
    "<keyword>" YYYY-MM-DD HH:MM:SS (NSEC s) NUM,NUM,NUM,NUM,NUM...
    """
    
    for keyword in ('read-history', 'write-history', 'dirreq-read-history', 'dirreq-write-history'):
      base_attr = keyword.replace('-', '_').replace('dirreq', 'dir')
      end_attr = base_attr + "_end"
      interval_attr = base_attr + "_interval"
      values_attr = base_attr + "_values"
      
      test_entries = (
        ("", []),
        (" ", []),
        (" 50,11,5", [50, 11, 5]),
      )
      
      for test_values, expected_values in test_entries:
        desc_text = _make_descriptor({keyword: "2012-05-03 12:07:50 (500 s)%s" % test_values})
        desc = ExtraInfoDescriptor(desc_text)
        self.assertEquals(datetime.datetime(2012, 5, 3, 12, 7, 50), getattr(desc, end_attr))
        self.assertEquals(500, getattr(desc, interval_attr))
        self.assertEquals(expected_values, getattr(desc, values_attr))
      
      test_entries = (
        "",
        "2012-05-03 ",
        "2012-05-03",
        "2012-05-03 12:07:60 (500 s)",
        "2012-05-03 12:07:50 (500s)",
        "2012-05-03 12:07:50 (500 s",
        "2012-05-03 12:07:50 (500 )",
        "2012-05-03 12:07:50 (500 s)11",
      )
      
      for entry in test_entries:
        desc_text = _make_descriptor({keyword: entry})
        desc = self._expect_invalid_attr(desc_text)
        self.assertEquals(None, getattr(desc, end_attr))
        self.assertEquals(None, getattr(desc, interval_attr))
        self.assertEquals(None, getattr(desc, values_attr))
  
  def test_port_mapping_lines(self):
    """
    Uses valid and invalid data to tests lines of the form...
    "<keyword>" port=N,port=N,...
    """
    
    for keyword in ('exit-kibibytes-written', 'exit-kibibytes-read', 'exit-streams-opened'):
      attr = keyword.replace('-', '_')
      
      test_entries = (
        ("", {}),
        ("443=100,other=111", {443: 100, 'other': 111}),
        ("80=115533759,443=1777,995=690", {80: 115533759, 443: 1777, 995: 690}),
      )
      
      for test_value, expected_value in test_entries:
        desc_text = _make_descriptor({keyword: test_value})
        desc = ExtraInfoDescriptor(desc_text)
        self.assertEquals(expected_value, getattr(desc, attr))
      
      test_entries = (
        "8000000=115533759",
        "-80=115533759",
        "80=-115533759",
        "=115533759",
        "80=",
        "80,115533759",
      )
      
      for entry in test_entries:
        desc_text = _make_descriptor({keyword: entry})
        self._expect_invalid_attr(desc_text, attr, {})
  
  def test_locale_mapping_lines(self):
    """
    Uses valid and invalid data to tests lines of the form...
    "<keyword>" CC=N,CC=N,...
    """
    
    for keyword in ('dirreq-v2-ips', 'dirreq-v3-ips', 'dirreq-v2-reqs', 'dirreq-v3-reqs', 'geoip-client-origins', 'entry-ips', 'bridge-ips'):
      attr = keyword.replace('-', '_').replace('dirreq', 'dir').replace('reqs', 'requests')
      
      test_entries = (
        ("", {}),
        ("uk=5,de=3,jp=2", {'uk': 5, 'de': 3, 'jp': 2}),
      )
      
      for test_value, expected_value in test_entries:
        desc_text = _make_descriptor({keyword: test_value})
        desc = ExtraInfoDescriptor(desc_text)
        self.assertEquals(expected_value, getattr(desc, attr))
      
      test_entries = (
        "uk=-4",
        "uki=4",
        "uk:4",
        "uk=4.de=3",
      )
      
      for entry in test_entries:
        desc_text = _make_descriptor({keyword: entry})
        self._expect_invalid_attr(desc_text, attr, {})
  
  def _expect_invalid_attr(self, desc_text, attr = None, expected_value = None):
    """
    Asserts that construction will fail due to desc_text having a malformed
    attribute. If an attr is provided then we check that it matches an expected
    value when we're constructed without validation.
    """
    
    self.assertRaises(ValueError, ExtraInfoDescriptor, desc_text)
    desc = ExtraInfoDescriptor(desc_text, validate = False)
    
    if attr:
      # check that the invalid attribute matches the expected value when
      # constructed without validation
      
      self.assertEquals(expected_value, getattr(desc, attr))
    else:
      # check a default attribute
      self.assertEquals("ninja", desc.nickname)
    
    return desc

