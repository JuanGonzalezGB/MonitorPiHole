from rpicore.estilos.estilo import dark, light

# ─── Registro de temas ───────────────────────────────────────────────────────
CLASESTEMAS: dict = {
    "dark":  dark.DarkColor,
    "light": light.LightColor,
}

# Nombre visible en el dropdown → código interno usado por EstiloFactory
TEMAS: dict[str, str] = {
    "Oscuro": "dark",
    "Claro":  "light",
}

# ─── Fuentes compartidas ─────────────────────────────────────────────────────
FORMATS: dict = {
    "F_TITLE":  ("monospace", 10, "bold"),
    "F_NORMAL": ("monospace", 10),
    "F_SMALL":  ("monospace", 8),
}
