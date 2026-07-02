import customtkinter as ctk
import yt_dlp
import os
import threading
import urllib.parse
import subprocess
import sys
import tkinter as tk
import requests
import json
import hashlib
from PIL import Image, ImageTk

LICENSE_SERVER = "https://verification-uj7s.onrender.com"
LICENSE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".license")

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# ── Rutas del proyecto (Adaptadas para compatibilidad .exe) ───────────────────
if getattr(sys, 'frozen', False):
    # Si corre empaquetado como .exe, busca los recursos en la carpeta temporal interna
    BASE_DIR_RECURSOS = sys._MEIPASS
    # Mantiene la carpeta música en tu directorio real de trabajo
    BASE_DIR = os.getcwd() 
else:
    BASE_DIR_RECURSOS = r"C:\Users\mtsthgo\Documents\DESCARGAS DE MP3"
    BASE_DIR = BASE_DIR_RECURSOS

CARPETA_FONDO  = os.path.join(BASE_DIR_RECURSOS, "fondo")
CARPETA_ICONS  = os.path.join(BASE_DIR_RECURSOS, "iconos")
CARPETA_MUSICA = os.path.join(BASE_DIR, "musica")
FONDO_PATH     = os.path.join(CARPETA_FONDO, "fondo1.png")  # dinámico

# ── Fuente principal ──────────────────────────────────────────────────────────
F_TITULO  = ("Segoe UI", 22, "bold")
F_SUBTIT  = ("Segoe UI", 12)
F_CARD    = ("Segoe UI", 15, "bold")
F_BODY    = ("Segoe UI", 13)
F_SMALL   = ("Segoe UI", 10)
F_BADGE   = ("Segoe UI", 11, "bold")
F_NAV     = ("Segoe UI", 13)
F_LOGO    = ("Segoe UI", 20, "bold")
F_STAT    = ("Segoe UI", 22, "bold")
F_MONO    = ("Consolas", 11)
F_MONO_SM = ("Consolas", 9)
F_MONO_XS = ("Consolas", 9, "bold")

# ── Paleta ────────────────────────────────────────────────────────────────────
C_BG_SIDEBAR   = "#0A0910"
C_BG_MAIN      = "#0D0C18"
C_BG_CARD_S    = "#151322"
C_BG_INPUT     = "#1A1828"
C_BG_HOVER     = "#21203A"
C_ACCENT       = "#6C52E8"
C_ACCENT_LIGHT = "#8B72F0"
C_SPOTIFY      = "#1DB954"
C_YOUTUBE      = "#FF0000"
C_SUCCESS      = "#22C55E"
C_WARNING      = "#F59E0B"
C_ERROR        = "#EF4444"
C_TEXT_PRI     = "#F0EEFF"
C_TEXT_SEC     = "#7B7899"
C_TEXT_MED     = "#A9A6C4"
C_BORDER       = "#2A2845"
C_STAT_DL      = "#6C52E8"; C_STAT_DL_BG = "#1E1A38"
C_STAT_OK      = "#22C55E"; C_STAT_OK_BG = "#0F2A1A"
C_STAT_GB      = "#F59E0B"; C_STAT_GB_BG = "#2A1F0A"


def _cargar_icono(nombre, size=(18, 18)):
    path = os.path.join(CARPETA_ICONS, nombre)
    if not os.path.exists(path):
        return None
    try:
        img = Image.open(path).convert("RGBA").resize(size, Image.LANCZOS)
        return ctk.CTkImage(light_image=img, dark_image=img, size=size)
    except Exception:
        return None


