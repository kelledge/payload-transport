import mock
from twisted.trial import unittest

from wsrc.transport import framing

class TestXBeeAPIUnFramer(unittest.TestCase):
  def setUp(self):
    self.valid_at_command_frame = b'\x7e\x00\x04\x08\x52\x4e\x48\x0f'
    self.valid_at_command_resp_frame = b'\x7e\x00\x05\x88\x01\x42\x44\x00\xf0'

    self.valid_frame_in_stream = (
      b'\x01\x02\x03' + 
      self.valid_at_command_frame + 
      b'\x03\x04\x05'
    )
    self.valid_frames = (
      self.valid_at_command_frame + 
      self.valid_at_command_resp_frame
    )
    self.valid_frames_in_stream = (
      b'\x01\x02\x03' +
      self.valid_at_command_frame +
      b'\x04\x05\x06' +
      self.valid_at_command_resp_frame +
      b'\x07\x08\x09'
    )

  def tearDown(self):
    pass

  def runFixture(self, fixture):
    frame_receiver = mock.MagicMock()
    unframer = framing.XBeeAPIUnFramer(target=frame_receiver)
    for b in fixture:
      unframer.send(b)

    return frame_receiver

  def test_detectValidFrame(self):
    frame_receiver = self.runFixture(self.valid_at_command_frame)
    expected_calls = [mock.call(
      length=4,
      contents='\x08\x52\x4e\x48',
      bytesum=0xf0,
      checksum=0x0f
    )]

    actual_calls = frame_receiver.send.call_args_list
    self.assertEqual(actual_calls, expected_calls)    

  def test_detectValidFrameInStream(self):
    frame_receiver = self.runFixture(self.valid_frame_in_stream)
    expected_calls = [mock.call(
      length=4,
      contents='\x08\x52\x4e\x48',
      bytesum=0xf0,
      checksum=0x0f
    )]

    actual_calls = frame_receiver.send.call_args_list
    self.assertEqual(actual_calls, expected_calls)    

  def test_detectMultipleValidFrames(self): 
    frame_receiver = self.runFixture(self.valid_frames)
    expected_calls = [
      mock.call(
        length=4,
        contents='\x08\x52\x4e\x48',
        bytesum=0xf0,
        checksum=0x0f
      ),
      mock.call(
        bytesum=271, 
        checksum=240, 
        length=5, 
        contents='\x88\x01\x42\x44\x00'
      )
    ]

    actual_calls = frame_receiver.send.call_args_list
    self.assertEqual(actual_calls, expected_calls) 

  def test_detectMultipleValidFramesInStream(self): 
    frame_receiver = self.runFixture(self.valid_frames_in_stream)
    expected_calls = [
      mock.call(
        length=4,
        contents='\x08\x52\x4e\x48',
        bytesum=0xf0,
        checksum=0x0f
      ),
      mock.call(
        bytesum=271, 
        checksum=240, 
        length=5, 
        contents='\x88\x01\x42\x44\x00'
      )
    ]

    actual_calls = frame_receiver.send.call_args_list
    self.assertEqual(actual_calls, expected_calls) 


class TestXBeeAPIFramer(unittest.TestCase):

  def setUp(self):
    self.api_at_command = '\x08\x52\x4e\x48'
    self.api_tx_request = (
      '\x10\x01\x00\x14\xa2\x00\x40' +
      '\x0a\x01\x27\xff\xfe\x00\x00' +
      '\x54\x78\x44\x61\x74\x61\x30\x41'
    )

  def test_correctChecksum(self):
    expected_checksum = '\x0f'    

    framer_generator = framing.XBeeAPIFramer(self.api_at_command)
    framer_list = list(framer_generator)
    actual_checksum = framer_list[-1]

    self.assertEqual(expected_checksum, actual_checksum)

  def test_correctLength(self):
    expected_length = '\x16'    

    framer_generator = framing.XBeeAPIFramer(self.api_tx_request)
    framer_list = list(framer_generator)
    actual_length = framer_list[1:3]

    self.assertEqual(expected_length, actual_length)

  def test_correctStartDelimiter(self):
    expected_start_delimiter = '\x7e'    

    framer_generator = framing.XBeeAPIFramer(self.api_tx_request)
    framer_list = list(framer_generator)
    actual_start_delimiter = framer_list[0]

    self.assertEqual(expected_start_delimiter, actual_start_delimiter)


class TestFrameManager(unittest.TestCase):
  pass
