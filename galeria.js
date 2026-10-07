/* ============================================================
   BLOQUE 14: AJUSTES Y ESTADO
   ------------------------------------------------------------
   CONFIG es lo único que hay que tocar si cambia una ruta.
   Después, tres variables guardan el estado de la página:
   · FOTOS    → todas las fotos leídas del manifiesto
   · VISIBLES → las que se están mostrando según el filtro
   · indice   → en qué foto está el visor a pantalla completa
   ============================================================ */
const CONFIG = {
  manifiesto: 'fotos.json',                        // la lista de fotos
  zip:        'descargas/rosen-fotografias.zip'    // el paquete de todo
};

let FOTOS    = [];
let VISIBLES = [];
let indice   = 0;
let categoriaActual = 'Todas';

/* Atajos a los elementos de la página, para no buscarlos mil veces */
const $ = (id) => document.getElementById(id);
const elGaleria   = $('galeria');
const elVacio     = $('vacio');
const elFiltros   = $('filtros');
const elCuenta    = $('cuenta');
const elZip       = $('descargarTodo');
const elVisor     = $('visor');
const elVisorImg  = $('visorImagen');
const elVisorTit  = $('visorTitulo');
const elVisorNota = $('visorNota');
const elVisorCont = $('visorContador');
const elVisorDesc = $('visorDescargar');
/* FIN BLOQUE 14 */


/* ============================================================
   BLOQUE 15: LEER EL MANIFIESTO
   ------------------------------------------------------------
   fotos.json lo escribe preparar_fotos.py. Si el sitio se abre
   haciendo doble clic al archivo (dirección file://), el
   navegador bloquea la lectura y hay que avisarlo con claridad.
   ============================================================ */
async function arrancar(){
  let datos;
  try{
    const respuesta = await fetch(CONFIG.manifiesto, { cache: 'no-store' });
    if(!respuesta.ok) throw new Error('HTTP ' + respuesta.status);
    datos = await respuesta.json();
  }catch(error){
    /* Hay dos motivos distintos por los que no se puede leer la lista,
       y conviene decir cuál es:
       · si la página se abrió con doble clic (file://), el navegador
         bloquea la lectura por seguridad;
       · si se sirvió bien pero el manifiesto no existe todavía,
         simplemente es que aún no se corrieron las fotos. */
    if(location.protocol === 'file:') mostrarAvisoDeServidor();
    else                             mostrarSinFotos();
    console.error('No se pudo leer ' + CONFIG.manifiesto, error);
    return;
  }

  FOTOS = Array.isArray(datos.fotos) ? datos.fotos : [];

  if(datos.zip) elZip.setAttribute('href', datos.zip);
  else          elZip.setAttribute('href', CONFIG.zip);

  if(FOTOS.length === 0){
    mostrarSinFotos();
    return;
  }

  pintarFiltros(datos.categorias || []);
  aplicarFiltro('Todas');
  prepararVisor();
}
/* FIN BLOQUE 15 */


/* ============================================================
   BLOQUE 16: LOS FILTROS
   ------------------------------------------------------------
   Se arman solos con las categorías que traiga el manifiesto.
   "Todas" siempre va primero.
   ============================================================ */
function pintarFiltros(categorias){
  const lista = ['Todas'].concat(categorias.filter(c => c && c !== 'Todas'));
  elFiltros.innerHTML = '';

  lista.forEach(nombre => {
    const boton = document.createElement('button');
    boton.type = 'button';
    boton.className = 'filtro';
    boton.textContent = nombre;
    boton.setAttribute('aria-pressed', String(nombre === 'Todas'));
    boton.addEventListener('click', () => aplicarFiltro(nombre));
    elFiltros.appendChild(boton);
  });
}

function aplicarFiltro(nombre){
  categoriaActual = nombre;

  /* Marcar el botón activo */
  elFiltros.querySelectorAll('.filtro').forEach(boton => {
    boton.setAttribute('aria-pressed', String(boton.textContent === nombre));
  });

  VISIBLES = (nombre === 'Todas')
    ? FOTOS.slice()
    : FOTOS.filter(foto => foto.categoria === nombre);

  pintarCuenta();
  pintarGaleria();
}
/* FIN BLOQUE 16 */


/* ============================================================
   BLOQUE 17: DIBUJAR LA GALERÍA
   ------------------------------------------------------------
   Cada foto se envuelve en un <figure> con su marco (el botón
   que la abre) y su pie en cursiva, como los pies del libro.
   Las imágenes se cargan con "loading=lazy": el navegador solo
   baja las que están por aparecer en pantalla. Eso es lo que
   hace que la página abra rápido aunque haya 200 fotos.
   ============================================================ */
function pintarCuenta(){
  const n = VISIBLES.length;
  elCuenta.textContent = n === 1 ? '1 fotografía' : n + ' fotografías';
}

function pintarGaleria(){
  const trozo = document.createDocumentFragment();

  VISIBLES.forEach((foto, posicion) => {
    const figura = document.createElement('figure');
    figura.className = 'foto';

    const marco = document.createElement('button');
    marco.type = 'button';
    marco.className = 'foto-marco';
    marco.title = 'Ver a pantalla completa';
    marco.addEventListener('click', () => abrirVisor(posicion));

    const imagen = document.createElement('img');
    imagen.src = foto.miniatura || foto.archivo;
    imagen.alt = foto.titulo || 'Fotografía';
    imagen.loading = 'lazy';
    imagen.decoding = 'async';
    /* Ancho y alto reales: el navegador reserva el hueco y la
       página no salta mientras las fotos van llegando */
    if(foto.ancho && foto.alto){
      imagen.width  = foto.ancho;
      imagen.height = foto.alto;
    }
    imagen.className = 'cargando';
    imagen.addEventListener('load',  () => imagen.classList.remove('cargando'));
    imagen.addEventListener('error', () => imagen.classList.remove('cargando'));

    marco.appendChild(imagen);
    figura.appendChild(marco);

    /* El pie solo se dibuja si hay algo que decir */
    if(foto.titulo || foto.nota){
      const pie = document.createElement('figcaption');
      pie.className = 'foto-pie';
      if(foto.titulo){
        const fuerte = document.createElement('b');
        fuerte.textContent = foto.titulo;
        pie.appendChild(fuerte);
      }
      if(foto.nota) pie.appendChild(document.createTextNode(foto.nota));
      figura.appendChild(pie);
    }

    trozo.appendChild(figura);
  });

  elGaleria.innerHTML = '';
  elGaleria.appendChild(trozo);
}
/* FIN BLOQUE 17 */


