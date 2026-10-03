# Space Shooter 2D — Laboratorio Pygame asistido por IAG

## Ficha técnica

| Campo | Detalle |
| --- | --- |
| **Juego** | Space Shooter 2D estilo arcade / pixel art |
| **Lenguaje** | Python 3.10+ |
| **Librería** | Pygame (`pip install pygame`) |
| **Asistente IAG** | Claude (Anthropic) |
| **Archivo principal** | `main.py` |
| **Resolución / FPS** | 960 x 540 a 60 FPS |
| **Persistencia** | Ninguna. No usa base de datos ni nube; todo el estado (vida, oleada, arma) vive en memoria durante la ejecución |

### Cómo ejecutar

```bash
pip install pygame
python main.py
```

### Controles

| Acción | Control |
| --- | --- |
| Mover la nave | `W A S D` o flechas |
| Disparar | Clic izquierdo del mouse (mantener para ráfaga) |
| Cambiar arma | `1` (1 cañón), `2` (2 cañones), `3` (3 cañones en abanico) |
| Iniciar / reiniciar | `ENTER` |

### Estados del juego

`inicio` → `jugando` → `gameover` o `victoria` → (`ENTER`) → `jugando`

### Características

- Pantalla de inicio con título pixelado en 3 capas de color y texto parpadeante.
- Nave pixel art generada desde una cuadrícula de texto (se dibuja la mitad y se espeja), con brillo pulsante, sombra y llama del propulsor.
- 8 tipos de aliens con sprite, vida y patrón de ataque propios: recto, abanico, teledirigido, doble, onda sinusoidal, ráfaga, radial y apuntado (doble daño).
- 3 oleadas con dificultad progresiva: los aliens tienen más vida y disparan más rápido en cada oleada.
- Vida del jugador con 5 corazones (llenos, medios y vacíos) e invulnerabilidad breve tras recibir un golpe.
- Sistema de partículas pixeladas (chispas, estelas, explosiones).
- Sonido retro generado por código: efectos, fanfarrias y música chiptune en bucle (sin archivos externos).

---

## Bitácora de Prompts (Prompt Log)

| Paso / Iteración | Prompt Exacto Utilizado (IAG) | Resultado / Ajustes Realizados |
| --- | --- | --- |
| **Paso 1: Selección del concepto** | "Necesito hacer un videojuego 2D en Python con Pygame para un laboratorio. Tiene que ser visual, dinámico y sin base de datos. ¿Qué idea me recomiendas?" | La IA propuso varias ideas (Pong, Snake, Flappy Bird, Space Invaders, esquivar meteoritos). Elegí **Space Shooter** porque permite mostrar jugador, enemigos, colisiones, vida y estados de juego. |
| **Paso 2: Interfaz principal (setup base)** | "Crea la base del juego en Pygame con ventana de 960x540, fondo negro, 60 FPS y manejo del evento QUIT. Quiero una pantalla de inicio con el título START THE GAME en letras pixeladas grandes con sombra de colores (amarillo, rojo y azul) y un texto PRESS ENTER que parpadee. Organiza el juego en estados: inicio, jugando, gameover y victoria." | Se generó la ventana, el bucle principal y los estados. El texto se agrandó con `transform.scale` sin suavizado para lograr el look pixelado. Ajuste manual: limitar `dt` a 0.05 s para que el juego no dé saltos si baja el rendimiento. |
| **Paso 3: Diseño de la nave principal** | "Diseña la nave del jugador en pixel art a partir de una cuadrícula de texto (solo la mitad izquierda y que se espeje), de color blanco con detalles cian, con brillo, sombra azul y llama de propulsor. Muévela con WASD y flechas, que no salga de la pantalla y que dispare proyectiles pixelados con chispas. Agrega 3 niveles de arma que se cambien con las teclas 1, 2 y 3." | La nave quedó simétrica y los 3 niveles de arma funcionan. Ajustes: se normalizó el movimiento diagonal (0.7071) para que no vaya más rápido, se limitó la zona vertical al 70% inferior de la pantalla y se dejó el arma nivel 2 como valor inicial. |
| **Paso 4: Diseño de los alienígenas** | "Crea 8 tipos de aliens distintos en pixel art, cada uno con su color, su cantidad de vida y su propio ataque: bola recta, abanico de 3, bola teledirigida, disparo doble, onda sinusoidal, ráfaga, abanico de 5 y orbe apuntado al jugador. Que entren desde arriba, se muevan en ondas, tengan barra de vida y parpadeen en blanco al recibir un golpe. Haz 3 oleadas, cada una con más vida y disparos más rápidos." | Se crearon los 8 tipos y las 3 oleadas. Ajustes: la colisión usa un rectángulo reducido (`inflate(-8, -8)`) para que sea más justa, la cadencia se multiplica por `0.88` en cada oleada y se limitó a 500 partículas para no bajar los FPS. El orbe apuntado hace doble daño. |
| **Paso 5: Diseño de la vida / salud** | "Agrega la vida del jugador con 5 corazones pixelados (lleno, medio y vacío) en la esquina superior derecha. Los poderes de los aliens deben quitar vida. Al recibir un golpe la nave parpadea unos segundos sin poder ser dañada, y cuando la vida llegue a 0 se muestra GAME OVER con opción de reiniciar con ENTER." | Corazones con medio estado (10 unidades de vida = 5 corazones). Ajustes: la hitbox de la nave se hizo más pequeña que el dibujo (30x60 px) y la invulnerabilidad se fijó en 1.4 s para que los golpes no se acumulen de inmediato. Se añadió también la pantalla YOU WIN al limpiar la tercera oleada. |
| **Paso 6: Disparo con el mouse** | "Modifica el juego para que el disparo sea con el clic izquierdo del mouse en lugar de la barra espaciadora. No cambies nada más, lo demás está perfecto." | Se reemplazó la tecla por `pygame.mouse.get_pressed()[0]`, así se dispara en ráfaga manteniendo el clic respetando la cadencia. Se actualizó el texto de ayuda del HUD a `CLICK FIRE`. |
| **Paso 7: Sonidos estilo 90s** | "Aumenta sonido al juego, algo para un juego de los años 90. No toques lo demás." | La IA generó los sonidos por código (ondas cuadradas, triángulo y ruido) sin archivos externos: disparo, impacto, explosión de alien, daño, fanfarrias de inicio, oleada, game over y victoria, más música chiptune en bucle. Ajustes: se bajó el volumen del disparo (0.12) y de la música (0.30), y se protegió la carga con `try/except` por si el equipo no tiene audio. |

---

## Depuración y manejo de la IAG

- **Rendimiento:** al disparar con varios cañones el número de partículas crecía sin control; se resolvió con un tope de 500 partículas.
- **Colisiones injustas:** el dibujo de la nave y de los aliens es más grande que su zona real de impacto; se usaron hitboxes reducidas.
- **Saltos de tiempo:** si el juego se congelaba un instante, los objetos "saltaban"; se limitó `dt` a 0.05 s.
- **Audio:** se evitó depender de numpy o de archivos `.wav` para que el proyecto corra solo con Pygame.

## Restricción técnica cumplida

El proyecto no utiliza bases de datos ni servicios en la nube. Todo el estado del juego se gestiona en memoria en tiempo de ejecución.
