"""
tex2docx.py — Converts a LaTeX document to Word (.docx) preserving TikZ diagrams,
cover page, table of contents, glossary, acronyms, and bibliography.

Usage:
    python tex2docx.py mi_documento.tex
    python tex2docx.py mi_documento.tex --pages 0,1,2 --labels portada,indice,glosario
    python tex2docx.py mi_documento.tex --dpi 300 --output resultado.docx

Requirements:
    - pdflatex (MiKTeX or TeX Live)
    - pandoc
    - Python 3.8+
    - PyMuPDF: pip install PyMuPDF
"""

import argparse
import os
import re
import subprocess
import sys
from typing import Dict, Tuple, Optional, List

try:
    import fitz  # PyMuPDF
except ImportError:
    print("ERROR: PyMuPDF not installed. Run:  pip install PyMuPDF")
    sys.exit(1)


def find_pandoc() -> Optional[str]:
    """Find pandoc executable across different platforms."""
    # Check PATH first
    for cmd in ["pandoc", "pandoc.exe"]:
        try:
            subprocess.run([cmd, "--version"], capture_output=True, check=True)
            return cmd
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass
            
    # Check common Windows location
    if sys.platform == "win32":
        local_pandoc = os.path.join(
            os.environ.get("LOCALAPPDATA", ""), "Pandoc", "pandoc.exe"
        )
        if os.path.exists(local_pandoc):
            return local_pandoc
            
    # Check common macOS/Linux locations
    else:
        for path in ["/usr/local/bin/pandoc", "/opt/homebrew/bin/pandoc", "/usr/bin/pandoc"]:
            if os.path.exists(path):
                return path
                
    return None


def extract_preamble_and_body(content: str) -> Tuple[str, str]:
    """Split a LaTeX document into preamble and body."""
    marker = r"\begin{document}"
    try:
        idx = content.index(marker)
        return content[:idx], content[idx:]
    except ValueError:
        print("ERROR: \\begin{document} not found in the TeX file.")
        sys.exit(1)


def build_standalone_preamble(preamble_raw: str) -> str:
    """Build a minimal preamble for standalone TikZ compilation."""
    lines = [
        r"\usepackage[T1]{fontenc}",
        r"\usepackage[utf8]{inputenc}",
        r"\usepackage{xcolor}",
        r"\usepackage{tikz}",
        r"\usepackage{amssymb}",
        r"\usepackage{graphicx}",
    ]

    # Detect babel
    m = re.search(r"(\\usepackage\[.*?\]\{babel\})", preamble_raw)
    if m:
        lines.append(m.group(1))

    # Detect font packages
    for pkg in ["mathpazo", "helvet", "lmodern", "libertine", "newtxtext"]:
        m = re.search(rf"(\\usepackage(?:\[.*?\])?\{{{pkg}\}})", preamble_raw)
        if m:
            lines.append(m.group(1))

    # TikZ libraries
    for m in re.finditer(r"(\\usetikzlibrary\{[^}]+\})", preamble_raw):
        lines.append(m.group(1))

    # Color definitions
    for m in re.finditer(r"(\\definecolor\{[^}]+\}\{[^}]+\}\{[^}]+\})", preamble_raw):
        lines.append(m.group(1))
    for m in re.finditer(r"(\\colorlet\{[^}]+\}\{[^}]+\})", preamble_raw):
        lines.append(m.group(1))

    # PGF layers
    for m in re.finditer(r"(\\pgfdeclarelayer\{[^}]+\})", preamble_raw):
        lines.append(m.group(1))
    for m in re.finditer(r"(\\pgfsetlayers\{[^}]+\})", preamble_raw):
        lines.append(m.group(1))

    # tikzset
    for m in re.finditer(r"(\\tikzset\{.*?\})", preamble_raw, flags=re.DOTALL):
        lines.append(m.group(1))

    return "\n".join(lines)


def parse_acronyms(preamble_raw: str) -> Dict[str, str]:
    """Extract acronym short forms from \\DeclareAcronym commands."""
    acronyms = {}
    for m in re.finditer(
        r"\\DeclareAcronym\{([^}]+)\}\{short\s*=\s*([^,}]+)", preamble_raw
    ):
        acronyms[m.group(1).strip()] = m.group(2).strip()
    return acronyms


