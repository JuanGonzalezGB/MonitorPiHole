from rpicore.estilos.estilo import dark, light

# ─── Registro de temas ───────────────────────────────────────────────────────
# Para agregar un tema:
#   1. Crea tu clase en estilo/mi_tema.py heredando de Estilo
#   2. Importala aquí y agrégala a CLASESTEMAS
#   3. Agrégala a TEMAS con { "Nombre visible": "codigo" }

CLASESTEMAS: dict = {
    "dark": dark.DarkColor,
    "light": light.LightColor
}

# Nombre visible en el dropdown → código interno usado por EstiloFactory
TEMAS: dict[str, str] = {
    "Oscuro": "dark",
    "Claro": "light",
}

# ─── Fuentes compartidas ─────────────────────────────────────────────────────
FORMATS: dict = {
    "F_TITLE":  ("monospace", 10, "bold"),
    "F_NORMAL": ("monospace", 10),
    "F_SMALL":  ("monospace", 8),
}
