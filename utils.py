import os
from PIL import Image,ImageSequence
import rsa
import requests
from config import LOCAL_IMG_DIR

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

def url_img_download(url):
    if os.path.exists(LOCAL_IMG_DIR) is False:
        os.mkdir(LOCAL_IMG_DIR)
    img_path = LOCAL_IMG_DIR + url.split('/')[-1]
    img=requests.get(url)
    with open(img_path,'wb') as f:
        f.write(img.content)
    return img_path

def image_transform(origin_img_path):
    '''
        input the path to the origin image and check its format and size.
        generate new image that satisfy the need of ocr. 
        return the path to the new image.
    '''
    im = Image.open(origin_img_path)
    name,file_format=os.path.splitext(origin_img_path)

    if file_format=='gif':
        #get the first image in this gif
        im=ImageSequence.all_frames(im)[0]
    h,w=im.size
    h = max(16,h)
    h = min(4096,h)
    w = max(16,w)
    w = min(4096,w)
    im = im.resize((h,w))
    output_path=name + '.png'
    print("Save local image:%s, resize: " %output_path,im.size)
    im=im.convert('RGBA')
    im.save(output_path)
    return output_path


if __name__ == "__main__":
    secret_str = rsa_encrypt("hello")
    print("Secret_str: %s" % secret_str)
    content = rsa_decrypt(secret_str)
    print("Plain_text: %s" % content)
