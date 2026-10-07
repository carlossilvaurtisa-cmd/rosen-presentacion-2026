# ============================================================
# BLOQUE 20: QUÉ HACE ESTE SCRIPT Y QUÉ NECESITA
# ------------------------------------------------------------
# Toma las fotos que están en la carpeta "originales" (tal como
# salen de la cámara), y las deja listas para la web:
#
#   1. Las gira si vienen de costado (el dato viene del EXIF).
#   2. Las reduce: el lado más largo queda en 2400 px.
#   3. Las convierte a JPEG con calidad 82 (se ven igual, pesan
#      mucho menos).
#   4. Hace una miniatura de 700 px para el muro de la página.
#   5. Escribe "fotos.json", que es la lista que lee la web.
#   6. Arma un ZIP con todo, para el botón "Descargar todo".
#
# Los ORIGINALES NUNCA SE TOCAN. Solo se leen.
#
# Si dentro de "originales" hay SUBCARPETAS, cada subcarpeta se
# vuelve una categoría de filtro en la página. Por ejemplo:
#   originales/Retratos/...      →  filtro "Retratos"
#   originales/La planta/...     →  filtro "La planta"
#   originales/suelta.jpg        →  filtro "Fotografías"
# ============================================================
import argparse, csv, json, os, re, sys, unicodedata, zipfile
from datetime import datetime
from pathlib import Path

# --- Dónde está cada cosa (todo relativo a este archivo) ---
RAIZ        = Path(__file__).resolve().parent
DIR_ORIG    = RAIZ / 'originales'      # entrada: las fotos crudas
DIR_WEB     = RAIZ / 'fotos'           # salida: fotos comprimidas
DIR_MIN     = DIR_WEB / 'min'          # salida: miniaturas
DIR_DESC    = RAIZ / 'descargas'       # salida: el ZIP
CSV_LEYENDAS = RAIZ / 'leyendas.csv'   # títulos y notas, editable
ARCH_EXCLUIR = RAIZ / 'excluir.txt'    # fotos que no salen, editable
ARCH_MANIF   = RAIZ / 'fotos.json'     # la lista que lee el sitio
ARCH_ZIP     = DIR_DESC / 'rosen-fotografias.zip'

MAX_LADO   = 2400   # px del lado más largo de la foto grande
CALIDAD    = 82     # 1-100. 82 es el punto dulce para fotos
MAX_MIN    = 700    # px del lado más largo de la miniatura
CALIDAD_MIN= 78
COLOR_FONDO= (246, 242, 233)   # el hueso del sitio, por si hay transparencia

# Extensiones que el script reconoce como fotos
EXTENSIONES = {'.jpg', '.jpeg', '.png', '.tif', '.tiff', '.webp', '.bmp', '.heic', '.heif'}
# FIN BLOQUE 20


# ============================================================
# BLOQUE 21: FUNCIONES DE APOYO
# ============================================================
def pedir_pillow():
    """Carga Pillow (la librería de imágenes) y avisa si falta."""
    try:
        from PIL import Image, ImageOps
    except ImportError:
        print('\nFalta Pillow. Instálalo con:\n   pip install Pillow\n')
        sys.exit(1)

    # Soporte para fotos HEIC/HEIF (las de iPhone). Si no está, no pasa nada.
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError:
        pass

    return Image, ImageOps


def orden_natural(texto):
    """
    Ordena como lo hace una persona: foto2 va antes que foto10.
    (Ordenar por texto pondría foto10 antes que foto2: mal.)
    """
    return [int(t) if t.isdigit() else t.lower()
            for t in re.split(r'(\d+)', str(texto))]


def limpiar_nombre(texto):
    """Deja el nombre en algo seguro para una dirección web."""
    texto = unicodedata.normalize('NFKD', str(texto))
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    texto = texto.lower()
    texto = re.sub(r'[^a-z0-9]+', '-', texto).strip('-')
    return texto or 'foto'


