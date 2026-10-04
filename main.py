import pygame
import sys
import math
import random
import array

# ---------- CONFIGURACIÓN ----------
ANCHO, ALTO = 960, 540
FPS = 60
NEGRO = (0, 0, 0)
AMARILLO = (255, 230, 40)
ROJO = (230, 40, 40)
AZUL = (40, 60, 230)
BLANCO = (255, 255, 255)

PALETA_CHISPA = ((255, 255, 255), (0, 230, 255), (30, 40, 160))
PALETA_FUEGO = ((255, 230, 40), (255, 120, 0), (230, 40, 40))

VIDA_MAX = 10          # 10 medios corazones = 5 corazones
OLEADAS_TOTALES = 3    # al limpiar la última, ganas

SR = 22050
pygame.mixer.pre_init(SR, -16, 1, 512)
pygame.init()
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Space Shooter 2D")
reloj = pygame.time.Clock()


# ---------- SONIDO RETRO (generado por código, sin archivos) ----------
SONIDOS = {}
MUSICA = None
CANALES = 1


def _a_sonido(buf):
    """Convierte las muestras mono al formato del mixer (mono o estéreo)."""
    if CANALES == 2:
        est = array.array("h")
        for s in buf:
            est.append(s)
            est.append(s)
        buf = est
    return pygame.mixer.Sound(buffer=buf)


def _onda(tipo, fase):
    f = fase % 1.0
    if tipo == "cuadrada":
        return 1.0 if f < 0.5 else -1.0
    if tipo == "pulso":
        return 1.0 if f < 0.25 else -1.0
    if tipo == "triangulo":
        return 4 * abs(f - 0.5) - 1
    if tipo == "sierra":
        return 2 * f - 1
    return random.uniform(-1, 1)     # ruido


def sintetizar(dur, f0, f1, tipo="cuadrada", vol=0.3, curva=1.0):
    """Un 'bip' que va de la frecuencia f0 a f1 y se apaga poco a poco."""
    n = int(SR * dur)
    buf = array.array("h")
    fase = 0.0
    for i in range(n):
        k = i / n
        fase += (f0 + (f1 - f0) * k) / SR
        env = (1 - k) ** curva
        buf.append(int(_onda(tipo, fase) * env * vol * 32767))
    return _a_sonido(buf)


def sintetizar_secuencia(notas, dur_nota, tipo="cuadrada", vol=0.3):
    """Varias notas seguidas (para fanfarrias de inicio, victoria, etc.)."""
    buf = array.array("h")
    for f in notas:
        n = int(SR * dur_nota)
        for i in range(n):
            k = i / n
            env = (1 - k * 0.6) if k < 0.9 else (1 - k) * 4
            buf.append(int(_onda(tipo, f * i / SR) * env * vol * 32767))
    return _a_sonido(buf)


