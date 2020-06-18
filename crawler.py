import requests
from bs4 import BeautifulSoup
from bs4.element import *
from urllib import parse
import csv_edit


# Convert the img src to MathML
def resolve_mathml(src=''):
    url_decode = parse.unquote(src)
    return re.findall("<math.*math>", url_decode)[0]


# Resolve the name of png
def resolve_png(src=''):
    name = src.split('/')[-1]
    return name.split('.')[-1]


# Resolve the tag as a plain text
# HTML Tag is a tree, use DFS to travers
def resolve_tag(tag=Tag(name='')):
    ret = ''
    url_map = {}
    for child in tag.children:                    # Traverse the children of tag
        if isinstance(child, NavigableString):    # NavigableString is a plain text, just append to ret
            ret += str(child)
        elif child.name == 'br':                  # Tag <br>, append a new line
            ret += '\n'
        elif child.name == 'img':                 # Tag <img>, append the attribute 'src'
            src = str(child['src'])
            if src.find('MathMLToImage') != -1:   # URL contains MathML then just resolve it
                math_ml = resolve_mathml(src)
                ret += math_ml
            elif src.find('png'):                 # Simple url for png
                key = resolve_png(src)
                ret += key                        # Placeholder for OCR to find the image path
                url_map[key] = src
            text, temp_map = resolve_tag(child)   # Call resolve_tag recursively
            ret += text
            url_map.update(temp_map)
        elif isinstance(child, Tag):              # If current child is a tag, call resolve_tag recursively
            text, temp_map = resolve_tag(child)
            ret += text
            url_map.update(temp_map)
    return ret, url_map


headers = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) " +
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36",
    # "X-CSRF-TOKEN:": csrf,
    "Cookie": "_session=eyJpdiI6IkVoTFl1SFdGaTdVS1Njblc4QTR6MGc9PSIsInZhbHVlIjoiVXRUT3FFbHpmcVpvQ2ZPTFc2N2hGV3FtZ0dWXC9nOERWaGJWVEtUbnBrT28zWVhuRlc3eHBWRlhlemVDMU0rdkYiLCJtYWMiOiI2MGMyOTNhZGI4NDM3MWVlZGQ2OWIxM2YxOGM2ODY5NDVjM2M2M2Y5NWI2MmFjNTQ0YzhhNTA2MDllNTgxYWU4In0%3D;" +
              "XSRF-TOKEN=eyJpdiI6Ik5oVUJFXC85c0FJZVwvcTV3bjdCbEtyQT09IiwidmFsdWUiOiJZV3I1XC9oT01OU2xKMThuck81TXRRbU9ZbWFpbk85c0lUbG5ZZlZuM3lrTlNHdVRVRDljTEZJMFRueGFkQUpUWSIsIm1hYyI6ImFmYzE3MDEzZTFjZjBjM2VmYjJmNDgxMDg1NDE0Njc2MGJjNDhhNGI0MDM3YTZjN2EzOTY2ZGNmMmYyZTVmZjAifQ%3D%3D",
    "X-Requested-With": "XMLHttpRequest"
}
time = 0
data = csv_edit.get_url_from_file("data/url.csv")
for url, status in data.items():
    if status == '0':  # 0 indicates that current url is not accessed
        resp = requests.get(url=url, headers=headers)
        soup = BeautifulSoup(resp.text, 'html.parser')
        title = soup.select_one("div .paper-question-title")
        options = soup.select_one("div .paper-question-options")
        analyze = soup.select_one("div .paper-analyize-wrap")
        if analyze.text == '显示答案解析':
            print("Login failure!Please refresh cookies!")
            exit(1)
        text, url_map = resolve_tag(title)
        print(text)
        text, url_map = resolve_tag(options)
        print(url_map)
        text, url_map = resolve_tag(analyze)
        print(text)
