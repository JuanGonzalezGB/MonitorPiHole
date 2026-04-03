from rpicore.estilos.estilo.estilizador import Estilo

class CrimsonColor(Estilo):
    def __init__(self):     
        self.nombre = "crimson_dark"

        self.bg = "#0a0505"        # negro rojizo profundo
        self.bg2 = "#120707"       # fondo secundario más visible
        self.border = "#920c0c"    # bordes rojo oscuro apagado

        self.colorok = "#ff0000"     # good (verde clásico para contraste funcional)
        self.colormid = "#ff807b"    # mid (ámbar/naranja suave tipo warning)
        self.colorbad = "#ffbebe"       # bad (rojo principal del tema)

        self.color1 = "#ff6b6b"      # acento rojo-rosado tipo highlight
        self.color2 = "#b22222"     # rojo oscuro azulado (crimson frío)
        self.color3 = "#f2e9e9"     # texto claro con tinte cálido

        self.muted = "#805353"     # texto apagado rojizo

        self.boton = "#1a0a0a"     # botones oscuros con leve rojo
        
    def colorBg(self):     return self.bg
    def colorBg2(self):    return self.bg2
    def colorBorder(self): return self.border
    def colorColorOk(self):  return self.colorok
    def colorColorMid(self): return self.colormid
    def colorColorBad(self):    return self.colorbad
    def colorColor1(self):   return self.color1
    def colorColor2(self):   return self.color2
    def colorColor3(self):  return self.color3
    def colorMuted(self):  return self.muted
    def colorBoton(self):  return self.boton
    def getNombre(self):   return self.nombre
