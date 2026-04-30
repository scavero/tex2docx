import pytest
from tex2docx import (
    extract_preamble_and_body,
    parse_acronyms,
    resolve_acronyms,
    format_bibliography,
    build_standalone_preamble
)

def test_extract_preamble_and_body():
    content = "\\documentclass{article}\n\\usepackage{tikz}\n\\begin{document}\nHello World\n\\end{document}"
    preamble, body = extract_preamble_and_body(content)
    assert "\\documentclass{article}" in preamble
    assert "\\usepackage{tikz}" in preamble
    assert "\\begin{document}" in body
    assert "Hello World" in body

def test_extract_preamble_missing_document(capsys):
    content = "\\documentclass{article}\n\\usepackage{tikz}\nHello World"
    with pytest.raises(SystemExit):
        extract_preamble_and_body(content)
    captured = capsys.readouterr()
    assert "ERROR: \\begin{document} not found" in captured.out

def test_parse_acronyms():
    preamble = "\\DeclareAcronym{API}{short = API, long = Application Programming Interface}\n\\DeclareAcronym{GUI}{short=GUI,long=Graphical User Interface}"
    acronyms = parse_acronyms(preamble)
    assert acronyms == {"API": "API", "GUI": "GUI"}

def test_resolve_acronyms():
    acronyms = {"API": "API", "GUI": "GUI"}
    text = "The \\ac{API} is good. The \\acp{API} are better. Use the \\acs{GUI} or \\acl{GUI}."
    resolved = resolve_acronyms(text, acronyms)
    assert resolved == "The API is good. The APIs are better. Use the GUI or GUI."

def test_resolve_acronyms_missing():
    acronyms = {"API": "API"}
    text = "The \\ac{UNKNOWN} and \\acp{UNKNOWN}."
    resolved = resolve_acronyms(text, acronyms)
    assert resolved == "The UNKNOWN and UNKNOWNs."

def test_format_bibliography():
    body = "Text before.\n\\begin{thebibliography}{99}\n\\bibitem{ref1} Author A. Book.\n\\bibitem{ref2} Author B. Article.\n\\end{thebibliography}\nText after."
    new_body, count = format_bibliography(body)
    assert count == 2
    assert "\\section*{Referencias}" in new_body
    assert "\\begin{description}" in new_body
    assert "\\item[{[1]}] Author A. Book." in new_body
    assert "\\item[{[2]}] Author B. Article." in new_body
    assert "\\end{description}" in new_body

def test_format_bibliography_empty():
    body = "Just some text without bib."
    new_body, count = format_bibliography(body)
    assert count == 0
    assert new_body == body

def test_build_standalone_preamble():
    preamble = "\\documentclass{article}\n\\usepackage[spanish]{babel}\n\\usepackage{mathpazo}\n\\usetikzlibrary{shapes,arrows}\n\\definecolor{mycolor}{RGB}{255,0,0}"
    standalone = build_standalone_preamble(preamble)
    assert "\\usepackage[T1]{fontenc}" in standalone
    assert "\\usepackage{tikz}" in standalone
    assert "\\usepackage[spanish]{babel}" in standalone
    assert "\\usepackage{mathpazo}" in standalone
    assert "\\usetikzlibrary{shapes,arrows}" in standalone
    assert "\\definecolor{mycolor}{RGB}{255,0,0}" in standalone
