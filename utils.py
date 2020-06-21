import os
from PIL import Image,ImageSequence
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
    filename = keys_path + pubkey_name
    if os.path.exists(filename):
        with open(filename, "r") as f:
            pub_key_str = f.read()
            try:
                pub_key = rsa.PublicKey.load_pkcs1(str_to_bytes(pub_key_str))
            except Exception as e:
                print(e)
                print("Load public key failed")
    return pub_key


def load_priv_key():
    priv_key = None
    filename = keys_path + privkey_name
    if os.path.exists(filename):
        with open(filename, "r") as f:
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


def contains_str(src='', target=''):
    return src.find(target) != -1

def get_PNG_img():
    pass

def image_transform(origin_img_path):
    '''
        input the path to the origin image and check its format and size.
        generate new image that satisfy the need of ocr. 
        return the path to the new image.
    '''
    im=Image.open(origin_img_path)
    name,file_format=os.path.splitext(origin_img_path)

    if file_format=='gif':
        #get the first image in this gif
        im=ImageSequence.all_frames(im)[0]

    h,w=im.size
    if min(h,w)<15:
        if min(h,w)==h:
            w=int(w*15/h)
            h=15
        else:
            h=int(h*15/w)
            w=15
        im.resize(h,w)

    output_path=name+'.png'
    im=im.convert('RGBA')
    im.save(output_path)
    return output_path


if __name__ == "__main__":
    secret_str = rsa_encrypt("hello")
    print("Secret_str: %s" % secret_str)
    content = rsa_decrypt(secret_str)
    print("Plain_text: %s" % content)
