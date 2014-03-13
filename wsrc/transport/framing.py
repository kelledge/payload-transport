"""

Frame Fields:
  Frame ID       | uint8
  64-bit Address | uint64
  AT Command     | int8[2] 
  Bitfields      | uint8
  String         | int8[*], NULL terminated
  Reserved       | 

"""

import struct

def coroutine(func):
  """
  A coroutine decorator. Kicks off a generator by callings its
  next method.
  """
  def start(*args, **kwargs):
    coroutine = func(*args, **kwargs)
    coroutine.next()
    return coroutine
  return start


def FrameFlattener(frame):
  """
  Process a frame byte-wise
  """
  for chunk in frame:
    for byte in chunk:
      yield byte


@coroutine
def XBeeAPIUnFramer(target=None):
  """
  Performs un-framing on a serial stream of data.
  """
  
  while True:
    byte = (yield)

    if byte == '\x7e':
      length_msb = (yield)
      length_lsb = (yield)
      frame_length, = struct.unpack('>H', length_msb + length_lsb)
      frame_bytesum = 0
      frame_contents = ''

      for _ in xrange(frame_length):
        byte = (yield)
        frame_bytesum, += struct.unpack('>B', byte)
        frame_contents += byte
	
      frame_checksum, = struct.unpack('>B', (yield))
      target.send(
        length=frame_length,
        contents=frame_contents,
        bytesum=frame_bytesum,
        checksum=frame_checksum
      )


def XBeeAPIFramer(bytes):
  """
  Performs framing on a series of bytes. Currently does the following:
  * Start delimiter
  * Length as big-endiann word
  * Checksum calculation
  """
  unsigned_byte_struct = struct.Struct('>B')

  frame_length = len(bytes)
  frame_bytesum = 0

  yield '\x7e'
  yield struct.pack('>H', frame_length)
  yield bytes

  for b in bytes:
    uint8_b, = unsigned_byte_struct.unpack(b)
    frame_bytesum += uint8_b

  frame_checksum = 0xff - (frame_bytesum & 0xff)
  yield unsigned_byte_struct.pack(frame_checksum)


def XBeeAPIFrameEscaper(
    frame,
    escape_marker='\x7d',
    escaped_bytes=('\x7e', '\x7d', '\x11', '\x13'),
    escape_mask='\x20'
  ):
  """
  Escapes the bytes in a frame according to XBee's requirements.

  Accepts frames, and performs escaping on them using the following protocol:
   * The first byte (the frame delimiter) is always unaltered.
   * If any remaining bytes in the frame are bytes in the 'escaped_bytes' tuple,
     they are escaped by preceding them with the 'escape_marker', followed by the
     original byte XOR'ed with the 'escape_mask'

  e.g. (assuming function defaults)
  >> 0x7e 0x11 0x00 0x7d -> 0x7e 0x7d 0x31 0x00 0x7d 0x9d
  """
  unsigned_byte_struct = struct.Struct('>B')
  escape_mask_int, = unsigned_byte_struct.unpack(escape_mask)

  # there is no garentee how the frame will be organized.
  # Flatten in so it can be processed byte-wise
  frame = FrameFlattener(frame)

  # the first byte of a frame is the delimiter, and is not escaped
  # simply yield it back unaltered
  yield next(frame)

  for byte in frame:
    if byte in escaped_bytes:
      yield escape_marker
      byte_int, = unsigned_byte_struct.unpack(byte)
      byte_int ^= escape_mask_int
      byte = unsigned_byte_struct.pack(byte_int)
    yield byte


class FrameManager(object):
  """
  Implements higher level framing functionality, including:
  * Validation of checksums
  * Accepts valid frames, rejects invalid frames.
  * 
  """
  def __init__(self, framer, unframer):
    self.framer = framer
    self.unframer = unframer


