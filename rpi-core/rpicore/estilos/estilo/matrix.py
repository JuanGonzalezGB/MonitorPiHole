from rpicore.estilos.estilo.estilizador import Estilo

class MatrixColor(Estilo):
    def __init__(self):     
        self.nombre = "matrix"

        self.bg = "#050805"        # negro verdoso muy oscuro
        self.bg2 = "#0b120b"       # fondo secundario
        self.border = "#143214"    # bordes verdes apagados

        self.colorok = "#00ff41"   # good (neón matrix puro)
        self.colormid = "#dbff3b"  # mid (amarillo-néon verdoso, tipo warning)
        self.colorbad = "#ffd900"     # bad (verde más profundo + tinte “peligro”)
        
        self.color1 = "#39ff88"      # verde agua brillante
        self.color2 = "#00ff9c"      # verde azulado neón
        self.color3 = "#c8ffd6"     # texto claro verdoso

        self.muted = "#3b693b"     # texto apagado / sombras

        self.boton = "#06210a"     # botones oscuros con tinte verde
        
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
