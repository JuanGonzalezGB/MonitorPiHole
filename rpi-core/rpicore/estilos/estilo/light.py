from rpicore.estilos.estilo.estilizador import Estilo

class LightColor(Estilo):
    def __init__(self):     
        self.nombre = "light"
        self.bg ="#ecdcd2"
        self.bg2 ="#ebdbd5"  
        self.border ="#41412b"
        self.colorok ="#19b37f"  
        self.colormid = "#e0bd20"   
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
