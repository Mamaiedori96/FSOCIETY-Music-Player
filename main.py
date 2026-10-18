
import os
import json
import io
import random
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import pygame
from mutagen import File as MutagenFile
from mutagen.id3 import ID3
from PIL import Image, ImageTk, ImageDraw

BG = "#080808"
PANEL = "#151515"
RED = "#ff2020"
RED_DARK = "#8f0000"
WHITE = "#eeeeee"
GREY = "#999999"

APP_DIR = Path(os.getenv("APPDATA") or Path.home()) / "FSOCIETY_Music_Player"
APP_DIR.mkdir(parents=True, exist_ok=True)
DATA_FILE = APP_DIR / "library.json"

TRACK_END_EVENT = pygame.USEREVENT + 1
UPDATE_INTERVAL = 100

fereastra = tk.Tk()
fereastra.title("FSOCIETY // MUSIC PLAYER")
fereastra.geometry("1000x650")
fereastra.minsize(850, 550)
fereastra.configure(bg=BG)

audio_functional = False

try:
    pygame.init()
    pygame.mixer.init()
    pygame.mixer.music.set_endevent(TRACK_END_EVENT)
    audio_functional = True
except pygame.error as eroare:
    print("Eroare audio:", eroare)

melodii = []
index_curent = -1
este_pauza = False
redare_activa = False
shuffle_activ = False
volum = 0.7
coperta_foto = None
durata_curenta = 0.0
pozitie_start = 0.0
moment_start = 0.0
utilizator_cauta = False
identificator_redare = 0

titlu_curent = tk.StringVar(value="NO TRACK SELECTED")
status = tk.StringVar(value="SYSTEM READY // WAITING FOR INPUT")
pagina_curenta = tk.StringVar(value="HOME")
timp_afisat = tk.StringVar(value="00:00 / 00:00")


def formateaza_timp(secunde):
    secunde = max(0, int(secunde))
    return f"{secunde // 60:02d}:{secunde % 60:02d}"


def obtine_durata(cale):
    try:
        audio = MutagenFile(cale)
        if audio is not None and audio.info is not None:
            return float(audio.info.length)
    except Exception as eroare:
        print("Eroare la citirea duratei:", eroare)
    return 0.0


def obtine_pozitia():
    if not redare_activa or este_pauza:
        return pozitie_start

    if moment_start == 0:
        return pozitie_start

    pozitie = pozitie_start + time.monotonic() - moment_start

    if durata_curenta > 0:
        pozitie = min(pozitie, durata_curenta)

    return max(0.0, pozitie)


def incarca_melodii():
    try:
        date = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        if isinstance(date, list):
            return list(dict.fromkeys(
                cale for cale in date
                if isinstance(cale, str) and os.path.isfile(cale)
            ))
    except (OSError, json.JSONDecodeError):
        pass
    return []


