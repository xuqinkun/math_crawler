import latex2mathml.converter as converter
import lxml.etree as ET
import re


def mathml2latex(mml_ns=''):
    try:
        mml_ns = re.sub("(?!>)\\+(?!<)", " ", mml_ns)
        mml_ns = re.sub("&nbsp;", " ", mml_ns)
        mml_ns = re.sub("<br>", "", mml_ns)
        mml_dom = ET.fromstring(mml_ns)
        xslt = ET.parse("xsltml_2.1/mmltex.xsl")
        transform = ET.XSLT(xslt)
        out = transform(mml_dom)
        return str(out)
    except Exception as e:
        print(e)
        print(mml_ns + " failed")


def latex2mathml(latex=''):
    if len(latex) == 0:
        return None
    return converter.convert(latex)
