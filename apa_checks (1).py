"""Revisiones automáticas basadas en reglas para normas APA 7.ª edición (español).

Son heurísticas: detectan errores frecuentes, pero no reemplazan la revisión
con el manual oficial (https://apastyle.apa.org) ni los requisitos de la institución.
"""
import re
import unicodedata

UP = "A-ZÁÉÍÓÚÑÜ"
LOW = "a-záéíóúñü"
YEAR = r"(?:\d{4}[a-z]?|s\. ?f\.)"

REF_HEADERS = re.compile(
    r"^\s*(referencias|referencias bibliogr[aá]ficas|bibliograf[ií]a|lista de referencias)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def _norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]", "", s).strip()


def split_text(text):
    """Separa cuerpo y lista de referencias. Devuelve (cuerpo, referencias|None)."""
    matches = list(REF_HEADERS.finditer(text))
    if not matches:
        return text, None
    m = matches[-1]
    return text[: m.start()], text[m.end():]


def split_references(ref_text):
    """Agrupa las líneas en referencias individuales."""
    start = re.compile(rf"^[{UP}][^()]{{0,250}}?\(\s*{YEAR}(?:, [^)]*)?\)")
    refs = []
    for line in ref_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if start.match(line) or not refs:
            refs.append(line)
        else:
            refs[-1] += " " + line
    return refs


def _issue(level, where, problem, fix, rule):
    return {"nivel": level, "donde": where, "problema": problem, "correccion": fix, "regla": rule}


def _snippet(text, pos, width=60):
    a = max(0, pos - 20)
    return "…" + text[a: pos + width].replace("\n", " ") + "…"


def check_body(body):
    issues = []

    # Citas parentéticas
    for m in re.finditer(r"\(([^()]*)\)", body):
        inner = m.group(1)
        if not re.search(YEAR, inner):
            continue
        for part in inner.split(";"):
            part = part.strip()
            ym = re.search(rf",?\s*({YEAR})(?!\w)", part)
            if not ym:
                continue
            authors = part[: ym.start()].strip()
            if "&" in authors:
                issues.append(_issue(
                    "Error", f"({inner})",
                    "Se usa «&» en la cita.",
                    f"({authors.replace('&', 'y')}, {ym.group(1)})",
                    "En español, las citas parentéticas unen los autores con «y», no con «&»."))
            if re.search(r"\b[A-ZÁÉÍÓÚÑ]\.", authors):
                issues.append(_issue(
                    "Error", f"({inner})",
                    "La cita incluye iniciales de nombre.",
                    "Usa solo los apellidos (salvo que dos autores compartan apellido).",
                    "En el texto se cita el apellido, sin iniciales."))
            if "," in authors and re.search(r"\sy\s", authors) and "et al" not in authors:
                issues.append(_issue(
                    "Error", f"({inner})",
                    "Parece una cita de 3 o más autores con todos los apellidos.",
                    f"({authors.split(',')[0].strip()} et al., {ym.group(1)})",
                    "APA 7: con 3 o más autores se cita el primero + «et al.» desde la primera vez."))
            if re.search(r"[^\s,]\s?\d{4}", part) and not re.search(rf",\s*{YEAR}", part) \
                    and not part.strip().startswith(tuple("0123456789")):
                issues.append(_issue(
                    "Error", f"({inner})", "Falta la coma entre el autor y el año.",
                    "(Apellido, año)", "Formato parentético: (Autor, año)."))

    # Citas narrativas de 3+ autores
    for m in re.finditer(
            rf"[{UP}][{LOW}]+, [{UP}][{LOW}]+(?:, [{UP}][{LOW}]+)* y [{UP}][{LOW}]+ \(\d{{4}}", body):
        first = m.group(0).split(",")[0]
        issues.append(_issue(
            "Error", _snippet(body, m.start()),
            "Cita narrativa con 3 o más autores listados.",
            f"{first} et al. (año)",
            "Con 3 o más autores se usa el primero + «et al.»."))

    # et al.
    for m in re.finditer(r"\bet\.? ?al\.?", body):
        if m.group(0) != "et al.":
            issues.append(_issue(
                "Error", _snippet(body, m.start()),
                f"Forma incorrecta: «{m.group(0)}».",
                "et al.",
                "Se escribe «et al.» (sin punto tras «et», con punto final)."))

    # s. f.
    for m in re.finditer(r"\b(?:s\.f\.|S\.F\.|s/f|n\.d\.|sin fecha)", body):
        issues.append(_issue(
            "Error", _snippet(body, m.start()),
            f"Forma incorrecta de «sin fecha»: «{m.group(0)}».",
            "s. f.",
            "Cuando no hay fecha se escribe «s. f.» (con espacio)."))

    # Página
    for m in re.finditer(r"\b(?:[Pp][aá]g\.?|[Pp][aá]gina|pag\.)\s?\d+", body):
        issues.append(_issue(
            "Error", _snippet(body, m.start()),
            f"Abreviatura de página incorrecta: «{m.group(0)}».",
            "p. 15 (o pp. 15-20)",
            "APA usa «p.» para una página y «pp.» para varias."))
    for m in re.finditer(r"\bp\.\s?\d+\s?[-–]\s?\d+", body):
        issues.append(_issue(
            "Error", _snippet(body, m.start()),
            "Se usa «p.» con un rango de páginas.",
            "pp. 15-20", "Para varias páginas se usa «pp.»."))

    # Ibid, op. cit.
    for m in re.finditer(r"\b(?:ibid|ib[ií]dem|op\. ?cit|loc\. ?cit)\b\.?", body, re.IGNORECASE):
        issues.append(_issue(
            "Error", _snippet(body, m.start()),
            f"Se usa «{m.group(0)}».",
            "Repite la cita (Autor, año).",
            "APA no usa «ibid.» ni «op. cit.»; se repite la cita autor-año."))

    # Citas directas
    qpat = re.compile(r"«([^»]+)»|“([^”]+)”|\"([^\"]+)\"")
    for m in qpat.finditer(body):
        q = next(g for g in m.groups() if g)
        words = len(q.split())
        if words < 4:
            continue
        after = body[m.end(): m.end() + 90]
        before = body[max(0, m.start() - 90): m.start()]
        has_page = re.search(r"\b(pp?\.|párr\.)\s?\d", after) or re.search(r"\b(pp?\.|párr\.)\s?\d", before[-60:])
        if words >= 40:
            issues.append(_issue(
                "Error", _snippet(body, m.start(), 80),
                f"Cita textual de {words} palabras entre comillas.",
                "Preséntala como bloque aparte, sin comillas, con sangría de 1,27 cm; la cita va después del punto final.",
                "Las citas de 40 palabras o más van en bloque."))
        if not has_page:
            issues.append(_issue(
                "Revisar", _snippet(body, m.start(), 80),
                "Cita entre comillas sin número de página visible.",
                "Añade (Autor, año, p. X). Si no hay páginas, usa párr. X o el apartado.",
                "Las citas textuales deben indicar la página (o párrafo)."))

    return issues


