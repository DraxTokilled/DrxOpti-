import customtkinter as ctk


class Tooltip:
    """Tooltip flotante estilo cyber — aparece al pasar el mouse sobre un widget."""

    def __init__(self, widget, text: str, delay_ms: int = 450):
        self._widget = widget
        self._text   = text
        self._delay  = delay_ms
        self._tip    = None
        self._after  = None

        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<Button>", self._hide, add="+")

    def _schedule(self, _event=None):
        self._cancel()
        self._after = self._widget.after(self._delay, self._show)

    def _cancel(self):
        if self._after:
            self._widget.after_cancel(self._after)
            self._after = None

    def _show(self):
        if self._tip:
            return
        x = self._widget.winfo_rootx() + 12
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 6

        self._tip = ctk.CTkToplevel(self._widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"+{x}+{y}")
        self._tip.attributes("-topmost", True)
        try:
            self._tip.attributes("-alpha", 0.94)
        except Exception:
            pass

        frame = ctk.CTkFrame(self._tip, fg_color="#13131F", corner_radius=6,
                             border_width=1, border_color="#2A2A45")
        frame.pack()
        ctk.CTkLabel(frame, text=self._text,
                     font=ctk.CTkFont("Consolas", 9),
                     text_color="#8899AA",
                     wraplength=260, justify="left").pack(padx=10, pady=6)

    def _hide(self, _event=None):
        self._cancel()
        if self._tip:
            self._tip.destroy()
            self._tip = None
