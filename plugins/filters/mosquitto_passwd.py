#pylint: skip-file

from ansible.errors import AnsibleError

def mosquitto_passwd(passwd):
  try:
    import passlib.hash
  except Exception as e:
    raise AnsibleError('mosquitto_passlib custom filter requires the passlib pip package installed') from e
  
  SALT_SIZE = 12
  ITERATIONS = 101

  digest = passlib.hash.pbkdf2_sha512.using(salt_size=SALT_SIZE, rounds=ITERATIONS) \
                                      .hash(passwd) \
                                      .replace("pbkdf2-sha512", "7") \
                                      .replace(".", "+")
  
  return digest + "=="


class FilterModule(object):
  def filters(self):
    return {
      'mosquitto_passwd': mosquitto_passwd,
    }   
