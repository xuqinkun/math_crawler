import pytesseract
from PIL import Image

img = Image.open("images/3.png")
data = pytesseract.image_to_string(img, lang="eng", config='--psm 4')

