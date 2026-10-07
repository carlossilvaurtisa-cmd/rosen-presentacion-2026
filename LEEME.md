# Entrega de fotografías — *La vida de un Rosen*

Mini sitio para entregarle las fotos al cliente. Está armado con el **diseño del
libro** (papel hueso, serif clásica, filetes finos, mucho aire) y el **rojo ROSEN**
usado con cuentagotas: solo en el botón de descargar y en el filtro activo.

---

## Cómo se usa, en tres pasos

**1. Pon las fotos en la carpeta `originales`**

Puedes dejarlas sueltas, o separarlas en subcarpetas. Cada subcarpeta se vuelve
un filtro en la página.

```
originales/
   Retratos/       juan-01.jpg   blanca-02.jpg   ...
   La planta/      nave-01.jpg   pasillo-02.jpg  ...
   Archivo/        baruch.jpg    ...
   suelta.jpg
```

Si hay fotos sueltas en la raíz de `originales`, caen en el filtro **Fotografías**.

**2. Ejecuta el script**

```
cd entrega-fotos
python preparar_fotos.py
```

El script hace todo solo:

| Qué hace | Detalle |
|---|---|
| Gira las verticales | Lee el dato de orientación del EXIF |
| Reduce | El lado más largo queda en 2400 px |
| Comprime | JPEG calidad 82, progresivo |
| Miniaturas | 700 px, para que el muro abra rápido |
| `fotos.json` | La lista que lee la página |
| `leyendas.csv` | Nace con las columnas de título y nota, para que las llenes |
| ZIP | `descargas/rosen-fotografias.zip`, para el botón *Descargar todo* |

> **Los originales nunca se tocan.** Solo se leen.

### Sobre los pies de foto

El script **no inventa pies**. Solo pone uno si el nombre del archivo dice algo
(`juan-en-la-planta_03` → «Juan en la planta 03»). Si el nombre es el que puso la
cámara (`DSC02672`) lo deja vacío: en la galería es mejor no tener pie que tener
uno que no informa a nadie.

Como estas fotos se llaman `DSC0xxxx`, **no hay pies**: la galería queda como un
muro limpio. Si quieres ponerle pies a algunas, escríbelos en `leyendas.csv`,
columna `titulo`, y vuelve a correr el script. También hay una columna `nota`,
que sale en cursiva debajo.

### Sobre los nombres al descargar

Al descargar, cada foto se guarda con **el nombre original del fotógrafo**
(`DSC02676.jpg`), no con el nombre interno numerado. Así tu cliente puede cruzar
las fotos con tu catálogo. Si le pones un título en `leyendas.csv`, se descarga
con ese título en vez del nombre de cámara.

**3. Míralo**

```
python preparar_fotos.py --servir
```

Se abre en `http://127.0.0.1:8000/index.html`. Para apagarlo, `Ctrl + C`.

> Si abres `index.html` haciendo **doble clic**, no se ven las fotos: el navegador
> no deja que una página lea archivos vecinos así. Hay que usar `--servir`
> (o subirlo a un hosting).

---

## Textos que puedes cambiar

| Qué | Dónde |
|---|---|
| Título, subtítulo y fecha de la portada | `index.html`, bloque **BLOQUE 2** |
| Pie con el crédito | `index.html`, bloque **BLOQUE 5** |
| Título y nota de cada foto | `leyendas.csv` (se respeta al volver a correr) |
| **Fotos que NO deben salir** | `excluir.txt` |
| El enlace de alta resolución | `index.html`, bloques **BLOQUE 2** y **BLOQUE 5** |
| Tamaño y calidad | `--max 3000 --calidad 88` |

Para cambiar el título de una foto: abre `leyendas.csv`, escribe en la columna
`titulo`, guarda y vuelve a correr el script.

### Sacar una foto de la galería

Abre `excluir.txt` y escribe el nombre del archivo original, uno por línea:

```
DSC03184.jpg
```

Vuelve a correr el script. La foto sale de la galería, del ZIP y del contador.

**El original NO se borra** — solo se deja fuera del sitio. Y queda excluida de
forma permanente: por más que vuelvas a correr el script, no reaparece. Para
devolverla, bórrala de `excluir.txt` y vuelve a correr.

Hoy hay una excluida: **`DSC03184.jpg`**, el autor sosteniendo el libro con gesto
serio. Quedó como última foto de la galería.

---

## Las fotos que se usaron

Las **126** fotos de `_fotos eventoFINALES`, en orden de captura. Una está
excluida, así que la galería muestra **125**.

| | |
|---|---|
| Originales | 3.120 MB (126 archivos de ~25 MB, 6192 × 4128) |
| Para la web | **80 MB** — un 97 % menos |
| ZIP de todo | 80 MB (125 fotos) |
| Excluidas | 1 → `DSC03184.jpg` |

**La fecha de las fotos no es confiable.** Todas tienen fecha EXIF entre las
23:58 y las 00:03, y el archivo dice `Software: Adobe Lightroom 9.6` — o sea que
la exportación reescribió las fechas y borró el modelo de cámara. Por eso la
portada **no** dice ninguna fecha. Si me pasas la fecha real, la agrego.

---

## Opciones del script

