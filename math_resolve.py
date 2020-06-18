import latex2mathml as lm
from mathml2latex import mathml
import latex2mathml.converter as converter
from urllib import parse
import re

from bs4 import BeautifulSoup


def mathml2latex(ml=''):
    return mathml.process_mathml(BeautifulSoup(ml, "lxml"))


def latex2mathml(latex=''):
    if len(latex) == 0:
        return None
    return converter.convert(latex)


url = "http://math.21cnjy.com/MathMLToImage?mml=%3Cmath+xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F1998%2FMath%2FMathML%22%3E%3Cmfrac%3E%3Cmn%3E22%3C%2Fmn%3E%3Cmn%3E7%3C%2Fmn%3E%3C%2Fmfrac%3E%3C%2Fmath%3E&key=4879004862d17115f5e110593a6f860c"
url_decode = parse.unquote(url)
ml = re.findall("<math.*math>", url_decode)[0]
latex = mathml2latex(url_decode)
# print(latex)
# print(latex2mathml(latex))