def _parse_in_text_citations(body):
    found = set()
    for m in re.finditer(r"\(([^()]*)\)", body):
        inner = m.group(1)
        if not re.search(YEAR, inner):
            continue
        for part in inner.split(";"):
            part = part.strip()
            part = re.sub(r",?\s*(?:como se citó en|citado en).*$", "", part)
            part = re.sub(r"^(?:cf\.|véase|ver|p\. ej\.,|por ejemplo,)\s*", "", part, flags=re.I)
            ym = re.search(rf",?\s*({YEAR})(?!\w)", part)
            if not ym:
                continue
            authors = part[: ym.start()].strip()
            if not authors:
                continue
            first = re.split(r"\s+y\s+|\s+&\s+|\s+et al\.?|,", authors)[0].strip()
            if first:
                found.add((first, ym.group(1).replace(" ", "")))
    S = rf"[{UP}][{LOW}]+(?: (?:de|del|la|los|las) [{UP}][{LOW}]+)*"
    for m in re.finditer(
            rf"({S})(?:(?:, {S})* y {S}| et al\.)?\s\((\d{{4}}[a-z]?|s\. ?f\.)", body):
        found.add((m.group(1), m.group(2).replace(" ", "")))
    return found


def check_references(refs, body):
    issues = []
    ref_keys = []
    for r in refs:
        ym = re.search(rf"\(\s*({YEAR})", r)
        name = re.split(r",|\. \(|\s\(", r)[0].strip()
        ref_keys.append((name, ym.group(1).replace(" ", "") if ym else None, r))

        short = r[:90] + ("…" if len(r) > 90 else "")
        if re.search(r"\bdoi\s*:|dx\.doi\.org|http://doi\.org", r, re.I):
            issues.append(_issue(
                "Error", short, "El DOI no está en formato de URL.",
                "https://doi.org/xxxxx",
                "APA 7: el DOI se escribe como URL completa (en APA 6 era «doi:»)."))
        if re.search(r"recuperad[oa] de|retrieved from|disponible en", r, re.I):
            issues.append(_issue(
                "Error", short, "Se usa «Recuperado de» o «Disponible en».",
                "Escribe solo la URL, sin frase previa.",
                "APA 7 omite «Recuperado de»; solo se usa fecha de consulta en contenido que cambia."))
        if "&" in r.split("(")[0]:
            issues.append(_issue(
                "Error", short, "Se usa «&» entre autores.",
                "Reemplázalo por «y».", "En español se usa «y» en las referencias."))
        if ym is None:
            issues.append(_issue(
                "Error", short, "No se detecta el año entre paréntesis.",
                "Autor. (año). Título…", "Toda referencia lleva el año entre paréntesis tras el autor."))
        if re.search(r"\bp\.\s?\d+\s?[-–]\s?\d+", r):
            issues.append(_issue(
                "Error", short, "Se usa «p.» con un rango de páginas.",
                "pp. 15-20", "Varias páginas: «pp.»."))
        if re.search(r"\b(?:Madrid|Lima|Bogotá|México|Buenos Aires|Santiago|Barcelona|Nueva York|New York|Londres):\s", r):
            issues.append(_issue(
                "Revisar", short, "Parece incluir el lugar de publicación.",
                "Elimina la ciudad; deja solo la editorial.",
                "APA 7 ya no incluye el lugar de publicación."))

    # Orden alfabético
    names = [_norm(k[2]) for k in ref_keys]
    for i in range(1, len(names)):
        if names[i] < names[i - 1]:
            issues.append(_issue(
                "Error", ref_keys[i][2][:90],
                "La referencia no está en orden alfabético.",
                "Ordena la lista por apellido del primer autor.",
                "La lista de referencias se ordena alfabéticamente."))
            break

    # Cruce citas ↔ referencias
    cited = _parse_in_text_citations(body)

    def match(c, rk):
        a, b = _norm(c[0]), _norm(rk[0])
        return rk[1] == c[1] and (b.startswith(a) or a.startswith(b))

    for c in sorted(cited):
        if not any(match(c, rk) for rk in ref_keys):
            issues.append(_issue(
                "Revisar", f"({c[0]}, {c[1]})",
                "Citada en el texto pero no aparece en las referencias.",
                "Agrega su referencia o corrige apellido/año.",
                "Todo lo citado en el texto debe estar en la lista (excepto comunicaciones personales)."))
    for rk in ref_keys:
        if rk[1] and not any(match(c, rk) for c in cited):
            issues.append(_issue(
                "Revisar", rk[2][:90],
                "Está en las referencias pero no se detecta su cita en el texto.",
                "Cítala en el texto o elimínala de la lista.",
                "Toda referencia debe citarse en el texto. (Si es fuente secundaria, solo va la que leíste.)"))
    return issues


