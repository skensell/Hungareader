import hmac
# Weird things happen when the c in crypto is lowercase or uppercase
from Crypto.Cipher import DES
import base64

from secrets import *


# =============================
# = Simple Message Encryption =
# =============================


def encrypt(msg):
    """A simple encryption. encrypted is a byte string.  We need base64 to make it url safe."""
    encrypted = DES.new(encryption_key, DES.MODE_ECB).encrypt(msg + ' '*(8 - (len(msg)%8)))
    return base64.b64encode(encrypted) # needed because of unicode errors

def decrypt(msg):
    """Simple inverse of encrypt"""
    encrypted = base64.b64decode(msg)
    return DES.new(encryption_key).decrypt(encrypted).rstrip()


# ======================
# = SECURE COOKIES =
# ======================

def make_secure_val(val):
    """Secure values for cookies. Protects against people modifying cookies.
    Takes 34 and returns 34|adjpsfoijapdfoijado"""
    h = hmac.new(secret, val).hexdigest()
    return '%s|%s' % (val, h)

def check_secure_val(secret_val):
    """Returns the original value if secret_val was hashed correctly."""
    val = secret_val.split('|')[0]
    if secret_val == make_secure_val(val):
        return val


if __name__ == '__main__':
    a = encrypt('ahFkZXZ-aG93aWxlYXJuZWRpdHISCxIFU3RvcnkYgICAgIDArwoM')
    print decrypt(a)
