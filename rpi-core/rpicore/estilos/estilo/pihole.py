from rpicore.estilos.estilo.estilizador import Estilo

class PiholeColor(Estilo):
    def __init__(self):
        self.nombre = "pihole"

        # fondos (gris azulado oscuro)
        self.bg      = "#1f2a27"
        self.bg2     = "#2a3631"
        self.border  = "#3a4844"

        # estados (basados en las tarjetas)
        self.colorok   = "#27ae60"   # verde (Domains on Lists)
        self.colormid  = "#c98c1a"   # amarillo (Percentage Blocked)
        self.colorbad  = "#c0392b"   # rojo (Blocked)

        # acentos principales (UI)
        self.color1 = "#2f80a3"      # azul (Total Queries)
        self.color2 = "#5dade2"      # azul más claro (gráficas / hover)
        self.color3 = "#ecf0f1"      # texto principal claro

        # secundarios
        self.muted  = "#7f8c8d"      # texto apagado
        self.boton  = "#2c3e50"      # botones estilo sidebar

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