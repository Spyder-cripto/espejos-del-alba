# COWORK → CODE · Espejos del Alba · Ideas de Chromatron (15-oct-2026)

Encargo de Fali (15-oct, 02:29): «Aprovecha todo lo que puedas [de Chromatron] para implementarlo en Espejos del Alba».

He separado dos cosas:

- **A. Lo que no cambia las reglas.** Ya está hecho y probado en un prototipo, en `canal/out/prototipo/index.html`. Te toca pasarlo a tus fuentes, si te parece bien.
- **B. Lo que sí cambia las reglas** (piezas nuevas). Es solo una propuesta. **Decide Fali**, y si dice que sí, va a REGLAS.md antes que a ningún motor.

No he tocado `main` ni la web publicada. El prototipo sale del `index.html` de `main` (c34d007), y solo cambian la **página** (HTML/CSS) y el **script del juego**. El motor (`window.Espejos`), el arte (`window.ARTE`) y `window.NIVELES` están idénticos byte a byte.

> **Aviso de carril (importante).** Para hacer el prototipo he leído el `index.html` construido, motor incluido. Eso **contamina mi independencia** para escribir el solucionador desde REGLAS.md sin mirar tu código. Propongo una salida: que el solucionador independiente lo escriba un subagente limpio que solo reciba REGLAS.md, y yo me quedo con la parte de auditar y comparar recuentos. Si preferís otra cosa, decidlo Fali o tú.

---

## A. Hecho en el prototipo (sin cambio de reglas)

| Idea de Chromatron | En Espejos del Alba |
|---|---|
| Ctrl+C / Ctrl+V copian y pegan soluciones como texto | **Código de tablero** `EA1.<nivel>.<fichas>` con Ctrl+C / Ctrl+V, botón «Compartir» y «Copiar solución» en la tarjeta de victoria |
| Compartir progreso y pistas con amigos | **Código de progreso** `EAP1.<nivel>[h<pistas>]…`, para pasar el progreso de un aparato a otro. Al cargarlo se funde con el que ya hay y se queda la marca con menos pistas |
| Tecla `R` reinicia el nivel | `R` reinicia, y además `Z` (o Ctrl+Z) **deshace**, el reinicio incluido. `1`–`9` eligen la pieza de la bandeja y `X` activa «Quitar» |
| El progreso se guarda (chroma.dat) | Además del progreso, **se guarda la partida a medias de cada nivel**, con las piezas que puso una pista |
| — | **Enlace con tablero**: `…/#EA1.n05.E3es.D4ds.E4es` abre ese nivel con esas piezas puestas. El `#n05` de siempre sigue valiendo |

### Formato del código de tablero (propuesta para REGLAS §10)

```
EA1.<id de nivel>.<casilla><pieza>.<casilla><pieza>…   (fichas en el orden de la forma canónica §9: por f y c)
casilla: columna A–J + fila 1–10, igual que los rótulos del tablero (C4 = f 3, c 2)
pieza:   es / eb  espejo «/» (sube hacia la derecha) / «\» (baja)
         ds / db  divisor «/» / «\»
         p        piedra
         f<color> filtro    (fR, fVA, fRVA…)  · color canónico R, V, A, RV, RA, VA, RVA
         c<color> cristal   (cA, cRV…)
```

- Es una biyección con la forma canónica `f,c,clase,ori` de §9 y no lleva barras invertidas, así que vale tal cual en un enlace.
- **Lo que se gana:** si los certificados de Cowork y los tuyos llevan también el código `EA1`, Fali puede abrir cualquier candidato o contraejemplo con un toque desde el móvil.
- Al leer, se aceptan minúsculas y espacios, y el color en cualquier orden (`fAR` → `fRA`). Se rechaza con un mensaje claro: nivel desconocido, casilla fuera, muro, pieza fija, casilla repetida, color que no vale (`fRR`) o más piezas de una clase de las que hay en el inventario.
- **Un tablero pegado o abierto por enlace no suma al progreso**, aunque sea la solución. Se ve encendido y avisa de que «no cuenta como resuelto por ti» hasta que se reinicia el nivel. Así nadie se apunta un nivel por pegar la solución de otro.

### Detalles de comportamiento que conviene conservar

- **Pistas.** Se cuentan las **pedidas** (`usadasPistas`), no las que siguen en el tablero. Deshacer una pista no la borra del marcador.
- **Nivel ya resuelto al volver.** Se ve encendido, sin la tarjeta de victoria y con el aviso «Este nivel ya lo tienes resuelto…».
- **Almacenamiento.** Nueva clave `espejos_del_alba_tableros_v1` con `{ <id>: { c: código, p: [casillas de pista], n: pistas pedidas, x: 1 si es prestado } }`. La clave de progreso `espejos_del_alba_v1` no cambia de formato. Todo va en try/catch: si el navegador no deja guardar, se juega igual.
- **Atajos.** No actúan mientras se escribe en un cuadro de texto ni con el diálogo «Compartir» abierto. `Esc` cierra los diálogos.
- **Pruebas.** El prototipo expone `window.ESPEJOS_UI` (codigoPos, leeCodigoPos, codigoProg, cargaProg, pegaPos, deshacer, reiniciar, abrir, estado) para pruebas automáticas.

### Prueba hecha (Chromium sin interfaz, `canal/out/prototipo/prueba.py`): 52 comprobaciones, 0 fallos

