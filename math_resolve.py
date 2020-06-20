import latex2mathml.converter as converter
from bs4 import BeautifulSoup
from mathml2latex import mathml


def mathml2latex(ml=''):
    return mathml.process_mathml(BeautifulSoup(ml, "lxml"))


def latex2mathml(latex=''):
    if len(latex) == 0:
        return None
    return converter.convert(latex)


if __name__ == '__main__':
    print(mathml2latex('<math xmlns="http://www.w3.org/1998/Math/MathML"><mo>-</mo><msqrt><mn>5</mn></msqrt></math>'))