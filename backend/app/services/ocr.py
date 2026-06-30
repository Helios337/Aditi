import re

LATEX_TO_SYMPY = {
    r"\\frac": " ",
    r"\\sqrt": "sqrt",
    r"\\pi": "pi",
    r"\\infty": "oo",
    r"\\cdot": "*",
    r"\\times": "*",
    r"\\left": "",
    r"\\right": "",
    r"\\,": "",
    r"\\;": "",
    r"\\!": "",
    r"\\text": "",
    r"\\mathrm": "",
}


def normalize_for_sympy(expression: str) -> str:
    text = expression.strip()
    text = text.replace("$", "")
    text = text.replace("^", "**")
    for latex, replacement in LATEX_TO_SYMPY.items():
        text = re.sub(latex, replacement, text)
    text = re.sub(r"\{([^}]*)\}", r"(\1)", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