def construir_musica():
    """Melodía corta tipo chiptune (lead + bajo) que se repite en bucle."""
    lead = [440, 523, 659, 523, 440, 523, 698, 523,
            392, 494, 587, 494, 330, 392, 494, 392]
    bajo = [110, 87.3, 98, 82.4]
    paso = 0.16
    n = int(SR * paso)
    buf = array.array("h")
    for idx, fl in enumerate(lead):
        fb = bajo[idx // 4]
        for i in range(n):
            k = i / n
            t = i / SR
            v_lead = _onda("pulso", fl * t) * (1 - k) ** 0.6 * 0.5
            v_bajo = _onda("triangulo", fb * t) * (1 - k * 0.4) * 0.8
            fade = min(1.0, (n - i) / 100)
            buf.append(int((v_lead + v_bajo) * 0.5 * fade * 32767))
    return _a_sonido(buf)


def iniciar_audio():
    global MUSICA, CANALES
    try:
        CANALES = pygame.mixer.get_init()[2]
        SONIDOS["disparo"] = sintetizar(0.11, 1500, 300, "cuadrada", 0.12, 1.5)
        SONIDOS["impacto"] = sintetizar(0.05, 900, 500, "ruido", 0.12, 1.0)
        SONIDOS["muerte_alien"] = sintetizar(0.45, 400, 40, "ruido", 0.35, 1.3)
        SONIDOS["dano"] = sintetizar(0.35, 260, 60, "sierra", 0.30, 1.0)
        SONIDOS["oleada"] = sintetizar_secuencia([330, 392, 523, 659], 0.09, "cuadrada", 0.22)
        SONIDOS["inicio"] = sintetizar_secuencia([262, 330, 392, 523, 659, 784], 0.07, "pulso", 0.22)
        SONIDOS["gameover"] = sintetizar_secuencia([523, 440, 349, 262, 196, 131], 0.17, "sierra", 0.25)
        SONIDOS["victoria"] = sintetizar_secuencia([392, 392, 392, 523, 659, 784, 1046], 0.12, "pulso", 0.22)
        MUSICA = construir_musica()
        MUSICA.set_volume(0.30)
    except Exception:
        SONIDOS.clear()
        MUSICA = None


def sonar(nombre):
    s = SONIDOS.get(nombre)
    if s:
        s.play()


def musica_on():
    if MUSICA:
        MUSICA.stop()
        MUSICA.play(loops=-1)


def musica_off():
    if MUSICA:
        MUSICA.stop()


iniciar_audio()


# ---------- TEXTO PIXELADO ----------
def texto_pixelado(texto, escala, color):
    fuente = pygame.font.Font(None, 16)
    base = fuente.render(texto, False, color)
    ancho, alto = base.get_size()
    return pygame.transform.scale(base, (ancho * escala, alto * escala))


def dibujar_titulo(texto, centro_x, y, escala):
    azul = texto_pixelado(texto, escala, AZUL)
    rojo = texto_pixelado(texto, escala, ROJO)
    amarillo = texto_pixelado(texto, escala, AMARILLO)
    x = centro_x - amarillo.get_width() // 2
    pantalla.blit(azul, (x + escala * 2, y + escala * 2))
    pantalla.blit(rojo, (x + escala, y + escala))
    pantalla.blit(amarillo, (x, y))


def pantalla_con_titulo(titulo, tiempo, escala=8, y=180):
    pantalla.fill(NEGRO)
    dibujar_titulo(titulo, ANCHO // 2, y, escala)
    if (tiempo // 500) % 2 == 0:
        sub = texto_pixelado("PRESS ENTER", 3, BLANCO)
        pantalla.blit(sub, (ANCHO // 2 - sub.get_width() // 2, 360))


# ---------- SPRITE DEL DISPARO ----------
BALA_GRID = [
    "..C..",
    ".CWC.",
    ".CWC.",
    "CCWCC",
    "CYWYC",
    ".YWY.",
    ".BYB.",
    "..B..",
]
COLORES_BALA = {
    "W": (255, 255, 255),
    "Y": (255, 240, 120),
    "C": (0, 230, 255),
    "B": (30, 70, 230),
}
ESCALA_BALA = 4


def construir_bala():
    e = ESCALA_BALA
    ancho, alto = len(BALA_GRID[0]), len(BALA_GRID)
    img = pygame.Surface((ancho * e, alto * e), pygame.SRCALPHA)
    for j, fila in enumerate(BALA_GRID):
        for i, letra in enumerate(fila):
            if letra in COLORES_BALA:
                pygame.draw.rect(img, COLORES_BALA[letra], (i * e, j * e, e, e))
    mascara = pygame.mask.from_surface(img)
    sombra = mascara.to_surface(setcolor=(30, 40, 160, 255), unsetcolor=(0, 0, 0, 0))
    brillo = mascara.to_surface(setcolor=(0, 220, 255, 255), unsetcolor=(0, 0, 0, 0))
    brillo.set_alpha(90)
    return img, sombra, brillo


BALA_IMG, BALA_SOMBRA, BALA_BRILLO = construir_bala()


# ---------- PARTÍCULAS PIXELADAS ----------
class Particula:
    def __init__(self, x, y, vx, vy, vida, tam, paleta):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.vida = self.vida_max = vida
        self.tam = tam
        self.paleta = paleta

    def actualizar(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vida -= dt

    def dibujar(self):
        t = self.vida / self.vida_max
        if t > 0.66:
            color, tam = self.paleta[0], self.tam
        elif t > 0.33:
            color, tam = self.paleta[1], self.tam
        else:
            color, tam = self.paleta[2], max(2, self.tam // 2)
        px = int(self.x) // 2 * 2
        py = int(self.y) // 2 * 2
        pygame.draw.rect(pantalla, color, (px, py, tam, tam))


class Destello:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.vida = self.vida_max = 0.07

    def actualizar(self, dt):
        self.vida -= dt

    def dibujar(self):
        e = 4
        k = 2 if self.vida > self.vida_max / 2 else 1
        x, y = int(self.x), int(self.y)
        pygame.draw.rect(pantalla, (0, 230, 255), (x - e * k, y - e // 2, e * k * 2, e))
        pygame.draw.rect(pantalla, (0, 230, 255), (x - e // 2, y - e * k, e, e * k * 2))
        pygame.draw.rect(pantalla, BLANCO, (x - e, y - e, e * 2, e * 2))


particulas = []
destellos = []
balas_enemigas = []
MAX_PARTICULAS = 500


def crear_particula(*args):
    if len(particulas) < MAX_PARTICULAS:
        particulas.append(Particula(*args))


def chispas_de_disparo(x, y):
    destellos.append(Destello(x, y))
    for _ in range(7):
        crear_particula(x, y, random.uniform(-220, 220), random.uniform(-260, -40),
                        random.uniform(0.12, 0.28), random.choice((4, 6)), PALETA_CHISPA)


def explosion(x, y, color, cantidad=30):
    """Explosión de píxeles (muerte de alien o de la nave)."""
    for _ in range(cantidad):
        ang = random.uniform(0, math.tau)
        vel = random.uniform(80, 330)
        paleta = PALETA_FUEGO if random.random() < 0.4 else (BLANCO, color, (40, 30, 100))
        crear_particula(x, y, math.cos(ang) * vel, math.sin(ang) * vel,
                        random.uniform(0.3, 0.7), random.choice((4, 6, 8)), paleta)


# ---------- DISPARO DEL JUGADOR ----------
class Disparo:
    VELOCIDAD = 900

    def __init__(self, x, y, vx=0):
        self.x, self.y = float(x), float(y)
        self.vx = vx
        self.vivo = True
        self.rect = BALA_IMG.get_rect(center=(x, y))
        self.reloj_estela = 0.0

    def actualizar(self, dt):
        self.x += self.vx * dt
        self.y -= self.VELOCIDAD * dt
        self.rect.center = (round(self.x), round(self.y))

        self.reloj_estela += dt
        while self.reloj_estela >= 0.015:
            self.reloj_estela -= 0.015
            crear_particula(self.x + random.randint(-6, 6), self.rect.bottom,
                            random.uniform(-30, 30), random.uniform(60, 160),
                            random.uniform(0.15, 0.3), random.choice((4, 6)),
                            PALETA_CHISPA if random.random() < 0.7 else PALETA_FUEGO)

        if self.rect.bottom < 0 or self.rect.right < 0 or self.rect.left > ANCHO:
            self.vivo = False

    def dibujar(self):
        e = ESCALA_BALA
        for dx, dy in ((-e, 0), (e, 0), (0, -e), (0, e)):
            pantalla.blit(BALA_BRILLO, (self.rect.x + dx, self.rect.y + dy))
        pantalla.blit(BALA_SOMBRA, (self.rect.x + e // 2, self.rect.y + e // 2))
        pantalla.blit(BALA_IMG, self.rect)


# ---------- NAVE DEL JUGADOR ----------
NAVE_MITAD = [
    "........W",
    "........W",
    ".......GW",
    ".......WW",
    "......GWC",
    "W.....GWW",
    "WG...GWCW",
    "WGG..WWCW",
    "WWGGGWWWW",
    "DWWWWWGCW",
    ".DWWWWWWW",
    "..DGWWDWW",
    "...DWWDGW",
    "....DWWGW",
    ".....DGWW",
    "......DWD",
    "......D.D",
]
COLORES_NAVE = {
    "W": (255, 255, 255),
    "G": (190, 190, 200),
    "D": (110, 110, 130),
    "C": (0, 230, 255),
}
ESCALA_NAVE = 6


def construir_sprite(mitad, colores, escala):
    """Espeja la mitad izquierda y la convierte en imagen."""
    filas = [f + f[-2::-1] for f in mitad]
    ancho, alto = len(filas[0]), len(filas)
    img = pygame.Surface((ancho * escala, alto * escala), pygame.SRCALPHA)
    for j, fila in enumerate(filas):
        for i, letra in enumerate(fila):
            if letra in colores:
                pygame.draw.rect(img, colores[letra], (i * escala, j * escala, escala, escala))
    return img


class Nave:
    VELOCIDAD = 420
    CADENCIA = 0.14

    def __init__(self, x, y):
        self.imagen = construir_sprite(NAVE_MITAD, COLORES_NAVE, ESCALA_NAVE)
        self.rect = self.imagen.get_rect(midbottom=(x, y))
        self.silueta = pygame.mask.from_surface(self.imagen)
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)
        self.nivel_arma = 2
        self.espera = 0.0
        self.retroceso = 0.0
        self.disparos = []
        self.vida = VIDA_MAX
        self.invul = 0.0          # segundos de invulnerabilidad tras un golpe

    @property
    def hitbox(self):
        """Zona real donde te pueden golpear (más pequeña que el dibujo)."""
        h = pygame.Rect(0, 0, 30, 60)
        h.center = self.rect.center
        return h

    def recibir_dano(self, dano):
        if self.invul > 0 or self.vida <= 0:
            return
        self.vida = max(0, self.vida - dano)
        self.invul = 1.4
        sonar("dano")
        explosion(self.rect.centerx, self.rect.centery, (255, 60, 60), 14)

    def mover(self, teclas, dt):
        dx = (teclas[pygame.K_d] or teclas[pygame.K_RIGHT]) - \
             (teclas[pygame.K_a] or teclas[pygame.K_LEFT])
        dy = (teclas[pygame.K_s] or teclas[pygame.K_DOWN]) - \
             (teclas[pygame.K_w] or teclas[pygame.K_UP])
        if dx and dy:
            dx *= 0.7071
            dy *= 0.7071
        self.x += dx * self.VELOCIDAD * dt
        self.y += dy * self.VELOCIDAD * dt
        limite_arriba = ALTO * 0.30
        limite_abajo = ALTO - 8 * ESCALA_NAVE // 2 - 6
        self.x = max(0, min(self.x, ANCHO - self.rect.width))
        self.y = max(limite_arriba, min(self.y, limite_abajo - self.rect.height))

    def cañones(self):
        e = ESCALA_NAVE
        centro = (self.rect.x + 8 * e + e // 2, self.rect.y)
        ala_izq = (self.rect.x + 1 * e + e // 2, self.rect.y + 5 * e)
        ala_der = (self.rect.x + 15 * e + e // 2, self.rect.y + 5 * e)
        if self.nivel_arma == 1:
            return [(*centro, 0)]
        if self.nivel_arma == 2:
            return [(*ala_izq, 0), (*ala_der, 0)]
        return [(*centro, 0), (*ala_izq, -150), (*ala_der, 150)]

    def disparar(self):
        for x, y, vx in self.cañones():
            self.disparos.append(Disparo(x, y, vx))
            chispas_de_disparo(x, y)
        sonar("disparo")
        self.espera = self.CADENCIA
        self.retroceso = 8

    def actualizar(self, teclas, dt):
        self.mover(teclas, dt)
        self.espera -= dt
        self.invul = max(0, self.invul - dt)
        # Disparo con clic izquierdo del mouse
        if pygame.mouse.get_pressed()[0] and self.espera <= 0:
            self.disparar()
        self.retroceso = max(0, self.retroceso - 60 * dt)
        self.rect.x = round(self.x)
        self.rect.y = round(self.y + self.retroceso)

        for d in self.disparos:
            d.actualizar(dt)
        self.disparos = [d for d in self.disparos if d.vivo]

    def dibujar_efectos(self, tiempo):
        e = ESCALA_NAVE
        sombra = self.silueta.to_surface(setcolor=(30, 40, 160, 255), unsetcolor=(0, 0, 0, 0))
        pantalla.blit(sombra, (self.rect.x + e, self.rect.y + e))
        pulso = 70 + int(40 * math.sin(tiempo / 250))
        brillo = self.silueta.to_surface(setcolor=(0, 220, 255, 255), unsetcolor=(0, 0, 0, 0))
        brillo.set_alpha(pulso)
        for dx, dy in [(-e, 0), (e, 0), (0, -e), (0, e)]:
            pantalla.blit(brillo, (self.rect.x + dx, self.rect.y + dy))
        base_y = self.rect.bottom
        for col in (6, 8, 10):
            cx = self.rect.x + col * e
            largo = random.choice((2, 3, 4)) * e
            pygame.draw.rect(pantalla, (255, 120, 0), (cx, base_y, e, largo))
            pygame.draw.rect(pantalla, (255, 230, 40), (cx, base_y, e, largo // 2))

    def dibujar(self, tiempo):
        # Parpadea mientras es invulnerable
        if self.invul > 0 and int(self.invul * 14) % 2:
            return
        self.dibujar_efectos(tiempo)
        pantalla.blit(self.imagen, self.rect)


# ---------- ALIENS (8 TIPOS) ----------
# Mitad izquierda de cada alien (la última columna es el centro).
# W = ojo blanco, K = pupila; las demás letras cambian de color según el alien.
ESCALA_ALIEN = 4
COMUN = {"W": (255, 255, 255), "K": (20, 20, 50)}

TIPOS = [
    {   # 1. Verde de un ojo -> bola recta
        "grid": ["....MM", "...MMM", "..MWWW", "MMMWWK", "M.MWWW", "..MMMM", "..MDMD", "...D.D"],
        "colores": {"M": (120, 220, 40), "D": (70, 150, 20)},
        "vida": 10, "ataque": "recto", "bala": (150, 255, 60), "cadencia": (1.6, 3.0),
    },
    {   # 2. Morado de dos ojos -> abanico de 3
        "grid": ["...MMM", "..MMMM", ".MMMMM", "AMWKMM", "AAWWMM", ".MMMMM", "..MMMM", "..A.A."],
        "colores": {"M": (200, 50, 200), "A": (130, 40, 160)},
        "vida": 10, "ataque": "abanico", "bala": (255, 90, 255), "cadencia": (2.2, 3.6),
    },
    {   # 3. Turquesa con cuernos -> bola teledirigida
        "grid": ["H....M", "HMMMMM", ".MMMWK", ".MMMMM", ".MMMWK", "..MMMM", "..MMWK",
                 "...MMM", "....MM", ".....M", ".....M"],
        "colores": {"M": (30, 200, 180), "H": (255, 150, 30)},
        "vida": 16, "ataque": "teledirigida", "bala": (60, 255, 220), "cadencia": (3.0, 4.5),
    },
    {   # 4. Rosa cangrejo -> disparo doble
        "grid": ["A.....", "AA....", ".MMMMM", ".MWMMW", ".MKMMK", "MMMMMM", ".MDMDM",
                 "..D.D.", ".D...D"],
        "colores": {"M": (235, 50, 120), "A": (255, 110, 160), "D": (170, 30, 90)},
        "vida": 14, "ataque": "doble", "bala": (255, 90, 150), "cadencia": (1.8, 3.0),
    },
    {   # 5. Azul medusa -> onda sinusoidal
        "grid": ["...MMM", "..MMMM", ".MLMMM", ".MMWWK", ".MMWWW", ".MMMMM", "..MMMM",
                 "..A.A.", ".A.A.A", "..A.A."],
        "colores": {"M": (70, 170, 255), "L": (170, 220, 255), "A": (60, 130, 230)},
        "vida": 10, "ataque": "onda", "bala": (120, 210, 255), "cadencia": (2.0, 3.4),
    },
    {   # 6. Amarillo calamar -> ráfaga de 3
        "grid": ["....MM", "...MMM", "...MWK", "...MMM", "...MWK", "...MMM", "...MWK",
                 "..MMMM", "..DMDM", "..A.A.", ".A.A.A", "..A.A."],
        "colores": {"M": (255, 200, 30), "A": (255, 140, 20), "D": (220, 150, 20)},
        "vida": 20, "ataque": "rafaga", "bala": (255, 240, 90), "cadencia": (2.4, 3.8),
    },
    {   # 7. Rosa con alas -> abanico amplio de 5
        "grid": ["...MMM", "..MMMM", ".BMMMM", "BBBMMM", "BBBMWK", ".BBMMM", "..MMMM",
                 "..T.T.", ".T.T.T", "..T.T."],
        "colores": {"M": (235, 50, 140), "B": (120, 220, 255), "T": (80, 170, 240)},
        "vida": 14, "ataque": "radial", "bala": (255, 130, 220), "cadencia": (2.8, 4.2),
    },
    {   # 8. Verde esfera -> orbe apuntado (¡hace doble daño!)
        "grid": ["...MMM", "..MMMM", "RMMMMM", "RRMWWK", "RMMMMM", "..MMMM", "..MDMD",
                 "..D.D.", ".D.D.D"],
        "colores": {"M": (90, 200, 60), "R": (170, 60, 200), "D": (50, 140, 40)},
        "vida": 18, "ataque": "apuntada", "bala": (200, 90, 255), "cadencia": (3.0, 4.6),
    },
]


def preparar_aliens():
    for t in TIPOS:
        colores = dict(COMUN)
        colores.update(t["colores"])
        img = construir_sprite(t["grid"], colores, ESCALA_ALIEN)
        mascara = pygame.mask.from_surface(img)
        t["img"] = img
        t["sombra"] = mascara.to_surface(setcolor=(30, 40, 160, 255), unsetcolor=(0, 0, 0, 0))
        t["blanco"] = mascara.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))


preparar_aliens()


class BalaEnemiga:
    """Poder que lanzan los aliens."""

    def __init__(self, x, y, vx, vy, color, modo="recto", dano=1):
        self.x, self.y = float(x), float(y)
        self.x_centro = float(x)
        self.vx, self.vy = vx, vy
        self.color = color
        self.oscuro = tuple(c // 3 for c in color)
        self.modo = modo
        self.dano = dano
        self.t = 0.0
        self.vida = 5.0
        self.vivo = True
        self.reloj_estela = 0.0

    @property
    def rect(self):
        return pygame.Rect(int(self.x) - 6, int(self.y) - 6, 12, 12)

    def actualizar(self, dt, nave):
        self.t += dt
        if self.modo == "teledirigida":
            obj = nave.rect.center
            ang_obj = math.atan2(obj[1] - self.y, obj[0] - self.x)
            vel = math.hypot(self.vx, self.vy)
            ang = math.atan2(self.vy, self.vx)
            dif = (ang_obj - ang + math.pi) % math.tau - math.pi
            ang += max(-1.8 * dt, min(1.8 * dt, dif))
            self.vx, self.vy = math.cos(ang) * vel, math.sin(ang) * vel
            self.vida -= dt
            if self.vida <= 0:
                self.vivo = False
        self.x_centro += self.vx * dt
        self.y += self.vy * dt
        self.x = self.x_centro + (math.sin(self.t * 7) * 38 if self.modo == "onda" else 0)

        self.reloj_estela += dt
        if self.reloj_estela >= 0.04:
            self.reloj_estela = 0
            crear_particula(self.x, self.y, random.uniform(-20, 20), random.uniform(-20, 20),
                            0.25, 4, (self.color, self.color, self.oscuro))

        if self.y > ALTO + 20 or self.y < -40 or self.x < -40 or self.x > ANCHO + 40:
            self.vivo = False

    def _orbe(self, x, y, r, color):
        pygame.draw.rect(pantalla, color, (x - r, y - r + 4, 2 * r, 2 * r - 8))
        pygame.draw.rect(pantalla, color, (x - r + 4, y - r, 2 * r - 8, 2 * r))

    def dibujar(self):
        x = int(self.x) // 2 * 2
        y = int(self.y) // 2 * 2
        self._orbe(x, y, 9, self.oscuro)
        self._orbe(x, y, 7, self.color)
        pygame.draw.rect(pantalla, BLANCO, (x - 3, y - 3, 6, 6))


class Alien:
    def __init__(self, tipo, x, y, vida_extra, fase):
        self.datos = TIPOS[tipo]
        self.img = self.datos["img"]
        self.rect = self.img.get_rect()
        self.vida = self.vida_max = self.datos["vida"] + vida_extra
        self.x_base, self.y_base = x, y
        self.y_act = y - random.randint(300, 420)    # entra desde arriba
        self.t = 0.0
        self.fase = fase
        self.amp = 40
        self.vel = random.uniform(0.9, 1.4)
        self.espera = random.uniform(1.5, 3.5)
        self.rafaga = 0
        self.t_rafaga = 0.0
        self.flash = 0.0
        self.vivo = True
        self.rect.center = (round(x), round(self.y_act))

    @property
    def entrado(self):
        return self.y_act >= self.y_base

    def recibir_golpe(self, dano=1):
        self.vida -= dano
        self.flash = 0.07
        if self.vida <= 0:
            self.vivo = False
            sonar("muerte_alien")
            explosion(self.rect.centerx, self.rect.centery, self.datos["bala"], 34)
        else:
            sonar("impacto")

    def disparar(self, nave, balas):
        cx, cy = self.rect.centerx, self.rect.bottom
        a, col = self.datos["ataque"], self.datos["bala"]
        if a == "recto":
            balas.append(BalaEnemiga(cx, cy, 0, 260, col))
        elif a == "abanico":
            for vx in (-130, 0, 130):
                balas.append(BalaEnemiga(cx, cy, vx, 240, col))
        elif a == "teledirigida":
            balas.append(BalaEnemiga(cx, cy, 0, 150, col, "teledirigida"))
        elif a == "doble":
            for off in (-14, 14):
                balas.append(BalaEnemiga(cx + off, cy, 0, 300, col))
        elif a == "onda":
            balas.append(BalaEnemiga(cx, cy, 0, 200, col, "onda"))
        elif a == "rafaga":
            self.rafaga, self.t_rafaga = 3, 0.0
        elif a == "radial":
            for ang in (-60, -30, 0, 30, 60):
                rad = math.radians(ang + 90)
                balas.append(BalaEnemiga(cx, cy, math.cos(rad) * 220, math.sin(rad) * 220, col))
        elif a == "apuntada":
            dx, dy = nave.rect.centerx - cx, nave.rect.centery - cy
            d = math.hypot(dx, dy) or 1
            balas.append(BalaEnemiga(cx, cy, dx / d * 330, dy / d * 330, col, dano=2))

    def actualizar(self, dt, nave, balas, mult):
        self.t += dt
        if self.y_act < self.y_base:
            self.y_act = min(self.y_base, self.y_act + 220 * dt)
        x = self.x_base + math.sin(self.t * self.vel + self.fase) * self.amp
        y = self.y_act + (math.sin(self.t * 1.8 + self.fase) * 8 if self.entrado else 0)
        self.rect.center = (round(x), round(y))
        self.flash = max(0, self.flash - dt)

        if not self.entrado:
            return
        self.espera -= dt
        if self.espera <= 0:
            self.disparar(nave, balas)
            self.espera = random.uniform(*self.datos["cadencia"]) * mult
        if self.rafaga > 0:
            self.t_rafaga -= dt
            if self.t_rafaga <= 0:
                balas.append(BalaEnemiga(self.rect.centerx, self.rect.bottom, 0, 360,
                                         self.datos["bala"]))
                self.rafaga -= 1
                self.t_rafaga = 0.12

    def dibujar(self):
        e = ESCALA_ALIEN
        pantalla.blit(self.datos["sombra"], (self.rect.x + e, self.rect.y + e))
        pantalla.blit(self.datos["blanco"] if self.flash > 0 else self.img, self.rect)
        # Barra de vida del alien
        w, x = self.rect.width, self.rect.x
        y = max(2, self.rect.y - 14)
        ratio = max(0, self.vida / self.vida_max)
        col = (60, 230, 80) if ratio > 0.5 else (255, 220, 40) if ratio > 0.25 else (240, 50, 50)
        pygame.draw.rect(pantalla, (20, 20, 40), (x - 2, y - 2, w + 4, 10))
        pygame.draw.rect(pantalla, (70, 70, 90), (x, y, w, 6))
        pygame.draw.rect(pantalla, col, (x, y, int(w * ratio), 6))


def crear_oleada(n):
    """8 aliens (uno de cada tipo). Cada oleada tienen más vida."""
    lista = []
    for i in range(8):
        x = 100 + i * (ANCHO - 200) / 7
        y = 85 + (i % 2) * 65
        lista.append(Alien(i, x, y, (n - 1) * 4, i * 0.7))
    return lista


# ---------- CORAZONES (VIDA DEL JUGADOR) ----------
HEART = [
    ".XX.XX.",
    "XLXXXXX",
    "XLXXXXX",
    "XXXXXXX",
    ".XXXXX.",
    "..XXX..",
    "...X...",
]
ESC_CORAZON = 2


def construir_corazon(estado):
    e = ESC_CORAZON
    img = pygame.Surface((7 * e, 7 * e), pygame.SRCALPHA)
    for j, fila in enumerate(HEART):
        for i, l in enumerate(fila):
            if l == ".":
                continue
            rojo = estado == "lleno" or (estado == "medio" and i <= 3)
            if rojo:
                col = (255, 150, 160) if l == "L" else (225, 0, 0)
            else:
                col = (130, 130, 130) if l == "L" else (95, 95, 95)
            pygame.draw.rect(img, col, (i * e, j * e, e, e))
    return img


CORAZONES = {k: construir_corazon(k) for k in ("lleno", "medio", "vacio")}


def dibujar_vida(nave):
    x0 = ANCHO - 5 * 18 - 8
    for i in range(5):
        u = nave.vida - i * 2
        estado = "lleno" if u >= 2 else "medio" if u == 1 else "vacio"
        pantalla.blit(CORAZONES[estado], (x0 + i * 18, 8))


# ---------- HUD ----------
def dibujar_hud(nave, oleada, aliens):
    pantalla.blit(texto_pixelado(f"WEAPON LV {nave.nivel_arma}", 2, AMARILLO), (16, 14))
    pantalla.blit(texto_pixelado(f"WAVE {oleada}/{OLEADAS_TOTALES}   ALIENS {len(aliens)}",
                                 2, (180, 180, 220)), (16, 36))
    pantalla.blit(texto_pixelado("WASD MOVE   CLICK FIRE   1-2-3 WEAPON", 2, (120, 120, 150)),
                  (16, ALTO - 30))
    dibujar_vida(nave)


# ---------- PARTIDA ----------
def nuevo_juego():
    particulas.clear()
    destellos.clear()
    balas_enemigas.clear()
    nave = Nave(ANCHO // 2, ALTO - 90)
    return nave, crear_oleada(1), 1, 2.2


def main():
    pygame.display.set_icon(pygame.transform.scale(
        construir_sprite(NAVE_MITAD, COLORES_NAVE, ESCALA_NAVE), (32, 32)))

    estado = "inicio"
    nave, aliens, oleada, banner = nuevo_juego()
    esperando, pausa = False, 0.0
    dt = 1 / FPS

    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN:
                if estado in ("inicio", "gameover", "victoria") and evento.key == pygame.K_RETURN:
                    nave, aliens, oleada, banner = nuevo_juego()
                    esperando = False
                    estado = "jugando"
                    sonar("inicio")
                    musica_on()
                elif estado == "jugando":
                    if evento.key == pygame.K_1:
                        nave.nivel_arma = 1
                    elif evento.key == pygame.K_2:
                        nave.nivel_arma = 2
                    elif evento.key == pygame.K_3:
                        nave.nivel_arma = 3
        tiempo = pygame.time.get_ticks()

        if estado == "inicio":
            pantalla_con_titulo("START THE GAME", tiempo)

        else:
            # ----- actualizar -----
            if estado == "jugando":
                nave.actualizar(pygame.key.get_pressed(), dt)
                mult = 0.88 ** (oleada - 1)          # aliens disparan más rápido
                for a in aliens:
                    a.actualizar(dt, nave, balas_enemigas, mult)
                for b in balas_enemigas:
                    b.actualizar(dt, nave)

                # tus balas -> aliens
                for d in nave.disparos:
                    for a in aliens:
                        if d.vivo and a.entrado and a.rect.inflate(-8, -8).colliderect(d.rect):
                            d.vivo = False
                            a.recibir_golpe(1)
                            for _ in range(4):
                                crear_particula(d.x, d.y, random.uniform(-150, 150),
                                                random.uniform(-150, 150), 0.2, 4, PALETA_CHISPA)
                            break
                nave.disparos = [d for d in nave.disparos if d.vivo]
                aliens = [a for a in aliens if a.vivo]

                # poderes de los aliens -> tu nave
                caja = nave.hitbox
                for b in balas_enemigas:
                    if b.vivo and caja.colliderect(b.rect):
                        b.vivo = False
                        nave.recibir_dano(b.dano)
                balas_enemigas[:] = [b for b in balas_enemigas if b.vivo]

                if nave.vida <= 0:
                    explosion(nave.rect.centerx, nave.rect.centery, (0, 230, 255), 60)
                    estado = "gameover"
                    musica_off()
                    sonar("gameover")

                # oleada limpiada
                if estado == "jugando" and not aliens:
                    if not esperando:
                        esperando, pausa = True, 1.5
                    pausa -= dt
                    if pausa <= 0:
                        esperando = False
                        if oleada >= OLEADAS_TOTALES:
                            estado = "victoria"
                            musica_off()
                            sonar("victoria")
                        else:
                            oleada += 1
                            aliens = crear_oleada(oleada)
                            banner = 2.2
                            sonar("oleada")
                banner = max(0, banner - dt)

            for p in particulas:
                p.actualizar(dt)
            for d in destellos:
                d.actualizar(dt)
            particulas[:] = [p for p in particulas if p.vida > 0]
            destellos[:] = [d for d in destellos if d.vida > 0]

            # ----- dibujar -----
            pantalla.fill(NEGRO)
            for p in particulas:
                p.dibujar()
            for a in aliens:
                a.dibujar()
            for b in balas_enemigas:
                b.dibujar()
            for d in nave.disparos:
                d.dibujar()
            if estado != "gameover":
                nave.dibujar(tiempo)
            for d in destellos:
                d.dibujar()
            dibujar_hud(nave, oleada, aliens)

            if estado == "jugando" and banner > 0:
                dibujar_titulo(f"WAVE {oleada}", ANCHO // 2, 250, 6)
            elif estado == "gameover":
                dibujar_titulo("GAME OVER", ANCHO // 2, 200, 8)
                if (tiempo // 500) % 2 == 0:
                    sub = texto_pixelado("PRESS ENTER", 3, BLANCO)
                    pantalla.blit(sub, (ANCHO // 2 - sub.get_width() // 2, 330))
            elif estado == "victoria":
                dibujar_titulo("YOU WIN", ANCHO // 2, 200, 8)
                if (tiempo // 500) % 2 == 0:
                    sub = texto_pixelado("PRESS ENTER", 3, BLANCO)
                    pantalla.blit(sub, (ANCHO // 2 - sub.get_width() // 2, 330))

        pygame.display.flip()
        dt = min(reloj.tick(FPS) / 1000, 0.05)


if __name__ == "__main__":
    main()