def review_text(text):
    body, ref_text = split_text(text)
    issues = check_body(body)
    refs = []
    note = None
    if ref_text is None:
        note = ("No se encontró un título «Referencias» en una línea aparte; "
                "se revisó solo el cuerpo y no se pudo cruzar citas con referencias.")
    else:
        refs = split_references(ref_text)
        issues += check_references(refs, body)
    return {"issues": issues, "n_refs": len(refs), "note": note}


# ---------------------------------------------------------------------------
# Revisión de formato en archivos .docx
# ---------------------------------------------------------------------------

ALLOWED_FONTS = {
    "times new roman": 12, "calibri": 11, "arial": 11, "georgia": 11,
    "lucida sans unicode": 10, "computer modern": 10,
}


def _style_attr(par, getter):
    st = par.style
    while st is not None:
        val = getter(st)
        if val is not None:
            return val
        st = st.base_style
    return None


# ---------------------------------------------------------------------------
# Tablas (archivo .docx)
# ---------------------------------------------------------------------------

LABEL_RE = re.compile(r"^\s*Tabla\s+(\d+)\s*$", re.IGNORECASE)
LABEL_START_RE = re.compile(r"^\s*Tabla\s+(\d+)\b", re.IGNORECASE)
NIL = (None, "nil", "none")


def _iter_blocks(doc):
    from docx.oxml.ns import qn
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    for child in doc.element.body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, doc)
        elif child.tag == qn("w:tbl"):
            yield Table(child, doc)


