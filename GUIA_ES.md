# Guía: Convertir LaTeX a Word preservando TikZ

## Requisitos previos

| Herramienta | Para qué | Instalación |
|---|---|---|
| `pdflatex` (MiKTeX) | Compilar LaTeX y los diagramas TikZ | [miktex.org](https://miktex.org/) |
| `pandoc` | Convertir LaTeX → Word | [pandoc.org](https://pandoc.org/) |
| `Python` | Entorno para ejecutar la herramienta | `pip install tex2docx-converter` |

---

## Flujo básico

### 1. Escribe tu documento `.tex` normalmente

Trabaja como siempre en LaTeX con tus diagramas TikZ, portada, índice, glosario, bibliografía, etc.

### 2. Ejecuta el script

```bash
tex2docx mi_documento.tex
```

Esto genera automáticamente **`mi_documento_word.docx`**.

### 3. Listo

El Word incluirá:
- ✅ **Portada** (como imagen de la versión PDF)
- ✅ **Índice** (como imagen)
- ✅ **Glosario de acrónimos** (como imagen)
- ✅ **Bibliografía** (como texto editable con formato `[1]`, `[2]`...)
- ✅ **Diagramas TikZ** (renderizados como PNG a 300 DPI)
- ✅ **Tablas, listas, secciones** (convertidos como texto editable)
- ✅ **Acrónimos** (`\ac{TIC}` → TIC, `\acp{KPI}` → KPIs)

---

## Opciones avanzadas

### Cambiar nombre del archivo de salida

```bash
tex2docx mi_documento.tex -o entregable_final.docx
```

### Cambiar resolución de los diagramas

```bash
# Mayor calidad (más pesado)
tex2docx mi_documento.tex --dpi 400

# Menor calidad (más ligero)
tex2docx mi_documento.tex --dpi 200
```

### Documento sin portada/índice/glosario

Si tu documento no tiene portada personalizada ni glosario:

```bash
tex2docx mi_documento.tex --no-pages
```

### Documento con páginas diferentes

Si tu portada está en la página 1, el índice en la 2, pero **no tienes glosario**:

```bash
tex2docx mi_documento.tex --pages 0,1 --labels portada,indice
```

> [!NOTE]
> Los números de página son **0-indexed** (página 1 = 0, página 2 = 1, etc.)

### Si tu glosario está en otra página

Por ejemplo, si la portada ocupa 2 páginas y el glosario está en la página 4:

```bash
tex2docx mi_documento.tex --pages 0,2,3 --labels portada,indice,glosario
```

### Cambiar directorio de trabajo

```bash
tex2docx mi_documento.tex --workdir images_output
```

---

## Qué hace el script por debajo (7 pasos)

```
mi_documento.tex
      │
      ├──[1] pdflatex ──► mi_documento.pdf (compilación completa)
      │                        │
      │                   [2] Extrae páginas 1,2,3 como PNG
      │                        │
      │                   ┌────┴─────────────────┐
      │                   │ page_portada.png      │
      │                   │ page_indice.png       │
      │                   │ page_glosario.png     │
      │                   └───────────────────────┘
      │
      ├──[3] Extrae cada \begin{tikzpicture}...\end{tikzpicture}
      │      del body y los compila como standalone PNG
      │      ┌───────────────────┐
      │      │ fig_1.png         │
      │      │ fig_2.png         │
      │      │ fig_3.png         │
      │      └───────────────────┘
      │
      ├──[4] Reemplaza \maketitle, \tableofcontents, \printacronyms
      │      con \includegraphics de las páginas extraídas
      │
      ├──[4b] Convierte \begin{thebibliography} a lista
      │       numerada editable con \begin{description}
      │
      ├──[5] Resuelve \ac{TIC} → TIC, \acp{KPI} → KPIs
      │
      ├──[6] Escribe el .tex intermedio limpio
      │
      └──[7] pandoc -f latex -t docx ──► mi_documento_word.docx
```

---

## Qué se convierte y cómo

| Elemento LaTeX | En el Word aparece como... |
|---|---|
| Portada (`\maketitle` + tcolorbox) | **Imagen** (idéntico al PDF) |
| Índice (`\tableofcontents`) | **Imagen** (idéntico al PDF) |
| Glosario (`\printacronyms`) | **Imagen** (idéntico al PDF) |
| Diagramas TikZ | **Imagen PNG** a 300 DPI |
| Bibliografía (`thebibliography`) | **Texto editable** con numeración [1], [2]... |
| Texto, secciones, listas | **Texto editable** |
| Tablas | **Tablas editables** (formato básico) |
| Acrónimos (`\ac{X}`) | **Texto plano** resuelto |
| `tcolorbox` del body | Se pierde la caja, queda el texto |
| Colores de títulos/headers | No se preservan (estilo Word por defecto) |
| `\url{...}` | **Enlace clicable** |
| `\textit{...}` | *Cursiva* |
| `\textbf{...}` | **Negrita** |

> [!TIP]
> Si necesitas que el Word sea 100% fiel al PDF visualmente, considera usar el PDF directamente. El Word es útil cuando necesitas que otros puedan **editar el texto**.

---

## Requisitos del documento `.tex`

Para que el script funcione correctamente, tu documento `.tex` debe seguir estas convenciones:

| Elemento | Requisito |
|---|---|
| Portada | Usar `\maketitle` seguido de `\newpage` |
| Índice | Usar `\tableofcontents` seguido de `\newpage` |
| Glosario | Usar `\printacronyms[...]` seguido de `\newpage` |
| Bibliografía | Usar `\begin{thebibliography}{99}...\end{thebibliography}` |
| Acrónimos | Definir con `\DeclareAcronym{X}{short = X, long = ...}` |
| Diagramas | Usar `\begin{tikzpicture}...\end{tikzpicture}` en el body |

> [!IMPORTANT]
> Los TikZ que estén dentro de `\newcommand` del preámbulo (como placeholders de logos) son ignorados automáticamente. Solo se procesan los del body del documento.

---

## Estructura de archivos generados

```
📁 tu_proyecto/
├── mi_documento.tex               ← tu fuente LaTeX
├── mi_documento.pdf               ← PDF compilado (paso 1)
├── mi_documento_word.docx         ← Word generado ✅
├── mi_documento_intermediate.tex  ← tex intermedio (se puede borrar)
├── tex2docx.py                    ← el script
└── 📁 tikz_png/                   ← imágenes generadas (se puede borrar)
    ├── page_portada.png
    ├── page_indice.png
    ├── page_glosario.png
    ├── fig_1.png
    ├── fig_2.png
    └── fig_3.png
```

---

## Referencia rápida de comandos

```bash
# Conversión básica
tex2docx documento.tex

# Con nombre de salida personalizado
tex2docx documento.tex -o resultado.docx

# Alta resolución para diagramas
tex2docx documento.tex --dpi 400

# Sin portada/índice/glosario (solo texto + tikz + bibliografía)
tex2docx documento.tex --no-pages

# Páginas personalizadas (ej: solo portada e índice)
tex2docx documento.tex --pages 0,1 --labels portada,indice

# Ver todas las opciones
tex2docx --help
```
