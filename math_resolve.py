import latex2mathml.converter as converter
from bs4 import BeautifulSoup
from mathml2latex import mathml


def mathml2latex(ml=''):
    return mathml.process_mathml(BeautifulSoup(ml, "lxml"))


def latex2mathml(latex=''):
    if len(latex) == 0:
        return None
    return converter.convert(latex)