```
python preparar_fotos.py --max 3000 --calidad 88     # más grandes y más pesadas
python preparar_fotos.py --originales "D:\fotos"     # usar otra carpeta de entrada
python preparar_fotos.py --servir                    # ver el resultado
```

| Opción | Por defecto | Para qué |
|---|---|---|
| `--originales` | `originales` | Carpeta de entrada |
| `--max` | `2400` | Lado más largo de la foto grande, en píxeles |
| `--calidad` | `82` | Calidad JPEG (1 a 100) |
| `--servir` | — | Levanta el servidor local y abre el navegador |

---

## El sitio publicado

**https://carlossilvaurtisa-cmd.github.io/rosen-presentacion-2026/**

Ese es el enlace que se le manda al cliente. Está servido por GitHub Pages.

| | |
|---|---|
| Repositorio | `carlossilvaurtisa-cmd/rosen-presentacion-2026` |
| Rama y carpeta | `main`, raíz del repositorio |
| Cuenta | `carlossilvaurtisa-cmd` (GitHub Free) |

**Para actualizar el sitio** después de cambiar algo (textos, fotos nuevas):

```
cd entrega-fotos
git add -A
git commit -m "lo que cambie"
git push
```

GitHub Pages vuelve a compilar solo, en un minuto o dos. Para ver cómo va:

```
gh api repos/carlossilvaurtisa-cmd/rosen-presentacion-2026/pages --jq .status
```

Debe decir `built`.

### ⚠️ Dos cosas que hay que saber

1. **El repositorio es público.** GitHub Free no permite publicar Pages desde un
   repositorio privado. Eso significa que las 120 fotos están accesibles no solo
   por la dirección de la galería, sino también por el repositorio. Le puse
   `noindex` a la página y un `robots.txt` que les pide a los buscadores que no la
   indexen, pero **no es una galería con contraseña**. Si necesitás algo
   realmente privado, hay que pasar a otro servicio (Netlify o Cloudflare Pages,
   que sí permiten proteger el sitio).

2. **El ZIP pesa 76 MB y está dentro del repositorio.** Git avisó que supera los
   50 MB recomendados. Funciona, pero si algún día se suben muchas más fotos o
   archivos más pesados, conviene sacarlo del repositorio y dejar solo el enlace
   de alta resolución.

### El enlace de alta resolución

Los archivos originales, sin comprimir, están en MEGA:

**https://mega.nz/folder/HcAgSQDZ#vQMIJpQkxL67mMblBRcq2w**

Aparece en dos lugares del sitio: el botón **Alta resolución** de la barra de
arriba, y la nota del pie. Para cambiarlo, reemplaza esa dirección en
`index.html` — está en el **BLOQUE 2** (el botón) y en el **BLOQUE 5** (el pie).

---

## Publicar en otro lado (si algún día hace falta)

La carpeta entera es el sitio: se sube tal cual, sin compilar nada.

- **Netlify Drop** → arrastra la carpeta `entrega-fotos` a `app.netlify.com/drop`.
  Devuelve un enlace en segundos y permite protegerlo con contraseña.
- **Cloudflare Pages** o **Vercel** funcionan parecido, pero ojo: Cloudflare
  rechaza archivos de más de 25 MB, y nuestro ZIP pesa 76 MB.

Antes de subir a cualquier lado, corre el script una última vez para que el ZIP y
las miniaturas queden al día.

---

## Qué hay adentro

```
entrega-fotos/
  index.html            la página
  estilos.css           el look del libro
  galeria.js            filtros, visor y descargas
  preparar_fotos.py     el script que prepara todo
  fotos.json            la lista de fotos (lo escribe el script)
  leyendas.csv          títulos y notas (editable)
  excluir.txt           fotos que no deben salir (editable)
  robots.txt            le pide a los buscadores que no indexen la galería
  .nojekyll             le dice a GitHub Pages que no procese los archivos
  originales/           ← aquí pones las fotos crudas
  fotos/                fotos comprimidas + min/
  descargas/            el ZIP
  LEEME.md              este archivo
```

---

## La paleta usada

Del libro, no de la marca:

| Uso | Color |
|---|---|
| Papel | `#F6F2E9` |
| Papel (tono bajo) | `#EDE7DB` |
| Tinta | `#1A1A1A` |
| Tinta suave | `#6E6862` |
| Filetes | `rgba(26,26,26,.14)` |
| **Rojo del libro** (acento) | `#D51921` |

**De dónde salió el rojo.** No es el borgoña de la marca: se midió sobre las
propias fotos de la presentación. Sobre 822.901 píxeles de rojo bien iluminado
—la portada y el telón de fondo— la mediana dio `#D51921`. Es el vermellón de la
tapa, y es el único color del sitio.

La **marca ROSEN** (rojo borgoña + blanco + azul, óvalos concéntricos, líneas
horizontales, sans redondeada gruesa) **no se usa**: el sitio sigue al libro.

Los **pétalos** de la portada aparecen sueltos y apenas transparentes en la
cabecera, como textura. Son lo único que hace que el sitio se reconozca como
«el libro». Para sacarlos: borra el bloque `<span class="petalos">` en
`index.html` (está dentro del **BLOQUE 2**).
