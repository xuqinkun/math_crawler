import os

import rsa

keys_path = './keys/'
pubkey_name = "public.pem"
privkey_name = "private.pem"


def bytes_to_str(data=b''):
    return str(data, encoding='utf-8')


def str_to_bytes(data=''):
    return bytes(data, encoding="utf-8")


def save_keys(pubkey=b'', privkey=b''):
    if not os.path.exists(keys_path):
        os.mkdir(keys_path)
    with open(keys_path + pubkey_name, "w") as f:
        f.write(bytes_to_str(pubkey))
    with open(keys_path + privkey_name, "w") as f:
        f.write(bytes_to_str(privkey))


def load_pub_key():
    pub_key = None
    pub_filename = keys_path + pubkey_name
    if os.path.exists(pub_filename):
        with open(pub_filename, "r") as f:
            pub_key_str = f.read()
            try:
                pub_key = rsa.PublicKey.load_pkcs1(str_to_bytes(pub_key_str))
            except Exception as e:
                print(e)
                print("Load public key failed")
    return pub_key


def load_priv_key():
    priv_key = None
    priv_filename = keys_path + privkey_name
    if os.path.exists(priv_filename):
        with open(priv_filename, "r") as f:
            priv_key_str = f.read()
            try:
                priv_key = rsa.PrivateKey.load_pkcs1(str_to_bytes(priv_key_str))
            except Exception as e:
                print(e)
                print("Load public key failed")
    return priv_key


def rsa_encrypt(plain_text):
    pub_key = load_pub_key()
    if not pub_key:
        pub_key, priv_key = rsa.newkeys(1024)
        try:
            save_keys(pub_key.save_pkcs1(), priv_key.save_pkcs1())
        except Exception as e:
            print(e)
            print("Save keys failed!")
    # Use pubkey to encrypt
    return rsa.encrypt(plain_text.encode("utf-8"), pub_key)


def rsa_decrypt(secret_text):
    priv_key = load_priv_key()
    if not priv_key:
        print("Empty private key, decrypt failed!")
        return secret_text
    return rsa.decrypt(secret_text, priv_key).decode("utf-8")


if __name__ == "__main__":
    secret_str = rsa_encrypt("hello")
    print("Secret_str: %s" % secret_str)
    content = rsa_decrypt(secret_str)
    print("Plain_text: %s" % content)
