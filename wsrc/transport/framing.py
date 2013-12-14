import struct

def coroutine(func):
  def start(*args,**kwargs):
    cr = func(*args,**kwargs)
    cr.next()
    return cr
  return start

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
      frame_length = struct.unpack('>H', length_msb + length_lsb)[0]
      frame_bytesum = 0
      frame_contents = ''

      for _ in xrange(frame_length):
	byte = (yield)
        frame_bytesum += struct.unpack('>B', byte)[0]
        frame_contents += byte
	
      frame_checksum = struct.unpack('>B', (yield))[0]
      target.send(
        length=frame_length,
        contents=frame_contents,
        bytesum=frame_bytesum,
        checksum=frame_checksum
      )


class FrameManager(object):
  pass