- **Soluciones de los 16 niveles.** Cada una (sacada del campo `s`) se pega como código `EA1`. El motor la da por buena, el código va y vuelve idéntico, no aparece la tarjeta de victoria y no suma progreso.
- **Códigos malos.** Hay 12 casos, cada uno con su mensaje.
- **n01 jugado con clics.** Colocar, girar y deshacer funcionan. Al resolverlo sale la victoria y el progreso se guarda con 0 pistas. Después, `R` lo vacía y `Z` lo devuelve como estaba.
- **Partida guardada.** La partida a medias se recupera al recargar. Un nivel resuelto aparece encendido y con ✔ en la lista.
- **Pistas.** Deshacer una pista quita la pieza, pero la pista sigue contando.
- **Teclas.** `3` elige la tercera pieza de la bandeja y `X` activa «Quitar».
- **Progreso.** Se exporta, se carga en otro contexto limpio, se funde con el existente (se queda la marca con menos pistas) y se ignoran los ids desconocidos.
- **Enlaces y portapapeles.** Un enlace `#EA1…` abre su nivel con su tablero. Ctrl+C y Ctrl+V usan el portapapeles real, y el botón «Copiar código» funciona.
- **Móvil (390 px).** No hay scroll horizontal ni errores de consola.

### Qué te pido, Code

1. Revisa el diff del script del juego frente a `main`. Es autocontenido y no toca el motor.
2. Si te parece bien, pásalo a tu fuente del juego y construye como siempre.
3. Avísame por el canal y vuelvo a pasar `prueba.py` contra tu construcción.

**No se publica sin el «sí» de Fali.**

---

## B. Propuesta de mecánicas nuevas (cambian REGLAS: decide Fali)

Los nombres de nivel de Chromatron 2–4 dejan ver sus mecánicas: *Teleporter Maze*, *Prismagic*, *Duelling Prisms*, *Doppler Mania*, *Conduit Maze Practice*, *Interference Patterns*. No copio su comportamiento exacto (no lo he verificado). Abajo van **definiciones propias**, cerradas para que tu motor y el solucionador puedan implementarlas igual. Las ordeno por valor para el juego frente a coste.

1. **Pieza fija girable** (losa con un pivote). No se mueve de su casilla, pero el jugador la puede girar. En el JSON sería `"fijas": [{ "tipo": "espejo", "ori": "/", "girable": true }]`. El coste es mínimo: el solucionador suma 2 opciones por pieza. Para la dificultad es muy rica, porque el jugador ve la pieza y tiene que adivinar su papel.
2. **Prisma** (pieza nueva, sin orientación). La luz que entra se descompone: el **rojo gira a la izquierda**, el **verde sigue recto** y el **azul gira a la derecha**, siempre respecto a su dirección de llegada. Con nuestros tres colores es la pieza estrella. Exige pensar en «de qué lado entra el blanco».
3. **Portales emparejados** (fijos, de par en par). Lo que entra por uno sale por su pareja en la misma dirección y con el mismo color. Con dos portales que se miran se forman bucles, pero el modelo «solo se propaga lo nuevo» (§4) ya los cierra.
4. **Conducto** (fijo o colocable, orientación `-` o `|`). Deja pasar la luz solo en su eje y corta la perpendicular.
5. **Rueda de color** (Doppler). Cambia cada color al siguiente: R→V→A→R. Así, RV→VA, y el blanco sigue blanco.
6. **Ojo dormido** (diana negativa). No puede recibir **ninguna** luz. Es barato de implementar y abre niveles de «esquivar».

Cualquiera que se apruebe va a **REGLAS v4**. Después lo implementan los dos motores, y un nivel solo vale si los recuentos coinciden, como siempre.

---

## C. Ideas de diseño de niveles (para Fali: nombres y estilo son suyos)

- **Sagas con número**, como hace Chromatron con *Blue vs. Green II–V* o *Color Challenge I–II*. Por ejemplo, «Duelo al alba I–V» (rojo contra azul, cada uno por su lado del templo) o «La prueba del color I–III». Dan sensación de progreso y dejan subir la dificultad de una mecánica de forma escalonada.
- **Nombres con guiño**, que son la mitad del encanto de Chromatron. Son candidatas mías, para que Fali elija o descarte: «Ni contigo ni sin ti», «El que parte y reparte», «Espejito, espejito», «A la tercera va la vencida», «Más vale maña», «El camino largo», «Arco iris de bolsillo», «Todo es blanco», «Dos son compañía», «Sin vuelta atrás».
- **Gran final mural.** Un tablero 10×10 con emisores en todo el borde y una docena de dianas, como la última captura de la página de Chromatron. Sería el cierre del escalón Gran Maestro.
- **Tableros compactos.** Electron Dance señala como defecto de Chromatron la rejilla grande y fija, frente al tablero ajustado de Archaica. Los nuestros (de 5×5 a 8×8) van en la buena dirección y conviene mantenerlos así.

---

Ficheros de esta entrega (rama `cowork`):

- `canal/out/COWORK_2026-10-15_ESPEJOS_chromatron.md` (este)
- `canal/out/prototipo/index.html` (el juego con lo de la sección A)
- `canal/out/prototipo/prueba.py` (pruebas en Chromium sin interfaz; `python3 prueba.py` desde esa carpeta)
- `canal/out/_INDICE_COWORK.md`

Copia en `_handoff`: **pendiente**, porque el PC de Fali no estaba conectado a las 02:30. La subo en cuanto se pueda.
