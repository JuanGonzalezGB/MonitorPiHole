from rpicore.estilos.estilo import dark, light, matrix, crimson, teal

# ─── Registro de temas ───────────────────────────────────────────────────────
CLASESTEMAS: dict = {
    "dark": dark.DarkColor,
    "matrix": matrix.MatrixColor,
    "crimson_dark": crimson.CrimsonColor,
    "teal_dark": teal.TealColor,
    "light": light.LightColor
}
# Nombre visible en el dropdown → código interno usado por EstiloFactory
TEMAS: dict[str, str] = {
    "Oscuro": "dark",
    "Claro": "light",
    "Matrix": "matrix",
    "Blood" : "crimson_dark",
    "Turquesa":"teal_dark"
}

# ─── Fuentes compartidas ─────────────────────────────────────────────────────
FORMATS: dict = {
    "F_TITLE":  ("monospace", 10, "bold"),
    "F_NORMAL": ("monospace", 10),
    "F_SMALL":  ("monospace", 8),
}