def titulo_legible(nombre):
    """De 'juan-en-la-planta_03' saca 'Juan En La Planta 03'."""
    base = re.sub(r'[_\-.]+', ' ', str(nombre)).strip()
    base = re.sub(r'\s+', ' ', base)
    return base[:1].upper() + base[1:] if base else 'Fotografía'


# Los nombres que pone la cámara sola: DSC02672, IMG_1234, P1000123,
# _MG_1234, GOPR1234, DJI_0001, capturas de pantalla…
PLANTILLA_CAMARA = re.compile(
    r'^(dsc|dscf|img|p|mg|gopr|mvi|sam|pict|dji|vlcsnap|captura|screenshot|foto|photo)\d+$'
)


def titulo_automatico(nombre):
    """
    Inventa un título a partir del nombre del archivo, PERO solo si el
    nombre dice algo. Si es el nombre que puso la cámara (DSC02672), no
    inventa nada: en la galería es mejor no tener pie que tener un pie
    que no informa a nadie. Si quieres uno, se escribe en leyendas.csv.
    """
    crudo = str(nombre).strip()
    compacto = re.sub(r'[^a-z0-9]', '', crudo.lower())
    if not compacto or compacto.isdigit() or PLANTILLA_CAMARA.match(compacto):
        return ''
    return titulo_legible(crudo)


def listar_originales(dir_orig):
    """
    Devuelve una lista de (ruta, categoria) recorriendo 'originales'.
    Si hay subcarpetas, el nombre de la subcarpeta es la categoría.
    """
    encontrados = []
    if not dir_orig.exists():
        return encontrados

    # Fotos sueltas en la raíz de "originales"
    for archivo in sorted(dir_orig.iterdir(), key=lambda p: orden_natural(p.name)):
        if archivo.is_file() and archivo.suffix.lower() in EXTENSIONES:
            encontrados.append((archivo, 'Fotografías'))

    # Fotos dentro de subcarpetas (una categoría por subcarpeta)
    for sub in sorted([d for d in dir_orig.iterdir() if d.is_dir()], key=lambda p: orden_natural(p.name)):
        for archivo in sorted(sub.rglob('*'), key=lambda p: orden_natural(p.name)):
            if archivo.is_file() and archivo.suffix.lower() in EXTENSIONES:
                encontrados.append((archivo, sub.name))

    return encontrados
# FIN BLOQUE 21


# ============================================================
# BLOQUE 22: LAS LEYENDAS (títulos y notas)
# ------------------------------------------------------------
# Se crea un archivo "leyendas.csv" la primera vez, ya rellenado
# con un título probable. El usuario lo abre, corrige lo que
# quiera y vuelve a correr el script: sus textos se respetan.
# ============================================================
CABECERA = ['archivo', 'categoria', 'titulo', 'nota']

def leer_leyendas():
    """Lee leyendas.csv y devuelve un diccionario archivo -> (categoria, titulo, nota)."""
    guardadas = {}
    if not CSV_LEYENDAS.exists():
        return guardadas
    with open(CSV_LEYENDAS, 'r', encoding='utf-8-sig', newline='') as f:
        for fila in csv.DictReader(f, delimiter=';'):
            clave = (fila.get('archivo') or '').strip()
            if clave:
                guardadas[clave] = (
                    (fila.get('categoria') or '').strip(),
                    (fila.get('titulo') or '').strip(),
                    (fila.get('nota') or '').strip(),
                )
    return guardadas


def escribir_leyendas(filas):
    """Guarda leyendas.csv, respetando lo que el usuario ya escribió."""
    with open(CSV_LEYENDAS, 'w', encoding='utf-8-sig', newline='') as f:
        escritor = csv.DictWriter(f, fieldnames=CABECERA, delimiter=';')
        escritor.writeheader()
        for fila in filas:
            escritor.writerow(fila)


