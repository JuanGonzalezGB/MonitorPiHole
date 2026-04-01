from rpicore.estilos.estilo.estilizador import Estilo


class DarkColor(Estilo):
    def __init__(self):
        self.nombre  = "dark"
        self.bg      = "#0f0f12"
        self.bg2     = "#161620"
        self.border  = "#1e1e2a"
        self.colorok   = "#3ddc84"
        self.colormid  = "#f0a030"
        self.colorbad     = "#e05252"
        self.color1    = "#7fd4c1"
        self.color2    = "#7a9fd4"
        self.color3   = "#e0e0e8"
        self.muted   = "#4a4a5a"
        self.boton   = "#0f2520"

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
