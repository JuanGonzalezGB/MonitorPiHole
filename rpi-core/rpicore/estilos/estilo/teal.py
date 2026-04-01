from rpicore.estilos.estilo.estilizador import Estilo


class TealColor(Estilo):
    def __init__(self):
        self.nombre = "teal_dark"

        self.bg      = "#050b0c"
        self.bg2     = "#071416"
        self.border  = "#0f2a2f"

        # equivalencias semánticas
        self.colorok   = "#2ee6c5"
        self.colormid  = "#1faf7f"
        self.colorbad  = "#6063a6"

        self.color1 = "#7fffd4"
        self.color2 = "#38b6ff"
        self.color3 = "#d9f7f3"

        self.muted  = "#2a4a4f"
        self.boton  = "#06191c"

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