# ------------------------------------------------------------
# LAS EXCLUSIONES (excluir.txt)
# ------------------------------------------------------------
# Una foto por línea, con el nombre del archivo original. Las que
# estén ahí NO salen en la galería. Los originales NO se borran:
# solo se dejan fuera de la página. Es la forma de sacar una foto
# sin que vuelva a aparecer la próxima vez que corras el script.
PLANTILLA_EXCLUIR = """\
# Fotos que NO deben salir en la galería.
#
# Escribe una por línea, con el nombre del archivo original.
# Ejemplo:
#   DSC03184.jpg
#
# Las líneas que empiezan con # no se leen.
# Los archivos originales NO se borran: solo se dejan fuera del sitio.
"""


def leer_exclusiones():
    """Devuelve el conjunto de nombres de archivo que hay que dejar fuera."""
    if not ARCH_EXCLUIR.exists():
        with open(ARCH_EXCLUIR, 'w', encoding='utf-8') as f:
            f.write(PLANTILLA_EXCLUIR)
        return set()

    fuera = set()
    with open(ARCH_EXCLUIR, 'r', encoding='utf-8-sig') as f:
        for linea in f:
            nombre = linea.strip()
            if not nombre or nombre.startswith('#'):
                continue
            fuera.add(nombre.lower())
    return fuera


def esta_excluida(ruta, excluidas):
    """¿Esta foto está en la lista de exclusiones? Compara con y sin extensión."""
    return ruta.name.lower() in excluidas or ruta.stem.lower() in excluidas
# FIN BLOQUE 22


# ============================================================
# BLOQUE 23: REDIMENSIONAR Y COMPRIMIR
# ============================================================
def redimensionar(imagen, lado_max, Image):
    """Achica la imagen solo si es más grande. Si ya es chica, no la toca."""
    ancho, alto = imagen.size
    lado_mayor = max(ancho, alto)
    if lado_mayor <= lado_max:
        return imagen
    factor = lado_max / float(lado_mayor)
    nuevo = (max(1, round(ancho * factor)), max(1, round(alto * factor)))
    return imagen.resize(nuevo, Image.LANCZOS)


def a_color_seguro(imagen, Image):
    """
    Deja la imagen en RGB, que es lo que entiende el JPEG.
    Si venía con transparencia, la rellena con el color hueso
    del sitio para que no quede un borde feo.
    """
    if imagen.mode in ('RGBA', 'LA', 'P'):
        imagen = imagen.convert('RGBA')
        fondo = Image.new('RGB', imagen.size, COLOR_FONDO)
        fondo.paste(imagen, mask=imagen.split()[-1])
        return fondo
    if imagen.mode != 'RGB':
        return imagen.convert('RGB')
    return imagen


def preparar_una(ruta, categoria, indice, leyendas, Image, ImageOps):
    """
    Procesa UNA foto: la gira, la achica, la comprime, le hace la
    miniatura, y devuelve la ficha que irá al manifiesto.
    """
    with Image.open(ruta) as original:
        # 1. Girar según el EXIF (si no, las verticales salen acostadas)
        imagen = ImageOps.exif_transpose(original)
        imagen = a_color_seguro(imagen, Image)

        ancho, alto = imagen.size

        # 2. La foto grande, para el visor y para descargar
        grande = redimensionar(imagen, MAX_LADO, Image)
        nombre_base = '%03d-%s' % (indice, limpiar_nombre(ruta.stem))
        destino = DIR_WEB / (nombre_base + '.jpg')
        grande.save(destino, 'JPEG', quality=CALIDAD, optimize=True,
                    progressive=True, subsampling='4:2:0')

        # 3. La miniatura, solo para el muro de la galería
        chica = redimensionar(imagen, MAX_MIN, Image)
        destino_min = DIR_MIN / (nombre_base + '.jpg')
        chica.save(destino_min, 'JPEG', quality=CALIDAD_MIN, optimize=True,
                   progressive=True)

    # 4. Los textos: lo que el usuario escribió manda; si no, se inventa
    guardado = leyendas.get(ruta.name)
    cat_final = (guardado[0] if guardado and guardado[0] else categoria)
    titulo    = (guardado[1] if guardado and guardado[1] else titulo_automatico(ruta.stem))
    nota      = (guardado[2] if guardado and guardado[2] else '')

    return {
        'archivo':    'fotos/' + destino.name,
        'miniatura':  'fotos/min/' + destino_min.name,
        'categoria':  cat_final,
        'titulo':     titulo,
        'nota':       nota,
        'ancho':      grande.size[0],
        'alto':       grande.size[1],
        'peso_kb':    round(destino.stat().st_size / 1024),
        'original':   ruta.name,
        '_peso_orig': ruta.stat().st_size,
    }, {'archivo': ruta.name, 'categoria': cat_final, 'titulo': titulo, 'nota': nota}