def _all_runs_flag(par, attr):
    """True si todos los fragmentos con texto tienen el formato (negrita/cursiva)."""
    runs = [r for r in par.runs if r.text.strip()]
    if not runs:
        return False
    st_val = _style_attr(par, lambda s: getattr(s.font, attr))
    for r in runs:
        v = getattr(r, attr)
        if v is None:
            v = st_val
        if not v:
            return False
    return True


def _bval(el, name):
    from docx.oxml.ns import qn

    if el is None:
        return None
    b = el.find(qn(f"w:{name}"))
    return b.get(qn("w:val")) if b is not None else None


def _table_has_vertical_lines(table):
    from docx.oxml.ns import qn

    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = tblPr.find(qn("w:tblBorders")) if tblPr is not None else None
    if borders is None and table.style is not None:
        borders = table.style.element.find(".//" + qn("w:tblBorders"))
    if borders is not None:
        for name in ("left", "right", "start", "end", "insideV"):
            if _bval(borders, name) not in NIL:
                return True
    elif table.style is not None and any(k in (table.style.name or "").lower() for k in ("grid", "cuadr")):
        return True
    for tc in tbl.iter(qn("w:tc")):
        tcPr = tc.find(qn("w:tcPr"))
        tcb = tcPr.find(qn("w:tcBorders")) if tcPr is not None else None
        if tcb is not None:
            for name in ("left", "right", "start", "end"):
                if _bval(tcb, name) not in NIL:
                    return True
    return False


def _table_has_inner_horizontal(table):
    from docx.oxml.ns import qn

    tblPr = table._tbl.tblPr
    borders = tblPr.find(qn("w:tblBorders")) if tblPr is not None else None
    if borders is None and table.style is not None:
        borders = table.style.element.find(".//" + qn("w:tblBorders"))
    return borders is not None and _bval(borders, "insideH") not in NIL


