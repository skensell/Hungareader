import re, hmac, hashlib, random, string
from Crypto.Cipher import DES
import base64
import logging

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


# ===========================
# = SECURE PASSWORDS =
# ===========================

def make_salt():
   return ''.join(random.choice(string.letters) for x in xrange(5))

def make_pw_hash(name, pw, salt=None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s'%(salt,h)

def pw_matches(name, pw, h): #replaces valid_pw from CS253
    """True if name and pw hash to get h(the pw_hash on file)."""
    salt = h.split(',')[0]
    return h == make_pw_hash(name, pw, salt=salt)


# ===================================
# = VALID USERNAMES, PWDS, & EMAILS =
# ===================================

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return not email or EMAIL_RE.match(email)

def validate(new_user, new_pwd, verify, level, email):
    """SignUp form validation."""
    
    have_error=False
    t_params = dict(new_user=new_user, email=email) #template parameters
    if not valid_username(new_user):
        t_params['error_new_user'] = "That's not a valid username."
        have_error = True
    
    if not valid_password(new_pwd):
        t_params['error_new_pwd'] = "That's not a valid password."
        have_error = True
    elif new_pwd != verify:
        t_params['error_verify'] = "Your passwords don't match."
        have_error = True
    
    if not valid_email(email):
        t_params['error_email'] = "That's not a valid email."
        have_error = True
    
    if level.lower() not in ['beginner', 'intermediate', 'advanced']:
        t_params['error_level'] = 'Please indicate your current level of Hungarian'
        have_error = True
    
    return have_error, t_params


if __name__ == '__main__':
    a = encrypt('ahFkZXZ-aG93aWxlYXJuZWRpdHISCxIFU3RvcnkYgICAgIDArwoM')
    print decrypt(a)