def resolve_acronyms(text: str, acronyms: Dict[str, str]) -> str:
    """Replace \\ac{X}, \\acp{X}, \\acs{X}, \\acl{X} with plain text."""
    text = re.sub(
        r"\\acp\{([^}]+)\}",
        lambda m: acronyms.get(m.group(1), m.group(1)) + "s",
        text,
    )
    for cmd in ["ac", "acs", "acf"]:
        text = re.sub(
            rf"\\{cmd}\{{([^}}]+)\}}",
            lambda m: acronyms.get(m.group(1), m.group(1)),
            text,
        )
    return text


def compile_tikz(tikz_code: str, standalone_preamble: str, output_dir: str, index: int, dpi: int = 300) -> Optional[Tuple[str, int, int]]:
    """Compile a TikZ snippet to a standalone PNG. Returns the path or None."""
    tex = (
        r"\documentclass[tikz, margin=2mm]{standalone}" + "\n"
        + standalone_preamble + "\n"
        + r"\begin{document}" + "\n"
        + tikz_code + "\n"
        + r"\end{document}" + "\n"
    )

    tex_path = os.path.join(output_dir, f"fig_{index}.tex")
    pdf_path = os.path.join(output_dir, f"fig_{index}.pdf")
    png_path = os.path.join(output_dir, f"fig_{index}.png")

    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(tex)

    subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", f"fig_{index}.tex"],
        cwd=output_dir, capture_output=True, text=True,
    )

    if not os.path.exists(pdf_path):
        return None

    doc = fitz.open(pdf_path)
    pix = doc.load_page(0).get_pixmap(dpi=dpi)
    pix.save(png_path)
    w, h = pix.width, pix.height
    doc.close()
    return png_path, w, h


def extract_pdf_pages(pdf_path: str, pages_dict: Dict[int, str], output_dir: str, dpi: int = 250) -> Dict[str, str]:
    """Extract specific pages from a PDF as PNGs.

    pages_dict: {page_number (0-indexed): label}
    Returns: {label: png_path}
    """
    doc = fitz.open(pdf_path)
    result = {}
    for page_num, label in pages_dict.items():
        if page_num >= len(doc):
            print(f"  WARN: Page {page_num} does not exist, skipping '{label}'")
            continue
        pix = doc.load_page(page_num).get_pixmap(dpi=dpi)
        img_path = os.path.join(output_dir, f"page_{label}.png")
        pix.save(img_path)
        result[label] = img_path
        print(f"  Page {page_num + 1} -> {img_path}  ({pix.width}x{pix.height} px)")
    doc.close()
    return result


def format_bibliography(body: str) -> Tuple[str, int]:
    """Convert \\begin{thebibliography}...\\end{thebibliography} to a
    well-formatted \\section + \\enumerate that pandoc renders cleanly as
    editable text in Word.

    Returns (new_body, number_of_entries_found).
    """
    # Find the thebibliography block (with optional \newpage before)
    pat = r"(\\newpage\s*)?\\begin\{thebibliography\}\{[^}]*\}(.*?)\\end\{thebibliography\}"
    m = re.search(pat, body, flags=re.DOTALL)
    if not m:
        return body, 0

    bib_content = m.group(2)

    # Parse individual \bibitem entries
    # Split on \bibitem{...} — each chunk after the first is one entry
    items = re.split(r"\\bibitem\{[^}]*\}", bib_content)
    items = [item.strip() for item in items if item.strip()]

    if not items:
        return body, 0

    # Build clean items for pandoc
    # Using \begin{description} with [N] labels renders best in Word via pandoc
    desc_items = []
    for i, item in enumerate(items, start=1):
        # Clean up: collapse multiple whitespace/newlines into single space
        clean = re.sub(r"\s+", " ", item).strip()
        desc_items.append(f"\\item[{{[{i}]}}] {clean}")

    replacement = (
        "\\newpage\n"
        "\\section*{Referencias}\n"
        "\\begin{description}\n"
        + "\n\n".join(desc_items) + "\n"
        "\\end{description}\n"
    )

    body = body[:m.start()] + replacement + body[m.end():]
    return body, len(items)


