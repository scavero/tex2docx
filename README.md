# tex2docx

[![PyPI version](https://badge.fury.io/py/tex2docx-converter.svg)](https://badge.fury.io/py/tex2docx-converter)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
> **Convert LaTeX documents to Word (.docx) while preserving TikZ diagrams, cover pages, table of contents, glossaries, and bibliography.**

Academic and technical documents written in LaTeX often need to be shared as Word files for collaboration. `tex2docx` automates this conversion in a single command, rendering TikZ diagrams as high-resolution PNGs and keeping the rest as editable text.

> 🇪🇸 **¿Hablas español?** Lee la [guía completa en español](GUIA_ES.md).

## ✨ Features

| LaTeX Element | Word Output |
|---|---|
| TikZ diagrams | High-res PNG images (300 DPI default) |
| Cover page (`\maketitle`) | Image — pixel-perfect from PDF |
| Table of contents | Image — pixel-perfect from PDF |
| Glossary (`\printacronyms`) | Image — pixel-perfect from PDF |
| Bibliography (`thebibliography`) | Editable numbered list `[1], [2]…` |
| Sections, lists, text | Editable text |
| Tables | Editable tables |
| Acronyms (`\ac{X}`, `\acp{X}`) | Resolved to plain text |
| Bold, italic, URLs | Preserved |

## 📋 Prerequisites

| Tool | Purpose | Install |
|---|---|---|
| **Python 3.8+** | Run the script | [python.org](https://python.org/) |
| **pdflatex** (MiKTeX or TeX Live) | Compile LaTeX & TikZ | [miktex.org](https://miktex.org/) / [tug.org/texlive](https://tug.org/texlive/) |
| **Pandoc** | LaTeX → Word conversion | [pandoc.org](https://pandoc.org/) |
| **PyMuPDF** | PDF → PNG rendering | `pip install PyMuPDF` |

## 🚀 Quick Start

```bash
# Install from PyPI
pip install tex2docx-converter

# Convert your document
tex2docx your_document.tex
```

This generates **`your_document_word.docx`** automatically.

## 📖 Usage

### Basic conversion

```bash
tex2docx document.tex
```

### Custom output filename

```bash
tex2docx document.tex -o deliverable.docx
```

### Higher resolution diagrams

```bash
tex2docx document.tex --dpi 400
```

### Exact LaTeX Formatting (Template & Numbering)

To make the Word document look exactly like LaTeX (using Computer Modern font, justified paragraphs, etc.), the tool now automatically downloads and uses a LaTeX-like template by default. 

You can also preserve the LaTeX section numbering (`1. Introduction`, `1.1. Background`) using `--number-sections`:

```bash
tex2docx document.tex --number-sections
```

You can also pass your own custom Word template to apply your corporate/university styles:
```bash
tex2docx document.tex --reference-doc my_university_template.docx
```

### Skip cover/TOC/glossary extraction

For documents without a custom cover page or glossary:

```bash
tex2docx document.tex --no-pages
```

### Custom page extraction

Extract only specific pages (0-indexed) with custom labels:

```bash
# Only cover and TOC (no glossary)
tex2docx document.tex --pages 0,1 --labels portada,indice

# Cover spans 2 pages, glossary on page 4
tex2docx document.tex --pages 0,2,3 --labels portada,indice,glosario
```

### All options

```bash
tex2docx --help
```

```
usage: tex2docx.py [-h] [--output OUTPUT] [--dpi DPI] [--pages PAGES]
                   [--labels LABELS] [--no-pages] [--workdir WORKDIR] texfile

positional arguments:
  texfile               Input .tex file

options:
  --output, -o          Output .docx filename (default: <input>_word.docx)
  --dpi                 DPI for TikZ rendering (default: 300)
  --pages               Comma-separated 0-indexed page numbers (default: 0,1,2)
  --labels              Comma-separated labels for pages (default: portada,indice,glosario)
  --no-pages            Skip page extraction (no cover/TOC/glossary images)
  --reference-doc REFERENCE_DOC
                        Custom Word template to apply styles
  --number-sections     Number sections in the output Word document
  --workdir WORKDIR     Directory to save extracted images (default: tikz_png)
```

## ⚙️ How It Works

```
document.tex
    │
    ├─[1] pdflatex ──► document.pdf (full compilation)
    │                     │
    │                [2] Extract pages as PNG (cover, TOC, glossary)
    │
    ├─[3] Extract & compile each TikZ diagram as standalone PNG
    │
    ├─[4] Replace \maketitle, \tableofcontents, \printacronyms
    │     with \includegraphics pointing to extracted PNGs
    │
    ├─[4b] Convert \begin{thebibliography} to editable numbered list
    │
    ├─[5] Resolve \ac{X} → X, \acp{X} → Xs
    │
    ├─[6] Write clean intermediate .tex
    │
    └─[7] pandoc -f latex -t docx ──► document_word.docx ✅
```

## 📁 Generated Files

```
your_project/
├── document.tex                ← Your LaTeX source
├── document.pdf                ← Compiled PDF (step 1)
├── document_word.docx          ← Generated Word file ✅
├── document_intermediate.tex   ← Intermediate file (can be deleted)
└── tikz_png/                   ← Generated images (can be deleted)
    ├── page_portada.png
    ├── page_indice.png
    ├── page_glosario.png
    ├── fig_1.png
    ├── fig_2.png
    └── ...
```

## 📝 LaTeX Document Requirements

For best results, your `.tex` document should follow these conventions:

| Element | Convention |
|---|---|
| Cover | `\maketitle` followed by `\newpage` |
| TOC | `\tableofcontents` followed by `\newpage` |
| Glossary | `\printacronyms[...]` followed by `\newpage` |
| Bibliography | `\begin{thebibliography}{99}...\end{thebibliography}` |
| Acronyms | `\DeclareAcronym{X}{short = X, long = ...}` |
| Diagrams | `\begin{tikzpicture}...\end{tikzpicture}` in the document body |

> **Note:** TikZ pictures defined inside `\newcommand` in the preamble (e.g., logo placeholders) are automatically ignored. Only diagrams in the document body are processed.

## 🤝 Contributing

Contributions are welcome! Feel free to:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Ideas for contributions

- [ ] Support for `beamer` presentations
- [ ] Custom Word template (`.dotx`) support
- [ ] Support for `pgfplots` charts
- [ ] GUI / web interface
- [ ] Cross-references and `\ref{}` resolution
- [ ] `bibtex` / `biblatex` support (in addition to `thebibliography`)

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## 💡 Tips

- If you need the Word file to be 100% visually identical to the PDF, consider sharing the PDF directly. The Word output is ideal when others need to **edit the text**.
- Use `--dpi 400` for presentation-quality diagrams.
- The intermediate `.tex` and `tikz_png/` directory can be safely deleted after conversion.
