from Crypto.Cipher import AES

def encrypt(key, data):
    return AES.new(key).encrypt(data)


def decrypt(key, data):
    return AES.new(key).decrypt(data)