def review_tables(doc, add):
    blocks = list(_iter_blocks(doc))
    tables = [(i, b) for i, b in enumerate(blocks) if hasattr(b, "rows")]
    if not tables:
        add("OK", "Tablas", "No se detectaron tablas en el documento.")
        return

    label_pars = set()
    numbers = []
    for k, (i, tbl) in enumerate(tables, 1):
        # párrafos no vacíos justo antes y después
        prev = []
        j = i - 1
        while j >= 0 and len(prev) < 2:
            b = blocks[j]
            if hasattr(b, "rows"):
                break
            if b.text.strip():
                prev.append(b)
            j -= 1
        nxt = None
        j = i + 1
        while j < len(blocks):
            b = blocks[j]
            if not hasattr(b, "rows") and b.text.strip():
                nxt = b
                break
            if hasattr(b, "rows"):
                break
            j += 1

        name = f"Tabla (n.º {k} del documento)"
        label = title = None
        if prev and LABEL_RE.match(prev[0].text):
            label = prev[0]  # rótulo sin título
        elif len(prev) == 2 and LABEL_RE.match(prev[1].text):
            label, title = prev[1], prev[0]
        elif prev and LABEL_START_RE.match(prev[0].text):
            add("Error", name, "El número y el título están en la misma línea. APA 7: «Tabla 1» en negrita en una línea, y el título en cursiva en la línea siguiente.")
            label_pars.add(id(prev[0]._p))
            m = LABEL_START_RE.match(prev[0].text)
            numbers.append(int(m.group(1)))
            label = None
            title = "ya reportado"
        else:
            add("Error", name, "No se encontró el rótulo «Tabla N» justo encima de la tabla. APA 7 pide el número y el título arriba de la tabla.")
            title = "ya reportado"

        if label is not None:
            label_pars.add(id(label._p))
            n = int(LABEL_RE.match(label.text).group(1))
            numbers.append(n)
            name = f"Tabla {n}"
            if _all_runs_flag(label, "bold"):
                add("OK", f"{name}: número", "«Tabla N» en negrita")
            else:
                add("Error", f"{name}: número", "«Tabla N» debe ir en negrita.")
            if title is None:
                add("Error", f"{name}: título", "Falta el título de la tabla en la línea siguiente al número (en cursiva).")
            else:
                if _all_runs_flag(title, "italic"):
                    add("OK", f"{name}: título", "En cursiva y en línea aparte")
                else:
                    add("Error", f"{name}: título", "El título debe ir en cursiva (y en negrita solo el número).")
                if _all_runs_flag(title, "bold"):
                    add("Revisar", f"{name}: título", "El título parece estar en negrita; APA 7 lo pide solo en cursiva.")

        # Líneas
        if _table_has_vertical_lines(tbl):
            add("Error", f"{name}: líneas", "Tiene líneas verticales o cuadrícula completa. APA 7: sin líneas verticales; solo líneas horizontales arriba, bajo los encabezados y al final.")
        else:
            add("OK", f"{name}: líneas", "Sin líneas verticales")
        if _table_has_inner_horizontal(tbl):
            add("Revisar", f"{name}: líneas", "Hay líneas horizontales entre todas las filas. APA 7 usa solo arriba, bajo los encabezados y al final.")

        # Tamaño de fuente dentro de la tabla (8 a 14 pt)
        sizes = set()
        for row in tbl.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    for r in p.runs:
                        if r.text.strip() and r.font.size:
                            sizes.add(r.font.size.pt)
        bad = sorted(x for x in sizes if x < 8 or x > 14)
        if bad:
            add("Error", f"{name}: fuente", f"Tamaño(s) {', '.join(str(x) for x in bad)} pt; en tablas APA 7 permite entre 8 y 14 pt.")

        # Nota debajo
        if nxt is not None:
            t = nxt.text.strip()
            if re.match(r"^(nota|notas)\b", t, re.IGNORECASE):
                first = next((r for r in nxt.runs if r.text.strip()), None)
                if not re.match(r"^Nota\.", t):
                    add("Error", f"{name}: nota", "La nota debe empezar con «Nota.» (con punto, no dos puntos).")
                elif first is None or not (first.italic or _style_attr(nxt, lambda s: s.font.italic)):
                    add("Error", f"{name}: nota", "La palabra «Nota.» debe ir en cursiva.")
                else:
                    add("OK", f"{name}: nota", "«Nota.» en cursiva")
            elif re.match(r"^fuente\b", t, re.IGNORECASE):
                add("Revisar", f"{name}: nota", "APA 7 no usa «Fuente:»; la fuente va dentro de la nota: «Nota. Tomado de… / Adaptado de…».")

    # Numeración consecutiva
    if numbers and numbers != list(range(1, len(numbers) + 1)):
        add("Error", "Tablas: numeración", f"La numeración es {numbers}; debe ser consecutiva (1, 2, 3…).")

    # Mención en el texto
    body_text = "\n".join(
        b.text for b in blocks
        if not hasattr(b, "rows") and id(b._p) not in label_pars
    )
    for n in sorted(set(numbers)):
        if not re.search(rf"\bTabla\s+{n}\b", body_text, re.IGNORECASE):
            add("Revisar", f"Tabla {n}: mención", f"No se menciona «Tabla {n}» en el texto. APA 7 pide referirse a cada tabla en el texto.")


