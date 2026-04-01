from rpicore.estilos.estilo.estilizador import Estilo

class MatrixColor(Estilo):
    def __init__(self):
        self.nombre = "matrix"

        self.bg      = "#050805"
        self.bg2     = "#0b120b"
        self.border  = "#143214"

        # equivalencias semánticas
        self.colorok   = "#00ff41"
        self.colormid  = "#ffd13b"
        self.colorbad  = "#e54100"

        self.color1 = "#39ff88"
        self.color2 = "#00ff9c"
        self.color3 = "#c8ffd6"

        self.muted  = "#2a3d2a"
        self.boton  = "#06210a"

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