# FIN BLOQUE 23


# ============================================================
# BLOQUE 24: EL MANIFIESTO Y EL ZIP
# ============================================================
def escribir_manifiesto(fotos, Image):
    """Escribe fotos.json: la lista que lee la página."""
    # Orden de categorías: el que aparece en la carpeta, sin repetir
    categorias = []
    for foto in fotos:
        if foto['categoria'] not in categorias:
            categorias.append(foto['categoria'])

    # Al manifiesto no le hacen falta los datos internos
    publicas = [{k: v for k, v in foto.items() if not k.startswith('_')} for foto in fotos]

    datos = {
        'titulo':     'La vida de un Rosen',
        'subtitulo':  'Biografía de Juan de Dios Rosenberg V.',
        'generado':   datetime.now().strftime('%Y-%m-%d %H:%M'),
        'zip':        'descargas/' + ARCH_ZIP.name,
        'total':      len(publicas),
        'categorias': categorias,
        'fotos':      publicas,
    }
    with open(ARCH_MANIF, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)
    return categorias


def armar_zip(fotos):
    """Junta todas las fotos comprimidas en un solo ZIP."""
    DIR_DESC.mkdir(parents=True, exist_ok=True)
    if ARCH_ZIP.exists():
        ARCH_ZIP.unlink()
    # ZIP_STORED: el JPEG ya viene comprimido, volver a comprimirlo no ayuda
    with zipfile.ZipFile(ARCH_ZIP, 'w', zipfile.ZIP_STORED) as z:
        for foto in fotos:
            ruta = RAIZ / foto['archivo']
            if ruta.exists():
                z.write(ruta, arcname=Path(foto['archivo']).name)
    return ARCH_ZIP.stat().st_size
# FIN BLOQUE 24


# ============================================================
# BLOQUE 25: EL PROGRAMA PRINCIPAL
# ============================================================
def borrar_salidas_anteriores():
    """Limpia las salidas viejas para que no queden fotos huérfanas."""
    for carpeta in (DIR_WEB, DIR_MIN):
        if carpeta.exists():
            for viejo in carpeta.glob('*'):
                if viejo.is_file():
                    viejo.unlink()
    DIR_WEB.mkdir(parents=True, exist_ok=True)
    DIR_MIN.mkdir(parents=True, exist_ok=True)