def review_docx(path):
    from docx import Document
    from docx.shared import Cm

    doc = Document(path)
    findings = []

    def add(level, item, detail):
        findings.append({"nivel": level, "elemento": item, "detalle": detail})

    sec = doc.sections[0]
    for label, val in (("Superior", sec.top_margin), ("Inferior", sec.bottom_margin),
                       ("Izquierdo", sec.left_margin), ("Derecho", sec.right_margin)):
        cm = val / Cm(1)
        if abs(cm - 2.54) <= 0.15:
            add("OK", f"Margen {label.lower()}", f"{cm:.2f} cm")
        else:
            add("Error", f"Margen {label.lower()}", f"{cm:.2f} cm; APA 7 pide 2,54 cm (1 in) en todos los lados.")

    pars = [p for p in doc.paragraphs if p.text.strip()]
    texts = [p.text for p in pars]
    full = "\n".join(texts)
    _, ref_text = split_text(full)

    # Fuente
    fonts = {}
    for p in pars:
        fname = _style_attr(p, lambda s: s.font.name)
        fsize = _style_attr(p, lambda s: s.font.size)
        for r in p.runs:
            if not r.text.strip():
                continue
            n = r.font.name or fname
            s = r.font.size or fsize
            key = (n.lower() if n else None, round(s.pt, 1) if s else None)
            fonts[key] = fonts.get(key, 0) + len(r.text)
    if fonts:
        (name, size), _n = max(fonts.items(), key=lambda kv: kv[1])
        if name is None:
            add("Revisar", "Fuente", "No se pudo leer (hereda del tema). Verifica a mano: Times New Roman 12, Calibri 11, Arial 11, Georgia 11, etc.")
        elif name in ALLOWED_FONTS:
            if size and abs(size - ALLOWED_FONTS[name]) > 0.1:
                add("Error", "Tamaño de fuente", f"{name.title()} {size} pt; APA 7 sugiere {ALLOWED_FONTS[name]} pt para esa fuente.")
            else:
                add("OK", "Fuente", f"{name.title()} {size or '?'} pt")
        else:
            add("Error", "Fuente", f"{name.title()} no está entre las recomendadas (Times New Roman 12, Calibri 11, Arial 11, Georgia 11, Lucida Sans Unicode 10, Computer Modern 10).")
        if len([k for k in fonts if fonts[k] > 40]) > 2:
            add("Revisar", "Fuentes mezcladas", "Se detectan varias fuentes/tamaños en el texto; APA 7 pide una sola fuente (los títulos y el código pueden variar).")

    # Interlineado y espacio entre párrafos
    ls = []
    sa = []
    for p in pars:
        v = p.paragraph_format.line_spacing or _style_attr(p, lambda s: s.paragraph_format.line_spacing)
        ls.append(v)
        a = p.paragraph_format.space_after
        a = a if a is not None else _style_attr(p, lambda s: s.paragraph_format.space_after)
        sa.append(a)
    known = [v for v in ls if isinstance(v, float)]
    if known:
        doble = sum(1 for v in known if abs(v - 2.0) < 0.05)
        if doble / len(known) >= 0.8:
            add("OK", "Interlineado", "Doble")
        else:
            add("Error", "Interlineado", f"Solo {doble} de {len(known)} párrafos tienen interlineado doble; APA 7 pide doble en todo el documento.")
    else:
        add("Revisar", "Interlineado", "No se pudo leer (hereda del estilo). Verifica a mano que sea doble (2,0).")
    knownsa = [a for a in sa if a is not None]
    if knownsa:
        con_espacio = sum(1 for a in knownsa if a.pt > 0.5)
        if con_espacio > len(knownsa) * 0.3:
            add("Error", "Espacio entre párrafos", "Hay espacio adicional después de los párrafos; APA 7 no lo usa (quita «Espaciado posterior»).")
        else:
            add("OK", "Espacio entre párrafos", "Sin espacio adicional")

    # Sangría de primera línea y sangría francesa
    idx_ref = None
    for i, p in enumerate(pars):
        if REF_HEADERS.match(p.text):
            idx_ref = i
    body_pars = pars[:idx_ref] if idx_ref is not None else pars
    body_long = [p for p in body_pars if len(p.text.split()) > 25 and not p.style.name.lower().startswith(("heading", "título", "title"))]
    if body_long:
        ok = 0
        for p in body_long:
            fi = p.paragraph_format.first_line_indent
            if fi is None:
                fi = _style_attr(p, lambda s: s.paragraph_format.first_line_indent)
            if fi is not None and abs(fi / Cm(1) - 1.27) < 0.15:
                ok += 1
        if ok / len(body_long) >= 0.8:
            add("OK", "Sangría de párrafo", "1,27 cm en la primera línea")
        else:
            add("Error", "Sangría de párrafo", f"Solo {ok} de {len(body_long)} párrafos largos tienen sangría de primera línea de 1,27 cm (0,5 in). Si usas Tab, no se detecta aquí; comprueba a mano.")
    if idx_ref is not None:
        refs = pars[idx_ref + 1:]
        if refs:
            hang = 0
            for p in refs:
                fi = p.paragraph_format.first_line_indent
                li = p.paragraph_format.left_indent
                if fi is not None and li is not None and fi < 0 and abs(abs(fi) / Cm(1) - 1.27) < 0.15:
                    hang += 1
            if hang / len(refs) >= 0.8:
                add("OK", "Sangría francesa", "1,27 cm en las referencias")
            else:
                add("Error", "Sangría francesa", f"Solo {hang} de {len(refs)} referencias tienen sangría francesa de 1,27 cm (Párrafo → Sangría especial → Francesa).")
    else:
        add("Revisar", "Lista de referencias", "No se encontró el título «Referencias» en una línea aparte.")

    # Numeración de páginas
    has_page = False
    for s in doc.sections:
        xml = s.header._element.xml + s.footer._element.xml
        if "PAGE" in xml:
            has_page = True
    add("OK" if has_page else "Error", "Numeración de páginas",
        "Detectada en encabezado/pie" if has_page else "No se detecta. APA 7 pide el número de página arriba a la derecha (encabezado).")

    review_tables(doc, add)

    return {"findings": findings, "text": full}
