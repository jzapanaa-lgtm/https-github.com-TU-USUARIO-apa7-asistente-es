import tempfile

import streamlit as st

from apa_checks import review_docx, review_text

st.set_page_config(page_title="Revisor APA 7.ª edición", page_icon="📚", layout="wide")

st.title("📚 Revisor APA 7.ª edición")
st.caption(
    "Pega tu texto o sube tu archivo Word (.docx) y revisa citas, referencias y formato. "
    "Es una ayuda de estudio basada en reglas: confirma siempre con el manual oficial "
    "(apastyle.apa.org) y con las normas de tu institución."
)

tab_texto, tab_docx, tab_ayuda = st.tabs(
    ["📝 Pegar texto", "📄 Subir archivo Word", "ℹ️ Qué revisa"]
)


def mostrar_issues(res):
    issues = res["issues"]
    if res.get("note"):
        st.info(res["note"])
    c1, c2, c3 = st.columns(3)
    errores = [i for i in issues if i["nivel"] == "Error"]
    revisar = [i for i in issues if i["nivel"] == "Revisar"]
    c1.metric("Errores", len(errores))
    c2.metric("Para revisar", len(revisar))
    c3.metric("Referencias detectadas", res["n_refs"])
    if not issues:
        st.success("No se detectaron problemas con las reglas automáticas. "
                   "Aun así, revisa a mano lo que el programa no puede ver.")
        return
    for n, i in enumerate(issues, 1):
        icono = "🔴" if i["nivel"] == "Error" else "🟡"
        with st.expander(f"{icono} {n}. {i['problema']}"):
            st.markdown(f"**Dónde:** `{i['donde']}`")
            st.markdown(f"**Cómo corregirlo:** {i['correccion']}")
            st.markdown(f"**Regla:** {i['regla']}")


with tab_texto:
    st.markdown(
        "Pega tu texto **con la lista de referencias al final**, bajo un título «Referencias» "
        "en una línea aparte. Al pegar texto se pierde el formato visual (márgenes, fuente, "
        "interlineado); para eso usa la pestaña de archivo Word."
    )
    texto = st.text_area("Tu texto", height=350, placeholder="Pega aquí tu texto…")
    if st.button("Revisar texto", type="primary"):
        if len(texto.strip()) < 30:
            st.warning("Pega un texto más largo para revisar.")
        else:
            mostrar_issues(review_text(texto))

with tab_docx:
    st.markdown(
        "Sube tu documento en formato **.docx**. Se revisan márgenes, fuente, interlineado, "
        "sangrías, numeración de páginas y también las citas y referencias del texto."
    )
    archivo = st.file_uploader("Archivo Word", type=["docx"])
    if archivo is not None and st.button("Revisar archivo", type="primary"):
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=True) as tmp:
            tmp.write(archivo.getbuffer())
            tmp.flush()
            try:
                res = review_docx(tmp.name)
            except Exception:
                st.error("No se pudo leer el archivo. Verifica que sea un .docx válido.")
                st.stop()
        st.subheader("Formato del documento")
        for f in res["findings"]:
            icono = {"OK": "✅", "Error": "🔴", "Revisar": "🟡"}[f["nivel"]]
            st.markdown(f"{icono} **{f['elemento']}:** {f['detalle']}")
        st.subheader("Citas y referencias")
        mostrar_issues(review_text(res["text"]))

with tab_ayuda:
    st.markdown(
        """
**Citas y referencias (texto)**
- «&» en lugar de «y», iniciales en citas, 3 o más autores sin *et al.*
- Formas incorrectas de *et al.*, *s. f.*, *p.* / *pp.*, y uso de *ibid.* u *op. cit.*
- Citas textuales sin página y citas de 40 palabras o más que deben ir en bloque
- DOI sin formato de URL, «Recuperado de», lugar de publicación
- Orden alfabético y correspondencia entre citas y lista de referencias

**Formato (archivo Word)**
- Márgenes de 2,54 cm, fuente y tamaño permitidos, interlineado doble
- Sin espacio extra entre párrafos, sangría de 1,27 cm, sangría francesa en referencias
- Numeración de páginas en el encabezado

**Lo que NO puede verificar**
- Cursivas en títulos de libros y revistas, niveles de títulos, tablas y figuras
- Si los datos de tu referencia (autor, año, DOI) son reales o están completos
- Requisitos propios de tu universidad o docente, que pueden prevalecer

Los resultados marcados 🟡 son sospechas, no errores seguros: verifícalos.
"""
    )

st.divider()
st.caption("Proyecto independiente, sin afiliación con la American Psychological Association.")
