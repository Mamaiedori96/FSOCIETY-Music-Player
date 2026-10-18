
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import pygame




BG = "#080808"
PANEL = "#151515"
RED = "#ff2020"
RED_DARK = "#8f0000"
WHITE = "#eeeeee"
GREY = "#999999"

fereastra = tk.Tk()
fereastra.title("FSOCIETY // MUSIC PLAYER")
fereastra.geometry("1000x650")
fereastra.minsize(850, 550)
fereastra.configure(bg=BG)

try:
    pygame.mixer.init()
    audio_functional = True
except pygame.error as eroare:
    audio_functional = False
    print("Eroare audio:", eroare)




melodii = []
index_curent = -1
este_pauza = False
volum = 0.7

titlu_curent = tk.StringVar(value="NO TRACK SELECTED")
status = tk.StringVar(value="SYSTEM READY // WAITING FOR INPUT")
pagina_curenta = tk.StringVar(value="HOME")




def actualizeaza_titlu():
    if 0 <= index_curent < len(melodii):
        nume = os.path.basename(melodii[index_curent])
        titlu_curent.set(nume)
        status.set(f"NOW PLAYING // {index_curent + 1}/{len(melodii)}")
    else:
        titlu_curent.set("NO TRACK SELECTED")
        status.set("SYSTEM READY // WAITING FOR INPUT")


def adauga_muzica():
    fisiere = filedialog.askopenfilenames(
        title="Selecteaza melodiile",
        filetypes=[
            ("Fisiere audio", "*.mp3 *.wav *.ogg"),
            ("Toate fisierele", "*.*")
        ]
    )

    adaugate = 0

    for fisier in fisiere:
        if fisier not in melodii:
            melodii.append(fisier)
            lista_melodii.insert(tk.END, os.path.basename(fisier))
            adaugate += 1

    if adaugate:
        status.set(f"SYSTEM // {adaugate} TRACK(S) ADDED")
        if index_curent == -1:
            status.set(f"SYSTEM // {len(melodii)} TRACK(S) LOADED")


def reda_muzica():
    global index_curent, este_pauza

    if not audio_functional:
        messagebox.showerror(
            "Audio error",
            "Sistemul audio nu a putut fi initializat. "
            "Verifica instalarea pygame-ce."
        )
        return

    selectie = lista_melodii.curselection()

    if selectie:
        index_curent = selectie[0]
    elif index_curent == -1 and melodii:
        index_curent = 0

    if not melodii or index_curent < 0:
        messagebox.showinfo("FSOCIETY", "Adauga mai intai o melodie.")
        return

    try:
        pygame.mixer.music.load(melodii[index_curent])
        pygame.mixer.music.set_volume(volum)
        pygame.mixer.music.play()
        este_pauza = False

        lista_melodii.selection_clear(0, tk.END)
        lista_melodii.selection_set(index_curent)
        lista_melodii.activate(index_curent)

        actualizeaza_titlu()

    except pygame.error as eroare:
        messagebox.showerror(
            "Playback error",
            f"Melodia nu a putut fi redata:\n{eroare}"
        )


def pauza_muzica():
    global este_pauza

    if not audio_functional:
        return

    if este_pauza:
        pygame.mixer.music.unpause()
        este_pauza = False
        status.set("PLAYBACK // RESUMED")
    elif pygame.mixer.music.get_busy():
        pygame.mixer.music.pause()
        este_pauza = True
        status.set("PLAYBACK // PAUSED")
    else:
        reda_muzica()


def opreste_muzica():
    global este_pauza

    if audio_functional:
        pygame.mixer.music.stop()

    este_pauza = False
    status.set("PLAYBACK // STOPPED")


def reda_urmatoarea():
    global index_curent, este_pauza

    if not melodii:
        return

    index_curent = (index_curent + 1) % len(melodii)
    este_pauza = False
    reda_muzica()