/* ============================================================
   BLOQUE 18: EL VISOR A PANTALLA COMPLETA
   ------------------------------------------------------------
   Se abre al hacer clic en una foto. Se navega con las flechas
   del teclado, con las flechas de los costados, o con Escape
   para cerrar.
   ============================================================ */
function prepararVisor(){
  $('visorCerrar').addEventListener('click', cerrarVisor);
  $('flechaIzq').addEventListener('click', (e) => { e.stopPropagation(); mover(-1); });
  $('flechaDer').addEventListener('click', (e) => { e.stopPropagation(); mover(1); });

  /* Al hacer clic en el fondo negro (no en la foto) se cierra */
  elVisor.addEventListener('click', (evento) => {
    if(evento.target === elVisor || evento.target.classList.contains('visor-lienzo')) cerrarVisor();
  });

  document.addEventListener('keydown', (evento) => {
    if(elVisor.hidden) return;
    if(evento.key === 'Escape')     cerrarVisor();
    if(evento.key === 'ArrowLeft')  mover(-1);
    if(evento.key === 'ArrowRight') mover(1);
  });
}

function abrirVisor(posicion){
  indice = posicion;
  elVisor.hidden = false;
  document.body.style.overflow = 'hidden';   /* que el fondo no scrollee */
  mostrarEnVisor();
}

function cerrarVisor(){
  elVisor.hidden = true;
  document.body.style.overflow = '';
  elVisorImg.removeAttribute('src');         /* libera memoria */
}

function mover(paso){
  if(VISIBLES.length === 0) return;
  indice = (indice + paso + VISIBLES.length) % VISIBLES.length;  /* da la vuelta */
  mostrarEnVisor();
}

function mostrarEnVisor(){
  const foto = VISIBLES[indice];
  if(!foto) return;

  elVisorImg.src = foto.archivo;
  elVisorImg.alt = foto.titulo || 'Fotografía';

  elVisorTit.textContent  = foto.titulo || '';
  elVisorNota.textContent = foto.nota   || '';
  elVisorCont.textContent = (indice + 1) + ' / ' + VISIBLES.length;

  elVisorDesc.setAttribute('href', foto.archivo);
  elVisorDesc.setAttribute('download', nombreDeDescarga(foto));

  /* Con una sola foto no tiene sentido mostrar flechas */
  const hayVarias = VISIBLES.length > 1;
  $('flechaIzq').hidden = !hayVarias;
  $('flechaDer').hidden = !hayVarias;
}

/* El nombre con el que se guarda la foto al descargarla.
   Orden de preferencia:
     1. el título escrito a mano ("Blanca y Baruch.jpg")
     2. el nombre original del archivo ("DSC02672.jpg"), que es el
        que el fotógrafo tiene en su catálogo: así el cliente puede
        cruzarlos
     3. el nombre interno, ya con su número de orden
   Se quitan los caracteres que Windows no acepta. */
function nombreDeDescarga(foto){
  const archivo  = String(foto.archivo || '');
  const extension = (archivo.match(/\.[a-z0-9]+$/i) || ['.jpg'])[0];
  const interno  = archivo.split('/').pop().replace(/\.[^.]+$/, '');
  const original = String(foto.original || '').replace(/\.[^.]+$/, '');
  const base = (foto.titulo || original || interno).trim().replace(/[\\/:*?"<>|]+/g, '-');
  return base + extension;
}
/* FIN BLOQUE 18 */


/* ============================================================
   BLOQUE 19: LOS DOS AVISOS
   ------------------------------------------------------------
   1) Aún no hay fotos: falta correr el script.
   2) Se abrió sin servidor: el navegador no deja leer archivos
      vecinos desde file://, así que hay que explicar cómo abrirla.
   ============================================================ */
function mostrarSinFotos(){
  elVacio.hidden = false;
  elCuenta.textContent = '';
  elVacio.innerHTML =
    '<p class="vacio-titulo">Todavía no hay fotografías</p>' +
    '<p class="vacio-texto">' +
      'Pon las fotos en la carpeta <b>originales</b> y ejecuta ' +
      '<b>preparar_fotos.py</b>. La página se arma sola.' +
    '</p>';
}

function mostrarAvisoDeServidor(){
  elVacio.hidden = false;
  elCuenta.textContent = '';
  elVacio.innerHTML =
    '<p class="vacio-titulo">Falta abrirlo con el servidor local</p>' +
    '<p class="vacio-texto">' +
      'El navegador no deja leer la lista de fotos cuando el archivo se abre ' +
      'haciendo doble clic. Abre la carpeta y ejecuta ' +
      '<b>preparar_fotos.py --servir</b>, o arrastra la carpeta a ' +
      '<b>netlify.com/drop</b> para publicarla.' +
    '</p>';
}

/* Arranca todo */
arrancar();
/* FIN BLOQUE 19 */