def salveaza_melodii():
    try:
        temporar = DATA_FILE.with_suffix(".tmp")
        temporar.write_text(
            json.dumps(melodii, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        temporar.replace(DATA_FILE)
    except OSError as eroare:
        messagebox.showerror(
            "FSOCIETY",
            f"Biblioteca nu a putut fi salvată:\n{eroare}"
        )


def actualizeaza_titlu():
    if 0 <= index_curent < len(melodii):
        titlu_curent.set(os.path.basename(melodii[index_curent]))
        status.set(f"NOW PLAYING // {index_curent + 1}/{len(melodii)}")
    else:
        titlu_curent.set("NO TRACK SELECTED")
        status.set("SYSTEM READY // WAITING FOR INPUT")


def afiseaza_coperta(cale):
    global coperta_foto

    imagine = None

    try:
        taguri = ID3(cale)
        coperti = taguri.getall("APIC")
        if coperti:
            imagine = Image.open(
                io.BytesIO(coperti[0].data)
            ).convert("RGB")
    except Exception:
        pass

    if imagine is None:
        imagine = Image.new("RGB", (220, 220), PANEL)
        ImageDraw.Draw(imagine).text((55, 100), "FSOCIETY", fill=RED)

    imagine.thumbnail((220, 220))
    coperta_foto = ImageTk.PhotoImage(imagine)
    imagine_coperta.configure(image=coperta_foto)


def adauga_muzica():
    fisiere = filedialog.askopenfilenames(
        title="Selectează melodiile",
        filetypes=[
            ("Fișiere audio", "*.mp3 *.wav *.ogg"),
            ("Toate fișierele", "*.*")
        ]
    )

    adaugate = 0

    for fisier in fisiere:
        if fisier not in melodii:
            melodii.append(fisier)
            lista_melodii.insert(tk.END, os.path.basename(fisier))
            adaugate += 1

    if adaugate:
        salveaza_melodii()
        status.set(f"SYSTEM // {adaugate} TRACK(S) ADDED")


def opreste_muzica():
    global este_pauza, redare_activa
    global pozitie_start, moment_start, identificator_redare

    identificator_redare += 1
    redare_activa = False
    este_pauza = False
    pozitie_start = 0.0
    moment_start = 0.0

    if audio_functional:
        pygame.mixer.music.stop()
        pygame.event.clear(TRACK_END_EVENT)

    bara_progres.set(0)
    timp_afisat.set(f"00:00 / {formateaza_timp(durata_curenta)}")
    status.set("PLAYBACK // STOPPED")


def reda_muzica():
    global index_curent, este_pauza, redare_activa
    global durata_curenta, pozitie_start, moment_start
    global identificator_redare

    if not audio_functional:
        messagebox.showerror(
            "Audio error",
            "Sistemul audio nu a putut fi inițializat. "
            "Verifică instalarea pygame-ce."
        )
        return

    selectie = lista_melodii.curselection()

    if selectie:
        index_curent = selectie[0]
    elif index_curent == -1 and melodii:
        index_curent = 0

    if not melodii or not 0 <= index_curent < len(melodii):
        messagebox.showinfo("FSOCIETY", "Adaugă mai întâi o melodie.")
        return

    cale = melodii[index_curent]

    if not os.path.isfile(cale):
        messagebox.showerror("FSOCIETY", "Fișierul audio nu mai există.")
        return

    try:
        identificator_redare += 1
        redare_activa = False
        este_pauza = False

        pygame.mixer.music.stop()
        pygame.event.clear(TRACK_END_EVENT)

        durata_curenta = obtine_durata(cale)
        pygame.mixer.music.load(cale)
        pygame.mixer.music.set_volume(volum)
        pygame.mixer.music.play()

        redare_activa = True
        pozitie_start = 0.0
        moment_start = time.monotonic()

        lista_melodii.selection_clear(0, tk.END)
        lista_melodii.selection_set(index_curent)
        lista_melodii.activate(index_curent)

        bara_progres.set(0)
        actualizeaza_titlu()
        afiseaza_coperta(cale)
        actualizeaza_afisaj_progres()

    except (pygame.error, OSError) as eroare:
        redare_activa = False
        este_pauza = False
        messagebox.showerror(
            "Playback error",
            f"Melodia nu a putut fi redată:\n{eroare}"
        )


def pauza_muzica():
    global este_pauza, pozitie_start, moment_start

    if not audio_functional:
        return

    if este_pauza:
        pygame.mixer.music.unpause()
        este_pauza = False
        moment_start = time.monotonic()
        status.set("PLAYBACK // RESUMED")

    elif redare_activa:
        pozitie_start = obtine_pozitia()
        pygame.mixer.music.pause()
        este_pauza = True
        status.set("PLAYBACK // PAUSED")

    else:
        reda_muzica()


def reda_urmatoarea():
    global index_curent

    if not melodii:
        opreste_muzica()
        status.set("PLAYBACK // LIBRARY EMPTY")
        return

    if shuffle_activ:
        optiuni = [
            i for i in range(len(melodii))
            if i != index_curent
        ]

        if not optiuni:
            opreste_muzica()
            status.set("PLAYBACK // END OF LIBRARY")
            return

        index_curent = random.choice(optiuni)

    else:
        if index_curent + 1 >= len(melodii):
            opreste_muzica()
            status.set("PLAYBACK // END OF LIBRARY")
            return

        index_curent += 1

    lista_melodii.selection_clear(0, tk.END)
    lista_melodii.selection_set(index_curent)
    lista_melodii.activate(index_curent)
    reda_muzica()


def reda_anterioara():
    global index_curent

    if not melodii:
        return

    if index_curent <= 0:
        index_curent = 0
    else:
        index_curent -= 1

    lista_melodii.selection_clear(0, tk.END)
    lista_melodii.selection_set(index_curent)
    lista_melodii.activate(index_curent)
    reda_muzica()


def comuta_shuffle():
    global shuffle_activ

    shuffle_activ = not shuffle_activ

    if shuffle_activ:
        buton_shuffle.config(text="SHUFFLE: ON", bg=RED)
        status.set("PLAYBACK // SHUFFLE ENABLED")
    else:
        buton_shuffle.config(text="SHUFFLE: OFF", bg=RED_DARK)
        status.set("PLAYBACK // SEQUENTIAL ORDER")


def schimba_volumul(valoare):
    global volum

    volum = float(valoare) / 100

    if audio_functional:
        pygame.mixer.music.set_volume(volum)


def incepe_cautarea(event=None):
    global utilizator_cauta
    utilizator_cauta = True


def aplica_cautarea(event=None):
    global utilizator_cauta, pozitie_start, moment_start

    utilizator_cauta = False

    if not audio_functional or not redare_activa or durata_curenta <= 0:
        actualizeaza_afisaj_progres()
        return

    tinta = float(bara_progres.get()) / 1000 * durata_curenta
    tinta = max(0.0, min(tinta, durata_curenta))

    try:
        pygame.mixer.music.set_pos(tinta)
        pozitie_start = tinta

        if not este_pauza:
            moment_start = time.monotonic()

        status.set(f"PLAYBACK // SEEK TO {formateaza_timp(tinta)}")

    except (pygame.error, ValueError) as eroare:
        messagebox.showwarning(
            "FSOCIETY",
            "Nu s-a putut schimba poziția în această melodie. "
            "Suportul pentru salt depinde de formatul fișierului."
        )
        print("Eroare la schimbarea poziției:", eroare)

    actualizeaza_afisaj_progres()


def actualizeaza_afisaj_progres():
    pozitie = obtine_pozitia()
    timp_afisat.set(
        f"{formateaza_timp(pozitie)} / "
        f"{formateaza_timp(durata_curenta)}"
    )


def proceseaza_evenimente_audio():
    if audio_functional:
        try:
            for eveniment in pygame.event.get([TRACK_END_EVENT]):
                if redare_activa and not este_pauza:
                    reda_urmatoarea()
        except pygame.error as eroare:
            print("Eroare la procesarea evenimentelor audio:", eroare)

    fereastra.after(UPDATE_INTERVAL, proceseaza_evenimente_audio)


def actualizeaza_timp():
    pozitie = obtine_pozitia()

    timp_afisat.set(
        f"{formateaza_timp(pozitie)} / "
        f"{formateaza_timp(durata_curenta)}"
    )

    if not utilizator_cauta:
        valoare = 0

        if durata_curenta > 0:
            valoare = pozitie / durata_curenta * 1000

        bara_progres.set(max(0, min(1000, valoare)))

    fereastra.after(UPDATE_INTERVAL, actualizeaza_timp)


def sterge_melodia():
    global index_curent, durata_curenta, pozitie_start, moment_start

    selectie = lista_melodii.curselection()

    if not selectie:
        messagebox.showinfo(
            "FSOCIETY",
            "Selectează melodia pe care vrei să o ștergi."
        )
        return

    index = selectie[0]
    nume = os.path.basename(melodii[index])

    if not messagebox.askyesno(
        "DELETE TRACK",
        f"Vrei să elimini „{nume}” din bibliotecă?"
    ):
        return

    if index == index_curent:
        opreste_muzica()
        index_curent = -1
        durata_curenta = 0.0
        pozitie_start = 0.0
        moment_start = 0.0
        titlu_curent.set("NO TRACK SELECTED")
        timp_afisat.set("00:00 / 00:00")
        bara_progres.set(0)
        imagine_coperta.configure(image="")
    elif index < index_curent:
        index_curent -= 1

    melodii.pop(index)
    lista_melodii.delete(index)
    salveaza_melodii()
    status.set(f"SYSTEM // TRACK REMOVED: {nume}")


def reda_selectia(event=None):
    reda_muzica()


def inchide_aplicatia():
    global redare_activa

    redare_activa = False
    salveaza_melodii()

    if audio_functional:
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        pygame.quit()

    fereastra.destroy()


bara_laterala = tk.Frame(fereastra, bg=PANEL, width=210)
bara_laterala.pack(side="left", fill="y")
bara_laterala.pack_propagate(False)

tk.Label(
    bara_laterala,
    text="FSOCIETY",
    bg=PANEL,
    fg=RED,
    font=("Consolas", 22, "bold")
).pack(pady=(30, 5))

tk.Label(
    bara_laterala,
    text="// AUDIO TERMINAL",
    bg=PANEL,
    fg=GREY,
    font=("Consolas", 9)
).pack(pady=(0, 35))


zona_principala = tk.Frame(fereastra, bg=BG)
zona_principala.pack(side="left", fill="both", expand=True)

titlu_pagina = tk.Label(
    zona_principala,
    text="// HOME",
    bg=BG,
    fg=RED,
    font=("Consolas", 16, "bold"),
    anchor="w"
)
titlu_pagina.pack(fill="x", padx=30, pady=(25, 15))

continut_pagina = tk.Frame(zona_principala, bg=BG)
continut_pagina.pack(fill="both", expand=True, padx=30, pady=5)

pagina_home = tk.Frame(continut_pagina, bg=BG)
pagina_now_playing = tk.Frame(continut_pagina, bg=BG)
pagina_library = tk.Frame(continut_pagina, bg=BG)
pagina_playlist = tk.Frame(continut_pagina, bg=BG)


def schimba_pagina(nume):
    pagina_curenta.set(nume)
    titlu_pagina.config(text=f"// {nume}")

    for widget in continut_pagina.winfo_children():
        widget.pack_forget()

    pagini = {
        "HOME": pagina_home,
        "NOW PLAYING": pagina_now_playing,
        "LIBRARY": pagina_library,
        "PLAYLIST": pagina_playlist
    }

    pagini[nume].pack(fill="both", expand=True)


def buton_meniu(text, comanda):
    return tk.Button(
        bara_laterala,
        text=text,
        command=comanda,
        bg=PANEL,
        fg=WHITE,
        activebackground=RED_DARK,
        activeforeground=WHITE,
        font=("Consolas", 11),
        bd=0,
        relief="flat",
        anchor="w",
        padx=25,
        pady=13,
        cursor="hand2"
    )


buton_meniu(" > HOME", lambda: schimba_pagina("HOME")).pack(fill="x")
buton_meniu(" > NOW PLAYING", lambda: schimba_pagina("NOW PLAYING")).pack(fill="x")
buton_meniu(" > LIBRARY", lambda: schimba_pagina("LIBRARY")).pack(fill="x")
buton_meniu(" > PLAYLIST", lambda: schimba_pagina("PLAYLIST")).pack(fill="x")

tk.Label(
    bara_laterala,
    text="STATUS: ONLINE",
    bg=PANEL,
    fg=RED,
    font=("Consolas", 10)
).pack(side="bottom", pady=25)

tk.Label(
    pagina_home,
    text="WELCOME TO FSOCIETY",
    bg=BG,
    fg=WHITE,
    font=("Consolas", 25, "bold")
).pack(anchor="w", pady=(35, 10))

tk.Label(
    pagina_home,
    text="YOUR MUSIC. YOUR SYSTEM. YOUR RULES.",
    bg=BG,
    fg=RED,
    font=("Consolas", 11)
).pack(anchor="w", pady=(0, 35))

tk.Label(
    pagina_home,
    text="> Load your local audio files.\n"
         "> Build your library.\n"
         "> Control playback from one place.",
    bg=BG,
    fg=GREY,
    font=("Consolas", 12),
    justify="left"
).pack(anchor="w", pady=10)

tk.Button(
    pagina_home,
    text="[ + ] ADD MUSIC",
    command=adauga_muzica,
    bg=RED_DARK,
    fg=WHITE,
    activebackground=RED,
    activeforeground=WHITE,
    font=("Consolas", 12, "bold"),
    bd=0,
    padx=20,
    pady=12,
    cursor="hand2"
).pack(anchor="w", pady=25)

tk.Label(
    pagina_now_playing,
    text="CURRENT TRACK",
    bg=BG,
    fg=GREY,
    font=("Consolas", 11)
).pack(anchor="w", pady=(15, 5))

tk.Label(
    pagina_now_playing,
    textvariable=titlu_curent,
    bg=BG,
    fg=RED,
    font=("Consolas", 18, "bold"),
    wraplength=650,
    justify="left"
).pack(anchor="w", pady=10)

imagine_coperta = tk.Label(
    pagina_now_playing,
    bg=PANEL,
    width=220,
    height=220
)
imagine_coperta.pack(anchor="w", pady=10)

tk.Label(
    pagina_now_playing,
    text="Use the controls below to manage playback.",
    bg=BG,
    fg=GREY,
    font=("Consolas", 10)
).pack(anchor="w", pady=5)

tk.Label(
    pagina_library,
    text="YOUR TRACKS",
    bg=BG,
    fg=WHITE,
    font=("Consolas", 15, "bold")
).pack(anchor="w", pady=(10, 12))

lista_melodii = tk.Listbox(
    pagina_library,
    bg=PANEL,
    fg=WHITE,
    selectbackground=RED_DARK,
    selectforeground=WHITE,
    font=("Consolas", 11),
    bd=0,
    highlightthickness=1,
    highlightbackground=RED_DARK,
    activestyle="none"
)
lista_melodii.pack(fill="both", expand=True, pady=(0, 12))
lista_melodii.bind("<Double-Button-1>", reda_selectia)

tk.Button(
    pagina_library,
    text="+ ADD MUSIC",
    command=adauga_muzica,
    bg=RED_DARK,
    fg=WHITE,
    activebackground=RED,
    activeforeground=WHITE,
    font=("Consolas", 10, "bold"),
    bd=0,
    padx=15,
    pady=9,
    cursor="hand2"
).pack(anchor="w", pady=(0, 8))

tk.Button(
    pagina_library,
    text="- DELETE TRACK",
    command=sterge_melodia,
    bg=RED_DARK,
    fg=WHITE,
    activebackground=RED,
    activeforeground=WHITE,
    font=("Consolas", 10, "bold"),
    bd=0,
    padx=15,
    pady=9,
    cursor="hand2"
).pack(anchor="w")

tk.Label(
    pagina_playlist,
    text="CURRENT PLAYLIST",
    bg=BG,
    fg=WHITE,
    font=("Consolas", 15, "bold")
).pack(anchor="w", pady=(10, 12))

tk.Label(
    pagina_playlist,
    text="All tracks added to your library appear here.",
    bg=BG,
    fg=GREY,
    font=("Consolas", 10)
).pack(anchor="w", pady=5)

tk.Button(
    pagina_playlist,
    text="OPEN LIBRARY",
    command=lambda: schimba_pagina("LIBRARY"),
    bg=RED_DARK,
    fg=WHITE,
    activebackground=RED,
    activeforeground=WHITE,
    font=("Consolas", 10, "bold"),
    bd=0,
    padx=15,
    pady=9,
    cursor="hand2"
).pack(anchor="w", pady=15)

bara_player = tk.Frame(zona_principala, bg=PANEL)
bara_player.pack(side="bottom", fill="x", padx=15, pady=15)

tk.Label(
    bara_player,
    textvariable=titlu_curent,
    bg=PANEL,
    fg=WHITE,
    font=("Consolas", 10, "bold"),
    anchor="w"
).pack(fill="x", padx=15, pady=(10, 3))

tk.Label(
    bara_player,
    textvariable=status,
    bg=PANEL,
    fg=RED,
    font=("Consolas", 9),
    anchor="w"
).pack(fill="x", padx=15, pady=(0, 4))

tk.Label(
    bara_player,
    textvariable=timp_afisat,
    bg=PANEL,
    fg=GREY,
    font=("Consolas", 9),
    anchor="w"
).pack(fill="x", padx=15, pady=(2, 0))

bara_progres = tk.Scale(
    bara_player,
    from_=0,
    to=1000,
    orient="horizontal",
    showvalue=False,
    resolution=1,
    bg=PANEL,
    fg=WHITE,
    troughcolor=RED_DARK,
    activebackground=RED,
    highlightthickness=0,
    bd=0,
    sliderlength=14
)
bara_progres.pack(fill="x", padx=15, pady=(0, 5))
bara_progres.bind("<ButtonPress-1>", incepe_cautarea)
bara_progres.bind("<ButtonRelease-1>", aplica_cautarea)

controale = tk.Frame(bara_player, bg=PANEL)
controale.pack(pady=(0, 8))


def buton_player(text, comanda, accent=False):
    return tk.Button(
        controale,
        text=text,
        command=comanda,
        bg=RED_DARK if accent else PANEL,
        fg=WHITE,
        activebackground=RED,
        activeforeground=WHITE,
        font=("Consolas", 10, "bold"),
        bd=0,
        padx=11,
        pady=7,
        cursor="hand2"
    )


buton_player("<<", reda_anterioara).pack(side="left", padx=3)
buton_player("PLAY / PAUSE", pauza_muzica, True).pack(side="left", padx=3)
buton_player("STOP", opreste_muzica).pack(side="left", padx=3)
buton_player(">>", reda_urmatoarea).pack(side="left", padx=3)

buton_shuffle = tk.Button(
    controale,
    text="SHUFFLE: OFF",
    command=comuta_shuffle,
    bg=RED_DARK,
    fg=WHITE,
    activebackground=RED,
    activeforeground=WHITE,
    font=("Consolas", 9, "bold"),
    bd=0,
    padx=10,
    pady=7,
    cursor="hand2"
)
buton_shuffle.pack(side="left", padx=3)

tk.Label(
    controale,
    text="VOL",
    bg=PANEL,
    fg=GREY,
    font=("Consolas", 9)
).pack(side="left", padx=(10, 4))

slider_volum = tk.Scale(
    controale,
    from_=0,
    to=100,
    orient="horizontal",
    command=schimba_volumul,
    bg=PANEL,
    fg=WHITE,
    troughcolor=RED_DARK,
    activebackground=RED,
    highlightthickness=0,
    bd=0,
    length=100
)
slider_volum.set(70)
slider_volum.pack(side="left", padx=3)

melodii = incarca_melodii()

for melodie in melodii:
    lista_melodii.insert(tk.END, os.path.basename(melodie))

if melodii:
    status.set(f"SYSTEM // {len(melodii)} TRACK(S) RESTORED")

schimba_pagina("HOME")
actualizeaza_timp()
proceseaza_evenimente_audio()

fereastra.protocol("WM_DELETE_WINDOW", inchide_aplicatia)
fereastra.mainloop()
