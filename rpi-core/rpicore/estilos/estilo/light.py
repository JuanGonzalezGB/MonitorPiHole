from rpicore.estilos.estilo.estilizador import Estilo


class LightColor(Estilo):
    def __init__(self):    


        self.nombre = "light"
        self.bg ="#f5f5f0"
        self.bg2 ="#ebebe5"  
        self.border ="#d0d0c8"
        self.colorok ="#1a7a3a"  
        self.colormid = "#b85c00"   
        self.colorbad = "#c0392b"   
        self.color1 = "#1a7a6a"   
        self.color2 = "#2a5fa8"   
        self.color3 = "#1a1a18"   
        self.muted = "#8a8a7a"   
        self.boton = "#79bbab"

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
