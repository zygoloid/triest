def le2(n):
  return chr(n % 256) + chr(n // 256)
def le4(n):
  return le2(n % 65536) + le2(n // 65536)

def wav(filename, f, dur, freq = 48000):
  global data
  samples = int(dur * 48000)
  bytes_per_sample = 2
  channels = 2
  bytes = samples * bytes_per_sample * channels
  data = [0] * bytes
  header = 'RIFF' + le4(44 + bytes) + 'WAVEfmt ' + le4(16) + le2(1) + le2(channels) + le4(freq) + le4(freq * bytes_per_sample * channels) + le2(bytes_per_sample * channels) + le2(bytes_per_sample * 8) + "data" + le4(bytes)
  assert(len(header) == 44)
  for t in range(len(data) / 4):
    (l,r) = f(t / 48000.)
    l = int(l * 32767)
    r = int(r * 32767)
    (data[4*t], data[4*t+1]) = (l % 256, (l // 256) % 256)
    (data[4*t+2], data[4*t+3]) = (r % 256, (r // 256) % 256)
  file(filename, 'wb').write(header + ''.join(chr(c) for c in data))

def warning(t):
  freq = 440 + 220 * t + 2 * sin(t * 100)
  v = sin(t * freq * 2*pi)
  if t > 0.35:
    v *= (0.5 - t) / 0.15
  return (.2 + .1 * sin(t * 440 * 2 * pi)) * v, \
         (.2 + .1 * cos(t * 440 * 2 * pi)) * v

from math import sin, cos, pi
wav('warning.wav', warning, dur=0.5)