def servir(ancho=1280):
    """Levanta un servidor local y abre el navegador. Es la forma
    correcta de ver la página: con doble clic no funciona."""
    import http.server, socketserver, threading, webbrowser
    os.chdir(RAIZ)
    manejador = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(('127.0.0.1', 8000), manejador) as httpd:
        direccion = 'http://127.0.0.1:8000/index.html'
        print('\n  Servidor local encendido en:\n  ' + direccion)
        print('\n  Para apagarlo: Ctrl + C\n')
        threading.Timer(1.0, lambda: webbrowser.open(direccion)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\n  Servidor apagado.\n')


def main():
    global MAX_LADO, CALIDAD, DIR_ORIG

    ap = argparse.ArgumentParser(description='Prepara las fotos para el sitio de entrega.')
    ap.add_argument('--originales', default=str(DIR_ORIG),
                    help='Carpeta con las fotos crudas (por defecto: originales)')
    ap.add_argument('--max', type=int, default=MAX_LADO,
                    help='Lado más largo de la foto grande en px (por defecto 2400)')
    ap.add_argument('--calidad', type=int, default=CALIDAD,
                    help='Calidad JPEG 1-100 (por defecto 82)')
    ap.add_argument('--servir', action='store_true',
                    help='Levanta el servidor local al terminar')
    args = ap.parse_args()

    MAX_LADO = args.max
    CALIDAD  = args.calidad
    DIR_ORIG = Path(args.originales)

    Image, ImageOps = pedir_pillow()

    if not DIR_ORIG.exists():
        DIR_ORIG.mkdir(parents=True, exist_ok=True)
        print('\n  Creé la carpeta "originales".')
        print('  Pon ahí las fotos (y subcarpetas para las categorías) y vuelve a correr.\n')
        return

    entrantes = listar_originales(DIR_ORIG)
    if not entrantes:
        print('\n  No hay fotos en ' + str(DIR_ORIG))
        print('  Formatos que reconozco: ' + ', '.join(sorted(EXTENSIONES)) + '\n')
        return

    # Sacar las que estén en excluir.txt (no se borran: solo no salen)
    excluidas = leer_exclusiones()
    if excluidas:
        antes = len(entrantes)
        entrantes = [(r, c) for (r, c) in entrantes if not esta_excluida(r, excluidas)]
        quitadas = antes - len(entrantes)
        if quitadas:
            print('\n  Fuera de la galería por excluir.txt: %d foto(s).' % quitadas)

    if not entrantes:
        print('\n  Todas las fotos están excluidas en excluir.txt. Nada que hacer.\n')
        return

    print('\n  Encontré %d fotos. Preparando...\n' % len(entrantes))
    borrar_salidas_anteriores()
    leyendas = leer_leyendas()

    fotos, filas_csv = [], []
    peso_original = 0
    for i, (ruta, categoria) in enumerate(entrantes, start=1):
        try:
            ficha, fila = preparar_una(ruta, categoria, i, leyendas, Image, ImageOps)
            fotos.append(ficha)
            filas_csv.append(fila)
            peso_original += ficha['_peso_orig']
            print('  %3d/%d  %-42s → %4d KB' %
                  (i, len(entrantes), ruta.name[:42], ficha['peso_kb']))
        except Exception as error:
            print('  ¡Ojo! No pude con %s → %s' % (ruta.name, error))

    if not fotos:
        print('\n  Ninguna foto se pudo procesar.\n')
        return

    escribir_leyendas(filas_csv)
    categorias = escribir_manifiesto(fotos, Image)
    peso_zip = armar_zip(fotos)

    peso_web = sum(f['peso_kb'] for f in fotos) / 1024.0
    peso_orig_mb = peso_original / 1024.0 / 1024.0

    print('\n  ' + '-' * 54)
    print('  Listo. %d fotos en %d categorías.' % (len(fotos), len(categorias)))
    print('  Categorías: ' + ', '.join(categorias))
    print('  Originales:   %6.1f MB' % peso_orig_mb)
    print('  Para la web:  %6.1f MB   (%.0f %% menos)' %
          (peso_web, 100 - (peso_web / peso_orig_mb * 100) if peso_orig_mb else 0))
    print('  ZIP de todo:  %6.1f MB' % (peso_zip / 1024 / 1024))
    print('  ' + '-' * 54)
    print('\n  Archivos que puedes editar:')
    print('   · leyendas.csv  → títulos y notas de cada foto')
    print('   · excluir.txt   → fotos que NO deben salir en la galería')
    print('   · index.html    → los textos de la portada')
    print('\n  Para verlo:  python preparar_fotos.py --servir\n')

    if args.servir:
        servir()


if __name__ == '__main__':
    main()
# FIN BLOQUE 25
