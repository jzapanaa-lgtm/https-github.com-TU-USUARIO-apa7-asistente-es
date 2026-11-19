# Asistente APA 7.ª edición (español)

Asistente experto en normas APA, 7.ª edición, para estudiantes e investigadores de habla
hispana. Ayuda a citar y formatear correctamente, explica la regla aplicada y **nunca inventa**
autores, fechas ni DOI.

## ¿Qué hace?

1. **Genera referencias**: libros, artículos, páginas web, tesis, videos, informes, leyes,
   redes sociales, IA generativa, etc.
2. **Genera citas en el texto**: parentética y narrativa; 1, 2 y 3 o más autores; citas
   directas con página; fuentes secundarias.
3. **Revisa y corrige** referencias o citas, explicando cada error.
4. **Explica el formato del documento**: márgenes, fuente, interlineado, sangría, títulos,
   tablas y figuras, portada y numeración.

## Formato de respuesta

```
Referencia:
Cita parentética:
Cita narrativa:
Nota: (regla aplicada)
```

## Estructura del repositorio

```
apa7-asistente-es/
├── README.md
├── SYSTEM_PROMPT.md                  # instrucciones del asistente (núcleo)
└── docs/
    ├── guia-formato-apa7.md          # formato del documento + cambios APA 6 → 7
    ├── guia-tablas-apa7.md           # tablas: formato, notas, Word y lista de verificación
    └── plantillas-referencias.md     # plantillas de referencias y citas
```

## Cómo usarlo

El archivo `SYSTEM_PROMPT.md` contiene las instrucciones. Úsalo en la plataforma que prefieras:

- **Claude**: crea un Proyecto, pega el contenido en «Instrucciones del proyecto» y sube
  los archivos de `docs/` como conocimiento.
- **ChatGPT**: crea un GPT personalizado, pega el prompt en «Instrucciones» y sube `docs/`.
- **Gemini**: crea un Gem con el prompt.
- **GitHub Copilot**: copia el contenido a `.github/copilot-instructions.md` en tu repo.
- **API**: envía el contenido de `SYSTEM_PROMPT.md` como mensaje de sistema.

## Publicar en GitHub

1. Crea un repositorio nuevo en https://github.com/new (por ejemplo, `apa7-asistente-es`).
2. En tu computadora, dentro de esta carpeta:

```bash
git init
git add .
git commit -m "Asistente APA 7 en español: versión inicial"
git branch -M main
git remote add origin https://github.com/TU-USUARIO/apa7-asistente-es.git
git push -u origin main
```

También puedes arrastrar los archivos a la página del repositorio con «Add file → Upload files».

## Advertencias

- Es una ayuda de estudio: **verifica** el resultado con el manual oficial
  (https://apastyle.apa.org) y con las normas de tu institución, que pueden prevalecer.
- Las referencias jurídicas varían según el país; el asistente preguntará cuál usas.
- Un asistente de IA puede equivocarse. Revisa que cada dato corresponda a tu fuente real.

## Contribuir

Las correcciones y nuevos ejemplos son bienvenidos mediante *issues* o *pull requests*.
Si propones un cambio de norma, cita la sección del manual que lo respalda.

## Licencia

Elige la que prefieras (por ejemplo, MIT para el código y CC BY 4.0 para la documentación) y
agrega un archivo `LICENSE`.

*Proyecto independiente, sin afiliación con la American Psychological Association.*
