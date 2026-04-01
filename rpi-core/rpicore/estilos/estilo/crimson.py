from rpicore.estilos.estilo.estilizador import Estilo

class CrimsonColor(Estilo):
    def __init__(self):
        self.nombre = "crimson_dark"

        self.bg      = "#0a0505"
        self.bg2     = "#120707"
        self.border  = "#2a0d0d"

        # equivalencias semánticas
        self.colorok   = "#2ecc71"
        self.colormid  = "#ffb347"
        self.colorbad  = "#ff3b3b"

        self.color1 = "#ff6b6b"
        self.color2 = "#b22222"
        self.color3 = "#f2e9e9"

        self.muted  = "#5a2a2a"
        self.boton  = "#1a0a0a"

    def colorBg(self):       return self.bg
    def colorBg2(self):      return self.bg2
    def colorBorder(self):   return self.border

    def colorColorOk(self):  return self.colorok
    def colorColorMid(self): return self.colormid
    def colorColorBad(self): return self.colorbad

    def colorColor1(self):   return self.color1
    def colorColor2(self):   return self.color2
    def colorColor3(self):   return self.color3

    def colorMuted(self):    return self.muted
    def colorBoton(self):    return self.boton

    def getNombre(self):     return self.nombre