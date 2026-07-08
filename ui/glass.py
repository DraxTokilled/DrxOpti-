import customtkinter as ctk

GLASS_BG     = "#13131F"
GLASS_BORDER = "#2A2A45"
GLASS_HIGHLIGHT = "#3A3A60"


def glass_frame(parent, corner_radius: int = 14, border_width: int = 1, **kwargs):
    """
    Simula un panel de cristal: fondo claro translúcido + borde brillante sutil.
    Tkinter no soporta alpha por widget, así que se simula con tonos elevados
    y un borde superior más claro para dar sensación de reflejo.
    """
    frame = ctk.CTkFrame(
        parent,
        fg_color=GLASS_BG,
        corner_radius=corner_radius,
        border_width=border_width,
        border_color=GLASS_BORDER,
        **kwargs,
    )
    return frame


def apply_window_glass(toplevel, alpha: float = 1.0):
    """
    Desactivado: la transparencia a nivel de ventana en Windows deja ver
    las apps de atrás y se ve rota. El efecto cristal se simula solo con
    los tonos elevados de los frames.
    """
    try:
        toplevel.attributes("-alpha", 1.0)
    except Exception:
        pass


def glass_header_row(parent, title: str, subtitle: str, title_color: str, height: int = 72):
    """Header sin overlap — título y subtítulo apilados con pack, nunca con place superpuesto."""
    header = ctk.CTkFrame(parent, fg_color="#0F0F1A", corner_radius=0, height=height)
    header.pack(fill="x")
    header.pack_propagate(False)

    text_col = ctk.CTkFrame(header, fg_color="transparent")
    text_col.pack(side="left", fill="y", padx=20, pady=10)

    title_lbl = ctk.CTkLabel(text_col, text=title, font=ctk.CTkFont("Consolas", 15, "bold"), text_color=title_color, anchor="w")
    title_lbl.pack(anchor="w")

    ctk.CTkLabel(text_col, text=subtitle, font=ctk.CTkFont("Consolas", 9), text_color="#445566", anchor="w").pack(anchor="w", pady=(2, 0))

    return header, title_lbl