def reda_anterioara():
    global index_curent, este_pauza

    if not melodii:
        return

    index_curent = (index_curent - 1) % len(melodii)
    este_pauza = False
    reda_muzica()


def schimba_volumul(valoare):
    global volum

    volum = float(valoare) / 100

    if audio_functional:
        pygame.mixer.music.set_volume(volum)


def reda_selectia(event=None):
    reda_muzica()


def inchide_aplicatia():
    if audio_functional:
        pygame.mixer.music.stop()
        pygame.mixer.quit()

    fereastra.destroy()




bara_laterala = tk.Frame(fereastra, bg=PANEL, width=210)
bara_laterala.pack(side="left", fill="y")
bara_laterala.pack_propagate(False)

logo = tk.Label(
    bara_laterala,
    text="FSOCIETY",
    bg=PANEL,
    fg=RED,
    font=("Consolas", 22, "bold")
)
logo.pack(pady=(30, 5))

sub_logo = tk.Label(
    bara_laterala,
    text="// AUDIO TERMINAL",
    bg=PANEL,
    fg=GREY,
    font=("Consolas", 9)
)
sub_logo.pack(pady=(0, 35))


def schimba_pagina(nume):
    pagina_curenta.set(nume)
    titlu_pagina.config(text=f"// {nume}")

    for widget in continut_pagina.winfo_children():
        widget.pack_forget()

    if nume == "HOME":
        pagina_home.pack(fill="both", expand=True)
    elif nume == "NOW PLAYING":
        pagina_now_playing.pack(fill="both", expand=True)
    elif nume == "LIBRARY":
        pagina_library.pack(fill="both", expand=True)
    elif nume == "PLAYLIST":
        pagina_playlist.pack(fill="both", expand=True)


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
buton_meniu(
    " > NOW PLAYING",
    lambda: schimba_pagina("NOW PLAYING")
).pack(fill="x")
buton_meniu(" > LIBRARY", lambda: schimba_pagina("LIBRARY")).pack(fill="x")
buton_meniu(" > PLAYLIST", lambda: schimba_pagina("PLAYLIST")).pack(fill="x")

tk.Label(
    bara_laterala,
    text="STATUS: ONLINE",
    bg=PANEL,
    fg=RED,
    font=("Consolas", 10)
).pack(side="bottom", pady=25)




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
).pack(anchor="w", pady=(40, 15))

tk.Label(
    pagina_now_playing,
    textvariable=titlu_curent,
    bg=BG,
    fg=RED,
    font=("Consolas", 18, "bold"),
    wraplength=650,
    justify="left"
).pack(anchor="w", pady=10)

tk.Label(
    pagina_now_playing,
    text="Use the controls below to manage playback.",
    bg=BG,
    fg=GREY,
    font=("Consolas", 10)
).pack(anchor="w", pady=10)




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
).pack(fill="x", padx=15, pady=(12, 3))

tk.Label(
    bara_player,
    textvariable=status,
    bg=PANEL,
    fg=RED,
    font=("Consolas", 9),
    anchor="w"
).pack(fill="x", padx=15, pady=(0, 8))

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
        font=("Consolas", 11, "bold"),
        bd=0,
        padx=14,
        pady=7,
        cursor="hand2"
    )


buton_player("<<", reda_anterioara).pack(side="left", padx=4)
buton_player("PLAY / PAUSE", pauza_muzica, True).pack(side="left", padx=4)
buton_player("STOP", opreste_muzica).pack(side="left", padx=4)
buton_player(">>", reda_urmatoarea).pack(side="left", padx=4)

tk.Label(
    controale,
    text="VOL",
    bg=PANEL,
    fg=GREY,
    font=("Consolas", 9)
).pack(side="left", padx=(15, 4))

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
    length=120
)
slider_volum.set(70)
slider_volum.pack(side="left", padx=4)




schimba_pagina("HOME")
fereastra.protocol("WM_DELETE_WINDOW", inchide_aplicatia)
fereastra.mainloop()
