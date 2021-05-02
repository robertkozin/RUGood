import random

def generate_uuid(length=7):
  uuid = ''
  options = '0123456701234567'
  for _ in range(length):
    idx = random.getrandbits(4)
    uuid += options[idx]
  return uuid

def get_uuid():
  try:
    with open('uuid.txt', 'r') as f:
      return f.read().strip()
  except OSError:
    uuid = generate_uuid()
    with open('uuid.txt', 'w') as f:
      f.write(uuid)
    return uuid