def replace_page_blocks(body: str, page_images: Dict[str, str]) -> str:
    """Replace \\maketitle, \\tableofcontents, \\printacronyms with page images."""

    def img_block(path):
        p = path.replace(os.sep, "/")
        return (
            f"\\begin{{figure}}[h!]\n\\centering\n"
            f"\\includegraphics[width=\\textwidth]{{{p}}}\n"
            f"\\end{{figure}}\n\\newpage\n"
        )

    # Cover: \maketitle ... \end{tcolorbox} \newpage
    if "portada" in page_images:
        pat = r"(\\maketitle.*?\\end\{tcolorbox\}\s*\\newpage)"
        text = img_block(page_images["portada"])
        body, n = re.subn(pat, lambda _: text, body, flags=re.DOTALL)
        if not n:
            # Fallback: just \maketitle \newpage
            pat2 = r"\\maketitle\s*\\newpage"
            body, n = re.subn(pat2, lambda _: text, body)
        print(f"  Portada: {'OK' if n else 'not found'}")

    # TOC
    if "indice" in page_images:
        pat = r"\\tableofcontents\s*\\newpage"
        text = img_block(page_images["indice"])
        body, n = re.subn(pat, lambda _: text, body)
        print(f"  Índice: {'OK' if n else 'not found'}")

    # Glossary / Acronyms
    if "glosario" in page_images:
        pat = r"\\printacronyms\[.*?\]\s*\\newpage"
        text = img_block(page_images["glosario"])
        body, n = re.subn(pat, lambda _: text, body)
        print(f"  Glosario: {'OK' if n else 'not found'}")

    return body


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert LaTeX to Word preserving TikZ, cover, TOC, and glossary."
    )
    parser.add_argument("texfile", help="Input .tex file")
    parser.add_argument(
        "--output", "-o", default=None,
        help="Output .docx filename (default: same name as input)"
    )
    parser.add_argument(
        "--dpi", type=int, default=300,
        help="DPI for TikZ diagram rendering (default: 300)"
    )
    parser.add_argument(
        "--pages", default="0,1,2",
        help="Comma-separated 0-indexed page numbers to extract (default: 0,1,2)"
    )
    parser.add_argument(
        "--labels", default="portada,indice,glosario",
        help="Comma-separated labels for extracted pages (default: portada,indice,glosario)"
    )
    parser.add_argument(
        "--no-pages", action="store_true",
        help="Skip page extraction (no cover/TOC/glossary images)"
    )
    parser.add_argument(
        "--workdir", default="tikz_png",
        help="Working directory for generated images (default: tikz_png)"
    )
    args = parser.parse_args()

    tex_file = args.texfile
    if not os.path.exists(tex_file):
        print(f"ERROR: File not found: {tex_file}")
        sys.exit(1)

    base = os.path.splitext(tex_file)[0]
    output_docx = args.output or f"{base}_word.docx"
    output_dir = args.workdir

    pandoc = find_pandoc()
    if not pandoc:
        print("ERROR: pandoc not found. Install from https://pandoc.org")
        sys.exit(1)

    # ---------------------------------------------------------------
    with open(tex_file, "r", encoding="utf-8") as f:
        content = f.read()

    preamble_raw, body = extract_preamble_and_body(content)
    standalone_pre = build_standalone_preamble(preamble_raw)
    os.makedirs(output_dir, exist_ok=True)

    # Step 1 — Compile full PDF
    print("\n[1/7] Compiling full PDF...")
    subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", tex_file],
        capture_output=True, text=True,
    )
    pdf_path = f"{base}.pdf"
    if not os.path.exists(pdf_path):
        print("ERROR: pdflatex failed. Check your .tex file.")
        sys.exit(1)
    print(f"  OK: {pdf_path}")

    # Step 2 — Extract pages
    page_images = {}
    if not args.no_pages:
        print("\n[2/7] Extracting pages from PDF...")
        pages = [int(p) for p in args.pages.split(",")]
        labels = args.labels.split(",")
        if len(pages) != len(labels):
            print("ERROR: --pages and --labels must have the same number of items")
            sys.exit(1)
        pages_dict = dict(zip(pages, labels))
        page_images = extract_pdf_pages(pdf_path, pages_dict, output_dir)
    else:
        print("\n[2/7] Skipping page extraction (--no-pages)")

    # Step 3 — Compile TikZ diagrams
    print("\n[3/7] Compiling TikZ diagrams...")
    tikz_pattern = r"(\\begin\{tikzpicture\}.*?\\end\{tikzpicture\})"
    tikz_matches = list(re.finditer(tikz_pattern, body, flags=re.DOTALL))
    print(f"  Found {len(tikz_matches)} diagram(s) in body.")

    tikz_replacements = []
    for i, m in enumerate(tikz_matches, start=1):
        tikz_code = m.group(1)
        result = compile_tikz(tikz_code, standalone_pre, output_dir, i, args.dpi)
        if result is None:
            print(f"  [{i}] ERROR — check {output_dir}/fig_{i}.log")
            continue
        png_path, w, h = result
        print(f"  [{i}] OK: {png_path}  ({w}x{h} px)")

        start, end = m.start(), m.end()
        prefix = body[:start].rstrip()
        resizebox_m = re.search(r"\\resizebox\{[^}]*\}\{[^}]*\}\{\s*$", prefix)
        if resizebox_m:
            suffix = body[end:]
            closing = re.match(r"\s*\}", suffix)
            if closing:
                start = resizebox_m.start()
                end = end + closing.end()

        repl = f"\\includegraphics[width=\\textwidth]{{{png_path.replace(os.sep, '/')}}}"
        tikz_replacements.append((start, end, repl))

    # Apply replacements
    new_body = body
    for s, e, r in reversed(tikz_replacements):
        new_body = new_body[:s] + r + new_body[e:]

    # Step 4 — Replace cover/TOC/glossary
    print("\n[4/7] Replacing cover, TOC, glossary...")
    if page_images:
        new_body = replace_page_blocks(new_body, page_images)
    else:
        print("  Skipped (no pages extracted)")

    # Step 4b — Format bibliography as editable text
    print("\n[4b/7] Formatting bibliography...")
    new_body, bib_count = format_bibliography(new_body)
    if bib_count:
        print(f"  Converted {bib_count} bibliography entries to numbered list.")
    else:
        print("  No bibliography found (or already clean).")

    # Step 5 — Resolve acronyms
    print("\n[5/7] Resolving acronyms...")
    acronyms = parse_acronyms(preamble_raw)
    if acronyms:
        new_body = resolve_acronyms(new_body, acronyms)
        print(f"  Resolved {len(acronyms)} acronym(s).")
    else:
        print("  No acronyms found.")

    # Clean preamble
    clean_preamble = preamble_raw
    clean_preamble = re.sub(r"\\DeclareAcronym\{[^}]+\}\{[^}]+\}\s*\n?", "", clean_preamble)
    clean_preamble = re.sub(r"\\usepackage\{acro\}[^\n]*\n?", "", clean_preamble)

    # Write intermediate tex
    intermediate_tex = f"{base}_intermediate.tex"
    with open(intermediate_tex, "w", encoding="utf-8") as f:
        f.write(clean_preamble + new_body)

    # Step 6 — Write intermediate tex
    print(f"\n[6/7] Writing intermediate TeX...")
    print(f"  {intermediate_tex}")

    # Step 7 — Pandoc conversion
    print(f"\n[7/7] Converting to {output_docx}...")
    res = subprocess.run(
        [pandoc, "-f", "latex", "-t", "docx",
         "--resource-path=.", intermediate_tex, "-o", output_docx],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        print(f"  Pandoc error:\n{res.stderr}")
        sys.exit(1)

    size_kb = os.path.getsize(output_docx) / 1024
    print(f"\n{'=' * 50}")
    print(f"  DONE: {output_docx}  ({size_kb:.0f} KB)")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