class BgCanvas(tk.Canvas):
    """Canvas de fondo: carga fondo1.png directamente, si no hay usa glow."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._bg_photo = None
        self.bind("<Configure>", self._redraw)

    def _redraw(self, event=None):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 2 or h < 2:
            return
        if os.path.exists(FONDO_PATH):
            self._draw_image(w, h)
        else:
            self._draw_glow(w, h)

    def _draw_image(self, w, h):
        try:
            img = Image.open(FONDO_PATH).convert("RGB")
            ratio = max(w / img.width, h / img.height)
            nw, nh = int(img.width * ratio), int(img.height * ratio)
            img = img.resize((nw, nh), Image.LANCZOS)
            x0 = (nw - w) // 2
            y0 = (nh - h) // 2
            img = img.crop((x0, y0, x0 + w, y0 + h))
            overlay = Image.new("RGB", (w, h), (8, 7, 18))
            img = Image.blend(img, overlay, alpha=0.52)
            self._bg_photo = ImageTk.PhotoImage(img)
            self.create_image(0, 0, anchor="nw", image=self._bg_photo)
        except Exception as e:
            print(f"Error cargando fondo: {e}")
            self._draw_glow(w, h)

    def _draw_glow(self, w, h):
        self.create_rectangle(0, 0, w, h, fill="#0D0C18", outline="")
        cx, cy = w * 0.62, h * 0.18
        for i in range(36, 0, -1):
            ratio = i / 36
            ro = int(300 * ratio)
            r = max(0, min(255, int(0x6C * ratio * 0.7 + 0x0D * (1 - ratio))))
            g = max(0, min(255, int(0x52 * ratio * 0.5 + 0x0C * (1 - ratio))))
            b = max(0, min(255, int(0xE8 * ratio * 0.8 + 0x18 * (1 - ratio))))
            self.create_oval(cx-ro, cy-ro*0.6, cx+ro, cy+ro*0.6,
                             fill=f"#{r:02x}{g:02x}{b:02x}", outline="")
        cx2, cy2 = w * 0.28, h * 0.72
        for i in range(18, 0, -1):
            ratio = i / 18
            ro = int(160 * ratio)
            r2 = max(0, min(255, int(0x3B * ratio * 0.5)))
            g2 = max(0, min(255, int(0x28 * ratio * 0.4)))
            b2 = max(0, min(255, int(0x9E * ratio * 0.6 + 0x18 * (1 - ratio))))
            self.create_oval(cx2-ro, cy2-ro*0.5, cx2+ro, cy2+ro*0.5,
                             fill=f"#{r2:02x}{g2:02x}{b2:02x}", outline="")


class ReproductorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Blackflag — Music Downloader")
        self.geometry("1120x720")
        self.minsize(1000, 640)
        self.configure(fg_color=C_BG_MAIN)

        # Cargar icono de la ventana principal dinámicamente si existe
        path_logo = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.ico")
        if getattr(sys, 'frozen', False):
            path_logo = os.path.join(sys._MEIPASS, "logo.ico")
        if os.path.exists(path_logo):
            self.iconbitmap(path_logo)

        self._nav_actual   = "inicio"
        self._panel_actual = None
        self._license_valid = False
        self._license_key = ""

        self._ico_yt = _cargar_icono("YouTube.ico")
        self._ico_sp = _cargar_icono("spotify.ico")

        self._show_license_screen()

    # ── Licencia ───────────────────────────────────────────────────────────────

    def _show_license_screen(self):
        self.lic_frame = ctk.CTkFrame(self, fg_color=C_BG_MAIN, corner_radius=0)
        self.lic_frame.pack(fill="both", expand=True)

        container = ctk.CTkFrame(self.lic_frame, fg_color="transparent")
        container.place(relx=0.5, rely=0.45, anchor="center")

        ctk.CTkLabel(container, text="⚑", font=("Segoe UI", 36),
                     text_color=C_ACCENT).pack(pady=(0, 4))
        ctk.CTkLabel(container, text="Blackflag", font=("Segoe UI", 20, "bold"),
                     text_color=C_TEXT_PRI).pack()
        ctk.CTkLabel(container, text="Ingresá tu clave de licencia",
                     font=F_BODY, text_color=C_TEXT_SEC).pack(pady=(4, 16))

        self.lic_entry = ctk.CTkEntry(container,
            placeholder_text="XXXX-XXXX-XXXX-XXXX",
            font=("Consolas", 14), fg_color=C_BG_INPUT, border_color=C_BORDER,
            text_color=C_TEXT_PRI, placeholder_text_color=C_TEXT_SEC,
            corner_radius=10, height=44, width=320, justify="center")
        self.lic_entry.pack(pady=(0, 12))
        self.lic_entry.bind("<Return>", lambda e: self._validar_licencia())

        self.lic_btn = ctk.CTkButton(container, text="Activar",
            font=("Segoe UI", 14, "bold"), fg_color=C_ACCENT, hover_color="#5540C8",
            text_color="white", corner_radius=10, height=44, width=200,
            command=self._validar_licencia)
        self.lic_btn.pack(pady=(0, 8))

        self.lic_status = ctk.CTkLabel(container, text="",
                                       font=F_SMALL, text_color=C_ERROR)
        self.lic_status.pack(pady=(4, 0))

        ctk.CTkLabel(container,
                     text="Sin conexión? Usá el modo offline si ya activaste antes.",
                     font=("Segoe UI", 9), text_color=C_TEXT_SEC).pack(pady=(16, 0))

        self.lic_entry.focus()
        self._check_saved_license()

    def _check_saved_license(self):
        if os.path.exists(LICENSE_FILE):
            try:
                with open(LICENSE_FILE, "r") as f:
                    data = json.load(f)
                key = data.get("key", "")
                expiry = data.get("expiry", "")
                sig = data.get("sig", "")

                expected = hashlib.sha256(f"{key}:{expiry}:{LICENSE_SERVER}".encode()).hexdigest()
                if sig != expected:
                    return

                from datetime import datetime
                expiry_dt = datetime.fromisoformat(expiry)
                now = datetime.utcnow()
                if expiry_dt > now:
                    self._license_key = key
                    self._license_valid = True
                    self.lic_btn.configure(state="disabled", text="✓ Válida (offline)")
                    self.lic_status.configure(text="Licencia offline válida", text_color=C_SUCCESS)
                    self.after(1200, self._license_success)
            except Exception:
                pass

    def _validar_licencia(self):
        key = self.lic_entry.get().strip().upper()
        if not key:
            self.lic_status.configure(text="Ingresá una clave")
            return

        self.lic_btn.configure(state="disabled", text="Verificando...")
        self.lic_status.configure(text="", text_color=C_ERROR)

        def _thread():
            try:
                resp = requests.get(f"{LICENSE_SERVER}/validate", params={"key": key}, timeout=10)
                data = resp.json()

                if data.get("valid"):
                    expiry_iso = data.get("expiration_date", "")

                    sig = hashlib.sha256(f"{key}:{expiry_iso}:{LICENSE_SERVER}".encode()).hexdigest()
                    try:
                        with open(LICENSE_FILE, "w") as f:
                            json.dump({"key": key, "expiry": expiry_iso, "sig": sig}, f)
                    except Exception:
                        pass

                    self._license_key = key
                    self._license_valid = True
                    self.after(0, self._license_success)
                else:
                    reason = data.get("reason", "INVALID")
                    msgs = {"EXPIRED": "✕ La licencia expiró", "KEY_NOT_FOUND": "✕ Clave inválida",
                            "KEY_DISABLED": "✕ Licencia desactivada"}
                    msg = msgs.get(reason, "✕ Clave inválida")
                    self.after(0, lambda: self._license_fail(msg))
            except requests.exceptions.ConnectionError:
                msg = "✕ No se pudo conectar al servidor"
                if os.path.exists(LICENSE_FILE):
                    msg += "\n   Usando modo offline..."
                    self.after(0, lambda: self._try_offline(key))
                else:
                    self.after(0, lambda: self._license_fail(msg))
            except Exception as e:
                self.after(0, lambda: self._license_fail(f"✕ Error: {str(e)[:40]}"))
            finally:
                self.after(0, lambda: self.lic_btn.configure(state="normal", text="Activar"))

        threading.Thread(target=_thread, daemon=True).start()

    def _try_offline(self, key):
        self._license_key = key
        self._license_valid = True
        self.lic_status.configure(text="Modo offline activado", text_color=C_WARNING)
        self.after(1500, self._license_success)

    def _license_success(self):
        self.lic_frame.destroy()
        self._build_ui()
        self.actualizar_biblioteca()
        self._start_periodic_validation()

    def _license_fail(self, msg):
        self.lic_status.configure(text=msg)
        self.lic_btn.configure(state="normal", text="Activar")
        self.lic_entry.focus()

    def _license_close(self):
        self.destroy()
        sys.exit(0)

    def _start_periodic_validation(self):
        self.after(10000, self._validate_periodic)

    def _validate_periodic(self):
        if not self._license_valid:
            return
        threading.Thread(target=self._check_license_background, daemon=True).start()
        self.after(60000, self._validate_periodic)

    def _check_license_background(self):
        try:
            resp = requests.get(f"{LICENSE_SERVER}/validate",
                                params={"key": self._license_key}, timeout=10)
            data = resp.json()
            if not data.get("valid"):
                self.after(0, self._license_expired_while_running)
        except Exception:
            pass

    def _license_expired_while_running(self):
        self._license_valid = False
        warn = ctk.CTkToplevel(self)
        warn.title("Licencia expirada")
        warn.geometry("360x180")
        warn.configure(fg_color=C_BG_MAIN)
        warn.transient(self)
        warn.grab_set()
        ctk.CTkLabel(warn, text="⚠", font=("Segoe UI", 36),
                     text_color=C_ERROR).pack(pady=(16, 4))
        ctk.CTkLabel(warn, text="Tu licencia expiró",
                     font=("Segoe UI", 16, "bold"), text_color=C_TEXT_PRI).pack()
        ctk.CTkLabel(warn, text="El programa se cerrará.",
                     font=F_BODY, text_color=C_TEXT_SEC).pack(pady=(6, 16))
        ctk.CTkButton(warn, text="Cerrar", command=self.destroy,
                      fg_color=C_ERROR, corner_radius=10).pack()
        self.after(5000, self.destroy)

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        root.pack(fill="both", expand=True)
        root.grid_columnconfigure(1, weight=1)
        root.grid_rowconfigure(0, weight=1)

        self._build_sidebar(root)

        right = ctk.CTkFrame(root, fg_color="transparent", corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(0, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self.bg_canvas = BgCanvas(right, bg="#0D0C18", highlightthickness=0)
        self.bg_canvas.grid(row=0, column=0, sticky="nsew")

        self.main_frame = ctk.CTkFrame(right, fg_color="transparent", corner_radius=0)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self._build_topbar()
        self._build_panel_inicio()

    # ── Sidebar ───────────────────────────────────────────────────────────────

    def _build_sidebar(self, parent):
        sb = ctk.CTkFrame(parent, fg_color=C_BG_SIDEBAR, width=240, corner_radius=0)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)

        # Logo
        lf = ctk.CTkFrame(sb, fg_color="transparent")
        lf.pack(fill="x", padx=22, pady=(28, 24))
        ctk.CTkLabel(lf, text="⚑", font=("Segoe UI", 24), text_color=C_ACCENT).pack(side="left", padx=(0, 10))
        tf = ctk.CTkFrame(lf, fg_color="transparent")
        tf.pack(side="left")
        ctk.CTkLabel(tf, text="Blackflag", font=F_LOGO, text_color=C_TEXT_PRI).pack(anchor="w")
        ctk.CTkLabel(tf, text="music downloader", font=F_SMALL, text_color=C_TEXT_SEC).pack(anchor="w")

        ctk.CTkFrame(sb, height=1, fg_color=C_BORDER).pack(fill="x", padx=16, pady=(0, 14))

        # Nav
        ctk.CTkLabel(sb, text="GENERAL", font=F_MONO_XS, text_color=C_TEXT_SEC).pack(anchor="w", padx=22, pady=(2, 6))

        self._nav_frames = {}
        nav_items = [
            ("inicio",    "⌂", "Inicio",     self._show_inicio),
            ("descargas", "↓", "Descargar",  self._show_descargar),
            ("biblioteca","♪", "Biblioteca", self._show_biblioteca),
            ("ajustes",   "⚙", "Ajustes",    self._show_ajustes),
        ]
        for key, icon, label, cmd in nav_items:
            self._nav_item(sb, key, icon, label, cmd)

        ctk.CTkFrame(sb, height=1, fg_color=C_BORDER).pack(fill="x", padx=16, pady=14)

        # Fuentes
        ctk.CTkLabel(sb, text="FUENTES", font=F_MONO_XS, text_color=C_TEXT_SEC).pack(anchor="w", padx=22, pady=(0, 6))
        self._source_item(sb, self._ico_yt, "YouTube", C_YOUTUBE, self._show_descargar)
        self._source_item(sb, self._ico_sp, "Spotify", C_SPOTIFY, self._show_descargar)

        ctk.CTkFrame(sb, height=1, fg_color=C_BORDER).pack(fill="x", padx=16, pady=14)

        # Playlists
        ctk.CTkLabel(sb, text="PLAYLISTS", font=F_MONO_XS, text_color=C_TEXT_SEC).pack(anchor="w", padx=22, pady=(0, 6))
        self.lbl_count_mis = self._playlist_item(sb, "≡", "Mis canciones", "0")
        ctk.CTkButton(sb, text="+ Nueva playlist", font=F_SMALL,
                      fg_color="transparent", text_color=C_TEXT_SEC,
                      hover_color=C_BG_HOVER, anchor="w", height=30).pack(fill="x", padx=12, pady=2)

        # Espacio inferior
        ctk.CTkFrame(sb, height=20, fg_color="transparent").pack(side="bottom")

    def _nav_item(self, parent, key, icon, label, cmd):
        active = (key == self._nav_actual)
        f = ctk.CTkFrame(parent, fg_color=C_ACCENT if active else "transparent", corner_radius=8)
        f.pack(fill="x", padx=12, pady=2)
        ctk.CTkLabel(f, text=icon, font=("Segoe UI", 14),
                     text_color=C_TEXT_PRI if active else C_TEXT_SEC, width=24).pack(side="left", padx=(10, 6), pady=8)
        ctk.CTkLabel(f, text=label, font=F_NAV,
                     text_color=C_TEXT_PRI if active else C_TEXT_MED).pack(side="left")
        f.bind("<Button-1>", lambda e, c=cmd, k=key: self._nav_click(k, c))
        for child in f.winfo_children():
            child.bind("<Button-1>", lambda e, c=cmd, k=key: self._nav_click(k, c))
        self._nav_frames[key] = f

    def _nav_click(self, key, cmd):
        for k, f in self._nav_frames.items():
            is_active = (k == key)
            f.configure(fg_color=C_ACCENT if is_active else "transparent")
            for child in f.winfo_children():
                try:
                    child.configure(text_color=C_TEXT_PRI if is_active else C_TEXT_MED)
                except Exception:
                    pass
        self._nav_actual = key
        cmd()

    def _source_item(self, parent, icon_img, label, color, cmd):
        f = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=8)
        f.pack(fill="x", padx=12, pady=2)
        if icon_img:
            ctk.CTkLabel(f, text="", image=icon_img, width=24).pack(side="left", padx=(10, 6), pady=7)
        else:
            ctk.CTkLabel(f, text="●", font=("Segoe UI", 12), text_color=color, width=24).pack(side="left", padx=(10, 6), pady=7)
        ctk.CTkLabel(f, text=label, font=F_NAV, text_color=C_TEXT_MED).pack(side="left")
        f.bind("<Button-1>", lambda e: cmd())
        for c in f.winfo_children():
            c.bind("<Button-1>", lambda e: cmd())

    def _playlist_item(self, parent, icon, label, count):
        f = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=8)
        f.pack(fill="x", padx=12, pady=2)
        ctk.CTkLabel(f, text=icon, font=("Segoe UI", 13), text_color=C_ACCENT_LIGHT, width=24).pack(side="left", padx=(10, 6), pady=7)
        ctk.CTkLabel(f, text=label, font=F_NAV, text_color=C_TEXT_MED).pack(side="left", expand=True, anchor="w")
        lbl = ctk.CTkLabel(f, text=count, font=F_MONO_XS,
                           fg_color=C_ACCENT, text_color="white", corner_radius=10, padx=7, pady=1)
        lbl.pack(side="right", padx=10)
        return lbl

    # ── Topbar ────────────────────────────────────────────────────────────────

    def _build_topbar(self):
        tb = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=70)
        tb.grid(row=0, column=0, sticky="ew", padx=36, pady=(28, 0))
        tb.grid_columnconfigure(0, weight=1)

        left = ctk.CTkFrame(tb, fg_color="transparent")
        left.pack(side="left")
        ctk.CTkLabel(left, text="¡Hola!", font=F_TITULO, text_color=C_TEXT_PRI).pack(anchor="w")
        ctk.CTkLabel(left, text="¿Qué música querés descargar hoy?", font=F_SUBTIT, text_color=C_TEXT_SEC).pack(anchor="w")

        ctk.CTkButton(tb, text="+ Pegar portapapeles", font=F_SMALL,
                      fg_color="transparent", border_width=1, border_color=C_BORDER,
                      text_color=C_TEXT_MED, hover_color=C_BG_HOVER,
                      corner_radius=8, height=36, command=self._pegar_portapapeles).pack(side="right")

    # ── Panel helpers ─────────────────────────────────────────────────────────

    def _clear_panel(self):
        if self._panel_actual and self._panel_actual.winfo_exists():
            self._panel_actual.destroy()
        self._panel_actual = None

    def _new_scroll(self):
        s = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent",
                                   scrollbar_button_color=C_BORDER,
                                   scrollbar_button_hover_color=C_ACCENT)
        s.grid(row=1, column=0, sticky="nsew", padx=28, pady=(14, 14))
        s.grid_columnconfigure(0, weight=1)
        self._panel_actual = s
        return s

    # ── Badges YouTube / Spotify (sin fondo, texto blanco) ───────────────────

    def _build_source_badges(self, parent):
        br = ctk.CTkFrame(parent, fg_color="transparent")
        br.pack(fill="x", padx=18, pady=(0, 16))

        # YouTube
        yb = ctk.CTkFrame(br, fg_color="transparent")
        yb.pack(side="left", padx=(0, 16))
        yb_inner = ctk.CTkFrame(yb, fg_color="transparent")
        yb_inner.pack()
        if self._ico_yt:
            ctk.CTkLabel(yb_inner, text="", image=self._ico_yt).pack(side="left", padx=(0, 6))
        else:
            ctk.CTkLabel(yb_inner, text="▶", font=("Segoe UI", 11), text_color=C_YOUTUBE).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(yb_inner, text="YouTube", font=F_BADGE, text_color="white").pack(side="left")

        # Spotify
        sb2 = ctk.CTkFrame(br, fg_color="transparent")
        sb2.pack(side="left")
        sb2_inner = ctk.CTkFrame(sb2, fg_color="transparent")
        sb2_inner.pack()
        if self._ico_sp:
            ctk.CTkLabel(sb2_inner, text="", image=self._ico_sp).pack(side="left", padx=(0, 6))
        else:
            ctk.CTkLabel(sb2_inner, text="●", font=("Segoe UI", 11), text_color=C_SPOTIFY).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(sb2_inner, text="Spotify", font=F_BADGE, text_color="white").pack(side="left")

    # ── Panel: Inicio ─────────────────────────────────────────────────────────

    def _show_inicio(self):
        self._clear_panel()
        self._build_panel_inicio()

    def _build_panel_inicio(self):
        scroll = self._new_scroll()

        # Card URL
        card = ctk.CTkFrame(scroll, fg_color=C_BG_CARD_S, corner_radius=14,
                            border_width=1, border_color=C_BORDER)
        card.pack(fill="x", pady=(0, 16))

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=18, pady=(16, 8))
        ic = ctk.CTkFrame(hdr, fg_color=C_ACCENT, width=36, height=36, corner_radius=18)
        ic.pack(side="left", padx=(0, 12))
        ic.pack_propagate(False)
        ctk.CTkLabel(ic, text="⊕", font=("Segoe UI", 16), text_color="white").pack(expand=True)
        ctk.CTkLabel(hdr, text="URL de YouTube o Spotify", font=F_CARD, text_color=C_TEXT_PRI).pack(side="left")

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=(0, 8))
        self.input_url = ctk.CTkEntry(row,
            placeholder_text="Pega el enlace de YouTube o Spotify...",
            font=("Consolas", 12), fg_color=C_BG_INPUT, border_color=C_BORDER,
            text_color=C_TEXT_PRI, placeholder_text_color=C_TEXT_SEC,
            corner_radius=10, height=46)
        self.input_url.pack(side="left", fill="x", expand=True, padx=(0, 12))
        self.btn_descargar = ctk.CTkButton(row, text="Descargar",
            font=("Segoe UI", 14, "bold"), fg_color=C_ACCENT, hover_color="#5540C8",
            text_color="white", corner_radius=10, height=46, width=130,
            command=self.iniciar_hilo_descarga)
        self.btn_descargar.pack(side="right")

        self._build_source_badges(card)

        # Status bar
        sc = ctk.CTkFrame(scroll, fg_color=C_BG_CARD_S, corner_radius=10,
                          border_width=1, border_color=C_BORDER)
        sc.pack(fill="x", pady=(0, 16))
        self.label_estado = ctk.CTkLabel(sc, text="  ● Listo para descargar",
                                         font=F_BODY, text_color=C_SUCCESS, anchor="w")
        self.label_estado.pack(fill="x", padx=16, pady=10)

        # Stats
        sr = ctk.CTkFrame(scroll, fg_color="transparent")
        sr.pack(fill="x", pady=(0, 20))
        sr.grid_columnconfigure((0, 1, 2), weight=1)
        self.stat_progreso  = self._stat_card(sr, 0, "↓", "0",    "Descargas en progreso", C_STAT_DL, C_STAT_DL_BG)
        self.stat_completas = self._stat_card(sr, 1, "✓", "0",    "Descargas completadas", C_STAT_OK, C_STAT_OK_BG)
        self.stat_espacio   = self._stat_card(sr, 2, "♪", "0 MB", "Espacio en biblioteca", C_STAT_GB, C_STAT_GB_BG)

        # Biblioteca header
        bh = ctk.CTkFrame(scroll, fg_color="transparent")
        bh.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(bh, text="Biblioteca", font=("Segoe UI", 18, "bold"), text_color=C_TEXT_PRI).pack(side="left")
        self.lbl_bib_count = ctk.CTkLabel(bh, text="0 pistas", font=F_MONO, text_color=C_TEXT_SEC)
        self.lbl_bib_count.pack(side="right")

        # Tabs
        tabs = ctk.CTkFrame(scroll, fg_color="transparent")
        tabs.pack(fill="x", pady=(0, 10))
        ctk.CTkButton(tabs, text="Todas las canciones", font=F_BODY,
                      fg_color=C_ACCENT, hover_color=C_ACCENT, text_color="white",
                      corner_radius=20, height=32, width=155).pack(side="left", padx=(0, 8))
        for t in ["Recientes"]:
            ctk.CTkButton(tabs, text=t, font=F_BODY,
                          fg_color="transparent", border_width=1, border_color=C_BORDER,
                          text_color=C_TEXT_MED, hover_color=C_BG_HOVER,
                          corner_radius=20, height=32, width=100).pack(side="left", padx=(0, 8))

        self.lista_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.lista_frame.pack(fill="x")
        self.actualizar_biblioteca()

    # ── Panel: Descargar ──────────────────────────────────────────────────────

    def _show_descargar(self):
        self._clear_panel()
        scroll = self._new_scroll()

        ctk.CTkLabel(scroll, text="Descargar música", font=("Segoe UI", 20, "bold"),
                     text_color=C_TEXT_PRI).pack(anchor="w", pady=(0, 16))

        card = ctk.CTkFrame(scroll, fg_color=C_BG_CARD_S, corner_radius=14,
                            border_width=1, border_color=C_BORDER)
        card.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(card, text="Pegá el link de YouTube o Spotify:",
                     font=F_BODY, text_color=C_TEXT_MED).pack(anchor="w", padx=18, pady=(16, 8))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=(0, 10))
        self.input_url = ctk.CTkEntry(row,
            placeholder_text="https://youtube.com/watch?v=...  o  https://open.spotify.com/track/...",
            font=("Consolas", 12), fg_color=C_BG_INPUT, border_color=C_BORDER,
            text_color=C_TEXT_PRI, placeholder_text_color=C_TEXT_SEC,
            corner_radius=10, height=46)
        self.input_url.pack(side="left", fill="x", expand=True, padx=(0, 12))
        self.btn_descargar = ctk.CTkButton(row, text="Descargar",
            font=("Segoe UI", 14, "bold"), fg_color=C_ACCENT, hover_color="#5540C8",
            text_color="white", corner_radius=10, height=46, width=130,
            command=self.iniciar_hilo_descarga)
        self.btn_descargar.pack(side="right")

        self._build_source_badges(card)

        # Info
        info_card = ctk.CTkFrame(scroll, fg_color=C_BG_CARD_S, corner_radius=14,
                                 border_width=1, border_color=C_BORDER)
        info_card.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(info_card, text="ℹ  Información", font=("Segoe UI", 13, "bold"),
                     text_color=C_TEXT_PRI).pack(anchor="w", padx=18, pady=(14, 6))
        for line in [
            "• YouTube: descarga en el mejor formato de audio disponible (webm/m4a).",
            "• Spotify: usa spotdl para buscar y descargar en MP3.",
            "• Playlists de YouTube: pegá el link de la playlist completa.",
            "• Si falla, verificá que yt-dlp y spotdl estén instalados.",
        ]:
            ctk.CTkLabel(info_card, text=line, font=F_SMALL,
                         text_color=C_TEXT_SEC, anchor="w", justify="left").pack(anchor="w", padx=18, pady=1)
        ctk.CTkFrame(info_card, height=8, fg_color="transparent").pack()

        # Status
        sc = ctk.CTkFrame(scroll, fg_color=C_BG_CARD_S, corner_radius=10,
                          border_width=1, border_color=C_BORDER)
        sc.pack(fill="x", pady=(0, 16))
        self.label_estado = ctk.CTkLabel(sc, text="  ● Listo",
                                         font=F_MONO, text_color=C_SUCCESS, anchor="w")
        self.label_estado.pack(fill="x", padx=16, pady=10)

        # Stats
        sr = ctk.CTkFrame(scroll, fg_color="transparent")
        sr.pack(fill="x", pady=(0, 20))
        sr.grid_columnconfigure((0, 1, 2), weight=1)
        self.stat_progreso  = self._stat_card(sr, 0, "↓", "0",    "En progreso",  C_STAT_DL, C_STAT_DL_BG)
        self.stat_completas = self._stat_card(sr, 1, "✓", "0",    "Completadas",  C_STAT_OK, C_STAT_OK_BG)
        self.stat_espacio   = self._stat_card(sr, 2, "♪", "0 MB", "Biblioteca",   C_STAT_GB, C_STAT_GB_BG)

        self.lbl_bib_count = ctk.CTkLabel(scroll, text="")
        self.lista_frame   = ctk.CTkFrame(scroll, fg_color="transparent")
        self.lista_frame.pack(fill="x")
        self.actualizar_biblioteca()

    # ── Panel: Biblioteca ─────────────────────────────────────────────────────

    def _show_biblioteca(self):
        self._clear_panel()
        scroll = self._new_scroll()

        bh = ctk.CTkFrame(scroll, fg_color="transparent")
        bh.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(bh, text="Tu Biblioteca", font=("Segoe UI", 20, "bold"), text_color=C_TEXT_PRI).pack(side="left")
        self.lbl_bib_count = ctk.CTkLabel(bh, text="0 pistas", font=F_MONO, text_color=C_TEXT_SEC)
        self.lbl_bib_count.pack(side="right")

        search_row = ctk.CTkFrame(scroll, fg_color="transparent")
        search_row.pack(fill="x", pady=(0, 14))
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *a: self.actualizar_biblioteca())
        ctk.CTkEntry(search_row, textvariable=self._search_var,
                     placeholder_text="🔍  Buscar canción...",
                     font=("Consolas", 12), fg_color=C_BG_INPUT, border_color=C_BORDER,
                     text_color=C_TEXT_PRI, placeholder_text_color=C_TEXT_SEC,
                     corner_radius=10, height=40).pack(fill="x")

        tabs = ctk.CTkFrame(scroll, fg_color="transparent")
        tabs.pack(fill="x", pady=(0, 12))
        ctk.CTkButton(tabs, text="Todas", font=F_BODY, fg_color=C_ACCENT,
                      hover_color=C_ACCENT, text_color="white", corner_radius=20,
                      height=32, width=90).pack(side="left", padx=(0, 8))
        ctk.CTkButton(tabs, text="Recientes", font=F_BODY,
                      fg_color="transparent", border_width=1, border_color=C_BORDER,
                      text_color=C_TEXT_MED, hover_color=C_BG_HOVER,
                      corner_radius=20, height=32, width=100).pack(side="left", padx=(0, 8))

        self.lista_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.lista_frame.pack(fill="x")

        self.stat_progreso  = ctk.CTkLabel(scroll, text="")
        self.stat_completas = ctk.CTkLabel(scroll, text="")
        self.stat_espacio   = ctk.CTkLabel(scroll, text="")
        self.actualizar_biblioteca()

    # ── Panel: Ajustes ────────────────────────────────────────────────────────

    def _show_ajustes(self):
        self._clear_panel()
        scroll = self._new_scroll()

        ctk.CTkLabel(scroll, text="Ajustes", font=("Segoe UI", 20, "bold"),
                     text_color=C_TEXT_PRI).pack(anchor="w", pady=(0, 20))

        # Fondo
        bg_card = ctk.CTkFrame(scroll, fg_color=C_BG_CARD_S, corner_radius=14,
                               border_width=1, border_color=C_BORDER)
        bg_card.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(bg_card, text="🖼  Fondo personalizado", font=("Segoe UI", 14, "bold"),
                     text_color=C_TEXT_PRI).pack(anchor="w", padx=18, pady=(16, 4))
        ctk.CTkLabel(bg_card,
                     text=f"Archivo fijo: {FONDO_PATH}",
                     font=F_MONO_SM, text_color=C_TEXT_SEC, justify="left").pack(anchor="w", padx=18, pady=(0, 6))

        existe = os.path.exists(FONDO_PATH)
        estado_txt = f"✓ Fondo encontrado: fondo1.png" if existe else f"✕ No encontrado: {FONDO_PATH}"
        ctk.CTkLabel(bg_card, text=estado_txt, font=F_SMALL,
                     text_color=C_SUCCESS if existe else C_ERROR).pack(anchor="w", padx=18, pady=(0, 16))

        # Carpeta música
        mus_card = ctk.CTkFrame(scroll, fg_color=C_BG_CARD_S, corner_radius=14,
                                border_width=1, border_color=C_BORDER)
        mus_card.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(mus_card, text="🎵  Carpeta de música", font=("Segoe UI", 14, "bold"),
                     text_color=C_TEXT_PRI).pack(anchor="w", padx=18, pady=(16, 4))
        ctk.CTkLabel(mus_card, text=CARPETA_MUSICA, font=F_MONO_SM,
                     text_color=C_TEXT_SEC).pack(anchor="w", padx=18, pady=(0, 6))

        archivos = [f for f in os.listdir(CARPETA_MUSICA)
                    if f.endswith(('.mp3', '.webm', '.m4a'))] if os.path.exists(CARPETA_MUSICA) else []
        total_bytes = sum(os.path.getsize(os.path.join(CARPETA_MUSICA, f))
                         for f in archivos if os.path.exists(os.path.join(CARPETA_MUSICA, f)))
        mb = total_bytes / (1024 * 1024)
        esp = f"{mb:.1f} MB" if mb < 1024 else f"{mb/1024:.1f} GB"
        ctk.CTkLabel(mus_card, text=f"{len(archivos)} canciones  ·  {esp}",
                     font=F_SMALL, text_color=C_ACCENT_LIGHT).pack(anchor="w", padx=18, pady=(0, 16))

        # Iconos
        ico_card = ctk.CTkFrame(scroll, fg_color=C_BG_CARD_S, corner_radius=14,
                                border_width=1, border_color=C_BORDER)
        ico_card.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(ico_card, text="🎨  Iconos", font=("Segoe UI", 14, "bold"),
                     text_color=C_TEXT_PRI).pack(anchor="w", padx=18, pady=(16, 4))
        ctk.CTkLabel(ico_card, text=f"Carpeta: {CARPETA_ICONS}",
                     font=F_MONO_SM, text_color=C_TEXT_SEC).pack(anchor="w", padx=18, pady=(0, 4))

        ico_row = ctk.CTkFrame(ico_card, fg_color="transparent")
        ico_row.pack(anchor="w", padx=18, pady=(0, 16))
        for nombre, img in [("YouTube.ico", self._ico_yt), ("spotify.ico", self._ico_sp)]:
            estado = "✓ cargado" if img else "✕ no encontrado"
            color  = C_SUCCESS if img else C_ERROR
            f = ctk.CTkFrame(ico_row, fg_color=C_BG_INPUT, corner_radius=8)
            f.pack(side="left", padx=(0, 10))
            inner = ctk.CTkFrame(f, fg_color="transparent")
            inner.pack(padx=10, pady=6)
            if img:
                ctk.CTkLabel(inner, text="", image=img).pack(side="left", padx=(0, 6))
            ctk.CTkLabel(inner, text=f"{nombre}  {estado}", font=F_SMALL, text_color=color).pack(side="left")

        # Cookies
        ck_card = ctk.CTkFrame(scroll, fg_color=C_BG_CARD_S, corner_radius=14,
                               border_width=1, border_color=C_BORDER)
        ck_card.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(ck_card, text="🌐  Navegador para cookies", font=("Segoe UI", 14, "bold"),
                     text_color=C_TEXT_PRI).pack(anchor="w", padx=18, pady=(16, 4))
        ctk.CTkLabel(ck_card,
                     text="Actualmente: Chrome\nNecesario para playlists privadas de YouTube.",
                     font=F_SMALL, text_color=C_TEXT_SEC, justify="left").pack(anchor="w", padx=18, pady=(0, 16))

    # ── Stat card ─────────────────────────────────────────────────────────────

    def _stat_card(self, parent, col, icon, value, label, color, bg_color):
        card = ctk.CTkFrame(parent, fg_color=C_BG_CARD_S, corner_radius=14,
                            border_width=1, border_color=C_BORDER)
        card.grid(row=0, column=col, padx=6, sticky="ew")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=20, pady=16, anchor="w")
        ib = ctk.CTkFrame(inner, fg_color=bg_color, width=44, height=44, corner_radius=22)
        ib.pack(side="left", padx=(0, 14))
        ib.pack_propagate(False)
        ctk.CTkLabel(ib, text=icon, font=("Segoe UI", 20), text_color=color).pack(expand=True)
        tf = ctk.CTkFrame(inner, fg_color="transparent")
        tf.pack(side="left")
        lbl = ctk.CTkLabel(tf, text=value, font=F_STAT, text_color=C_TEXT_PRI)
        lbl.pack(anchor="w")
        ctk.CTkLabel(tf, text=label, font=F_SMALL, text_color=C_TEXT_SEC).pack(anchor="w")
        return lbl

    # ── Biblioteca ────────────────────────────────────────────────────────────

    def actualizar_biblioteca(self):
        if not hasattr(self, 'lista_frame') or not self.lista_frame.winfo_exists():
            return
        for w in self.lista_frame.winfo_children():
            w.destroy()

        if not os.path.exists(CARPETA_MUSICA):
            os.makedirs(CARPETA_MUSICA)

        archivos = sorted([f for f in os.listdir(CARPETA_MUSICA)
                           if f.endswith(('.mp3', '.webm', '.m4a'))])

        if hasattr(self, '_search_var'):
            query = self._search_var.get().strip().lower()
            if query:
                archivos = [f for f in archivos if query in f.lower()]

        count = len(archivos)

        if hasattr(self, 'lbl_bib_count') and self.lbl_bib_count.winfo_exists():
            self.lbl_bib_count.configure(text=f"{count} pistas")
        if hasattr(self, 'lbl_count_mis'):
            self.lbl_count_mis.configure(text=str(count))
        if hasattr(self, 'stat_completas') and self.stat_completas.winfo_exists():
            self.stat_completas.configure(text=str(count))

        total_bytes = sum(os.path.getsize(os.path.join(CARPETA_MUSICA, f))
                         for f in archivos if os.path.exists(os.path.join(CARPETA_MUSICA, f)))
        mb = total_bytes / (1024 * 1024)
        esp = f"{mb:.1f} MB" if mb < 1024 else f"{mb/1024:.1f} GB"
        if hasattr(self, 'stat_espacio') and self.stat_espacio.winfo_exists():
            self.stat_espacio.configure(text=esp)

        if not archivos:
            ctk.CTkLabel(self.lista_frame, text="No hay canciones descargadas todavía.",
                         font=F_BODY, text_color=C_TEXT_SEC).pack(pady=24)
            return

        # Cabecera
        hdr = ctk.CTkFrame(self.lista_frame, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(hdr, text="#",       font=F_MONO_XS, text_color=C_TEXT_SEC, width=36).pack(side="left", padx=(8, 0))
        ctk.CTkLabel(hdr, text="TÍTULO",  font=F_MONO_XS, text_color=C_TEXT_SEC).pack(side="left", padx=52, expand=True, anchor="w")
        ctk.CTkLabel(hdr, text="FORMATO", font=F_MONO_XS, text_color=C_TEXT_SEC, width=60).pack(side="right", padx=(0, 12))
        ctk.CTkLabel(hdr, text="KBPS",    font=F_MONO_XS, text_color=C_TEXT_SEC, width=55).pack(side="right", padx=(0, 8))
        ctk.CTkFrame(self.lista_frame, height=1, fg_color=C_BORDER).pack(fill="x", pady=(0, 6))

        for i, archivo in enumerate(archivos):
            self._track_row(i + 1, archivo)

    def _track_row(self, num, archivo):
        ext = archivo.rsplit(".", 1)[-1].upper()
        nombre = archivo.rsplit(".", 1)[0]
        ext_colors = {"MP3": "#6C52E8", "WEBM": "#E85252", "M4A": "#52A8E8"}
        ec = ext_colors.get(ext, C_ACCENT)
        ext_bgs = {"MP3": "#1A1838", "WEBM": "#381818", "M4A": "#182838"}
        ebg = ext_bgs.get(ext, C_BG_INPUT)

        row = ctk.CTkFrame(self.lista_frame, fg_color="transparent", corner_radius=8)
        row.pack(fill="x", pady=2)
        row.bind("<Enter>",  lambda e, r=row: r.configure(fg_color=C_BG_HOVER))
        row.bind("<Leave>",  lambda e, r=row: r.configure(fg_color="transparent"))

        ctk.CTkLabel(row, text=f"{num:02d}", font=F_MONO,
                     text_color=C_ACCENT, width=36).pack(side="left", padx=(8, 0), pady=12)

        thumb = ctk.CTkFrame(row, fg_color=ebg, width=38, height=38, corner_radius=6)
        thumb.pack(side="left", padx=10)
        thumb.pack_propagate(False)
        icons_map = {"MP3": "♪", "WEBM": "▶", "M4A": "♫"}
        ctk.CTkLabel(thumb, text=icons_map.get(ext, "♩"), font=("Segoe UI", 16), text_color=ec).pack(expand=True)

        ctk.CTkLabel(row, text=nombre, font=F_BODY, text_color=C_TEXT_PRI,
                     anchor="w").pack(side="left", fill="x", expand=True, pady=12)

        ctk.CTkLabel(row, text=ext, font=F_MONO_XS,
                     fg_color=ebg, text_color=ec, corner_radius=6,
                     padx=8, pady=2, width=50).pack(side="right", padx=(0, 12))
        ctk.CTkLabel(row, text="320", font=F_MONO_SM,
                     text_color=C_TEXT_SEC, width=40).pack(side="right", padx=(0, 8))
        ctk.CTkButton(row, text="⋮", font=("Segoe UI", 16), fg_color="transparent",
                      text_color=C_TEXT_SEC, hover_color=C_BG_HOVER,
                      width=30, height=30, corner_radius=15).pack(side="right", padx=(0, 4))

    # ── Acciones ──────────────────────────────────────────────────────────────

    def _pegar_portapapeles(self):
        try:
            t = self.clipboard_get()
            self.input_url.delete(0, "end")
            self.input_url.insert(0, t)
        except Exception:
            pass

    def iniciar_hilo_descarga(self):
        url = self.input_url.get().strip()
        if not url:
            self._set_status("  ✕ Pegá un enlace válido", C_ERROR)
            return
        self.btn_descargar.configure(state="disabled", text="...")
        if hasattr(self, 'stat_progreso') and self.stat_progreso.winfo_exists():
            self.stat_progreso.configure(text="1")
        self._set_status("  ◌ Preparando descarga...", C_WARNING)
        hilo = threading.Thread(target=self.proceso_descarga, args=(url,))
        hilo.daemon = True
        hilo.start()

    def proceso_descarga(self, url):
        try:
            if "spotify.com" in url:
                self._descargar_spotify(url)
            else:
                self._descargar_youtube(url)
        except Exception as e:
            msg = str(e)[:60] + "..." if len(str(e)) > 60 else str(e)
            self.after(0, lambda: self._set_status(f"  ✕ {msg}", C_ERROR))
            self.after(0, lambda: self.btn_descargar.configure(state="normal", text="Descargar"))
            self.after(0, lambda: self.stat_progreso.configure(text="0")
                       if hasattr(self, 'stat_progreso') and self.stat_progreso.winfo_exists() else None)

    def _descargar_spotify(self, url):
        self.after(0, lambda: self._set_status("  ◌ Descargando via spotdl...", C_WARNING))
        if not os.path.exists(CARPETA_MUSICA):
            os.makedirs(CARPETA_MUSICA)
        proceso = subprocess.Popen(
            [sys.executable, "-m", "spotdl", url, "--output", CARPETA_MUSICA],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace")
        for linea in proceso.stdout:
            linea = linea.strip()
            if linea and ("Downloaded" in linea or "Downloading" in linea):
                c = linea[:58] + "..." if len(linea) > 58 else linea
                self.after(0, lambda l=c: self._set_status(f"  ◌ {l}", C_WARNING))
        proceso.wait()
        if proceso.returncode == 0:
            self.after(0, self._finalizar)
        else:
            self.after(0, lambda: self._set_status("  ✕ Error en spotdl. ¿Está instalado?", C_ERROR))
            self.after(0, lambda: self.btn_descargar.configure(state="normal", text="Descargar"))

    def _descargar_youtube(self, url):
        if "list=" in url and "v=" in url:
            p = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(p.query)
            lid = params.get("list", [None])[0]
            if lid:
                url = f"https://www.youtube.com/playlist?list={lid}"
        opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{CARPETA_MUSICA}/%(title)s.%(ext)s',
            'noplaylist': False,
            # Se eliminó la dependencia fija de cookies de navegador para evitar crasheos en .exe
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        self.after(0, self._finalizar)

    def _finalizar(self):
        self._set_status("  ✓ Descarga completada", C_SUCCESS)
        self.input_url.delete(0, "end")
        self.btn_descargar.configure(state="normal", text="Descargar")
        if hasattr(self, 'stat_progreso') and self.stat_progreso.winfo_exists():
            self.stat_progreso.configure(text="0")
        self.actualizar_biblioteca()

    def _set_status(self, text, color):
        if hasattr(self, 'label_estado') and self.label_estado.winfo_exists():
            self.label_estado.configure(text=text, text_color=color)


if __name__ == "__main__":
    app = ReproductorApp()
    app.mainloop()