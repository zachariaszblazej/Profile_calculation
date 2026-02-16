import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
import os
import sys
import platform
import tempfile
import subprocess



def generuj_profile(dlugosci, sztuki, PROFIL=6000, GRANICA=6000, ZAPAS=0):
    dlugosci = [x + ZAPAS for x in dlugosci]

    pociete_segmenty = []
    times = len(dlugosci)

    for i in range(times):

        segment = max(dlugosci)
        idx = dlugosci.index(segment)
        ilosc_sztuk = sztuki[idx]
        do_obciecia = segment * ilosc_sztuk

        while ilosc_sztuk > 0:
            nowy_profil = {}
            modyfikowany_profil = {}
            ilosc_ciecia = 0
            using_reszta = False
            # use existing leftover if possible
            if len(pociete_segmenty) > 0:
                reszty = [p['reszta'] for p in pociete_segmenty]
                using_reszta = segment <= max(reszty)

            if using_reszta:
                for j in range(len(pociete_segmenty)):
                    try:
                        optymalna_reszta = max(reszty)
                    except ValueError:
                        continue
                    index_opt_reszty = reszty.index(optymalna_reszta)

                    while segment <= optymalna_reszta and ilosc_sztuk > 0:
                        do_obciecia -= segment
                        optymalna_reszta -= segment
                        modyfikowany_profil = pociete_segmenty[index_opt_reszty]
                        modyfikowany_profil['segmenty'].append(segment)
                        modyfikowany_profil['reszta'] = optymalna_reszta
                        reszty = [p['reszta'] for p in pociete_segmenty]
                        ilosc_sztuk -= 1

            else:
                do_obciecia = segment * ilosc_sztuk
                obcinane = do_obciecia
                while obcinane > PROFIL:
                    obcinane -= segment

                ilosc_ciecia = obcinane // segment
                ilosc_sztuk -= ilosc_ciecia

                schemat_pociecia = [segment for x in range(ilosc_ciecia)]
                reszta_profilu = PROFIL - obcinane

                nowy_profil = {'segmenty': schemat_pociecia, 'reszta': reszta_profilu}
                pociete_segmenty.append(nowy_profil)

        dlugosci.remove(segment)
        sztuki.remove(sztuki[idx])

    ostatni_profil = pociete_segmenty[-1]
    dlugosci_ostatniego_profilu = ostatni_profil['segmenty']
    profile_z_nieakceptowalna_reszta = [p for p in pociete_segmenty[:-1] if p['reszta'] >= min(dlugosci_ostatniego_profilu)]
    if len(profile_z_nieakceptowalna_reszta) > 0:

        for p in profile_z_nieakceptowalna_reszta:
           if p['reszta'] >= min(dlugosci_ostatniego_profilu):
               dlugosci_mozliwe_do_transferu = [d for d in dlugosci_ostatniego_profilu if d <= p['reszta']]
               segment_do_transferu = max(dlugosci_mozliwe_do_transferu)

               p['segmenty'].append(segment_do_transferu)
               p['reszta'] -= segment_do_transferu
               p['segmenty'].sort(reverse=True)

               ostatni_profil['segmenty'].remove(segment_do_transferu)
               ostatni_profil['reszta'] += segment_do_transferu

    calkowite_profile = []
    for p in pociete_segmenty:
       profil = [s for s in p['segmenty']]
       profil.append(p['reszta'])
       calkowite_profile.append(profil)

    profile_dla_dostawcy = []

    for p in calkowite_profile:
        profil_dla_dostawcy = []
        segment_dostawczy = 0
        for i, s in enumerate(p):
            proba = segment_dostawczy + s
            if proba < GRANICA:
                segment_dostawczy = proba
                if i == len(p) - 1:
                    profil_dla_dostawcy.append(segment_dostawczy)
            else:
                profil_dla_dostawcy.append(segment_dostawczy)
                segment_dostawczy = s

        profile_dla_dostawcy.append(profil_dla_dostawcy)

    ostatnia_reszta = calkowite_profile[-1][-1]

    if sum(profile_dla_dostawcy[-1]) != PROFIL:
        czesc_1, czesc_2 = ostatnia_reszta - GRANICA, GRANICA
        profile_dla_dostawcy[-1][-1] += czesc_1
        profile_dla_dostawcy[-1].append(czesc_2)

    return [profile_dla_dostawcy, pociete_segmenty]


class ProfileCutterApp:
    def __init__(self, root):
        self.root = root
        root.title('Tnij profile - aplikacja desktop')

        # Input widgets
        pad_y = 2
        ttk.Label(root, text='Nowy profil [mm]:').grid(row=0, column=0, sticky='w', padx=10, pady=pad_y)
        self.profil_var = tk.StringVar(value='6000')
        self.profil_entry = ttk.Entry(root, textvariable=self.profil_var, width=10)
        self.profil_entry.grid(row=0, column=1, sticky='w', pady=pad_y)

        ttk.Label(root, text='Zapas [mm]:').grid(row=0, column=2, sticky='w', padx=(20, 0), pady=pad_y)
        self.zapas_var = tk.StringVar(value='0')
        self.zapas_entry = ttk.Entry(root, textvariable=self.zapas_var, width=8)
        self.zapas_entry.grid(row=0, column=3, sticky='w', pady=pad_y)

        # --- Dynamiczna lista pozycji (długość + ilość) ---
        self.rows = []  # lista dict: {'frame', 'dv', 'sv', 'widgets'}

        # Kontener ze scrollem na wiersze pozycji
        self.rows_canvas = tk.Canvas(root, highlightthickness=0, height=200)
        self.rows_scrollbar = ttk.Scrollbar(root, orient='vertical', command=self.rows_canvas.yview)
        self.rows_inner = ttk.Frame(self.rows_canvas)

        self.rows_inner.bind('<Configure>', lambda e: self.rows_canvas.configure(scrollregion=self.rows_canvas.bbox('all')))
        self.rows_canvas_window = self.rows_canvas.create_window((0, 0), window=self.rows_inner, anchor='nw')
        self.rows_canvas.configure(yscrollcommand=self.rows_scrollbar.set)

        self.rows_canvas.grid(row=1, column=0, columnspan=4, sticky='nsew', padx=10, pady=pad_y)
        self.rows_scrollbar.grid(row=1, column=4, sticky='ns', pady=pad_y)

        # Scroll myszką
        def _on_mousewheel(event):
            self.rows_canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
        self.rows_canvas.bind_all('<MouseWheel>', _on_mousewheel)

        # Rozciągnij canvas gdy okno się poszerzy
        self.rows_canvas.bind('<Configure>', lambda e: self.rows_canvas.itemconfig(self.rows_canvas_window, width=e.width))

        # Przycisk „+" do dodawania pozycji
        btn_frame = ttk.Frame(root)
        btn_frame.grid(row=2, column=0, columnspan=4, sticky='w', padx=10, pady=(2, 4))
        self.btn_add_row = ttk.Button(btn_frame, text='+ Dodaj pozycję', command=self.add_row)
        self.btn_add_row.pack(side='left')

        # Dodaj 3 startowe wiersze
        for _ in range(3):
            self.add_row()

        self.btn_cut = ttk.Button(root, text='Tnij profile', command=self.compute)
        self.btn_cut.grid(row=3, column=0, padx=10, pady=(10, 4), sticky='w')
        self.btn_clear = ttk.Button(root, text='Wyczyść', command=self.clear)
        self.btn_clear.grid(row=3, column=1, padx=10, pady=(10, 4), sticky='w')

        self.output = ScrolledText(root, width=70, height=18)
        self.output.grid(row=4, column=0, columnspan=5, padx=10, pady=(10, 10), sticky='nsew')

        # Przyciski pod outputem
        self.btn_print = ttk.Button(root, text='Drukuj', command=self.print_output)
        self.btn_print.grid(row=5, column=0, padx=10, pady=(0, 12), sticky='w')

        # Grid weight to let text expand
        root.grid_rowconfigure(1, weight=0)
        root.grid_rowconfigure(4, weight=1)
        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=1)
        root.grid_columnconfigure(2, weight=1)
        root.grid_columnconfigure(3, weight=1)

        # Ustaw tło (jeśli istnieje) za wszystkimi kontrolkami
        if hasattr(self, '_bg_label'):
            try:
                self._bg_label.lower()
            except Exception:
                pass  # ignoruj jeśli środowisko nie wspiera

    # Bind background resize only
    # (already bound in background loading if Pillow succeeded)

    def add_row(self):
        """Dodaje nowy wiersz (Długość + Ilość + przycisk −) do listy pozycji."""
        idx = len(self.rows) + 1
        row_frame = ttk.Frame(self.rows_inner)
        row_frame.pack(fill='x', pady=1)

        lbl = ttk.Label(row_frame, text=f'Długość {idx} [mm]:')
        lbl.pack(side='left', padx=(0, 4))

        dv = tk.StringVar()
        e_d = ttk.Entry(row_frame, textvariable=dv, width=8)
        e_d.pack(side='left', padx=(0, 8))

        lbl2 = ttk.Label(row_frame, text='Ilość:')
        lbl2.pack(side='left', padx=(0, 4))

        sv = tk.StringVar()
        e_s = ttk.Entry(row_frame, textvariable=sv, width=6)
        e_s.pack(side='left', padx=(0, 8))

        row_data = {'frame': row_frame, 'dv': dv, 'sv': sv, 'lbl': lbl}

        btn_remove = ttk.Button(row_frame, text='−', width=3,
                                command=lambda rd=row_data: self.remove_row(rd))
        btn_remove.pack(side='left', padx=(4, 0))
        row_data['btn_remove'] = btn_remove

        self.rows.append(row_data)
        # Przewiń na dół po dodaniu
        self.rows_canvas.update_idletasks()
        self.rows_canvas.yview_moveto(1.0)

    def remove_row(self, row_data):
        """Usuwa wiersz pozycji z listy."""
        if row_data in self.rows:
            self.rows.remove(row_data)
            row_data['frame'].destroy()
            # Przenumeruj etykiety
            for i, rd in enumerate(self.rows, start=1):
                rd['lbl'].configure(text=f'Długość {i} [mm]:')

    def _on_resize_bg(self, event):
        if not self._bg_orig:
            return
        try:
            from PIL import Image, ImageTk
            w = max(50, event.width)
            h = max(50, event.height)
            resized = self._bg_orig.resize((w, h), Image.LANCZOS)
            self._bg_image = ImageTk.PhotoImage(resized)
            self._bg_label.configure(image=self._bg_image)
        except Exception:
            pass

    # Removed overlay panel logic per user request (overlay deleted)


    def compute(self):
        try:
            profil = int(self.profil_var.get())
        except Exception:
            messagebox.showerror('Błąd', 'Niepoprawna wartość pola Nowy profil')
            return

        try:
            zapas = int(self.zapas_var.get())
        except Exception:
            messagebox.showerror('Błąd', 'Niepoprawna wartość pola Zapas')
            return

        dlugosci = []
        sztuki = []
        for rd in self.rows:
            d = rd['dv'].get().strip()
            s = rd['sv'].get().strip()
            if d != '' and s != '':
                try:
                    di = int(d)
                    si = int(s)
                except ValueError:
                    messagebox.showerror('Błąd', f'Niepoprawne dane: {d} / {s}')
                    return
                dlugosci.append(di)
                sztuki.append(si)

        if not dlugosci:
            messagebox.showinfo('Brak', 'Brak danych do obliczeń')
            return

        # Uwaga: generuj_profile mutuje przekazane listy (usuwa elementy),
        # dlatego przekazujemy kopie aby zachować oryginalne do wyświetlenia w sekcji "Zlecenie".
        profile_dla_dostawcy, profile_dla_firmy = generuj_profile(dlugosci.copy(), sztuki.copy(), profil, profil, zapas)

        self.output.delete('1.0', tk.END)
        self.output.insert(tk.END, f'Wyniki dla profili o długości {profil} mm\n\nKażde cięcie zabiera {zapas} mm materiału.\n\n')
        self.output.insert(tk.END, 'Zlecenie:\n')
        for d, s in zip(dlugosci, sztuki):
            self.output.insert(tk.END, f'  {s} x {d} mm\n')

        self.output.insert(tk.END, '\nProfile dla firmy:\n')
        for idx, p in enumerate(profile_dla_firmy, start=1):
            # W wyjściu pokazujemy oryginalne długości (bez dodanego zapasu),
            # bo zapas jest już opisany tekstowo powyżej.
            segs = ', '.join(str(x - zapas) for x in p['segmenty']) if zapas else ', '.join(str(x) for x in p['segmenty'])
            res = p['reszta']
            self.output.insert(tk.END, f'  {idx}) Segmenty: {segs} | Reszta: {res}\n')

    def clear(self):
        self.profil_var.set('6000')
        self.zapas_var.set('0')
        for rd in self.rows:
            rd['dv'].set('')
            rd['sv'].set('')
        self.output.delete('1.0', tk.END)

    def print_output(self):
        """Po kliknięciu 'Drukuj' na Windows:
        - Otwórz Notatnik (nowy, pusty dokument),
        - Wklej zawartość outputu do dokumentu.

        Na innych systemach: spróbuj 'lpr', w przeciwnym razie zaproponuj zapis do pliku.
        """
        content = self.output.get('1.0', tk.END).strip()
        if not content:
            messagebox.showinfo('Brak danych', 'Brak treści do wydruku.')
            return

        system = platform.system().lower()
        try:
            if system.startswith('win'):
                try:
                    # Szybkie rozwiązanie: użyj schowka + Ctrl+V (działa na Win10 i Win11)
                    from pywinauto import Application
                    from pywinauto.keyboard import send_keys
                    import time

                    # Skopiuj zawartość do schowka systemowego
                    self.root.clipboard_clear()
                    self.root.clipboard_append(content)
                    self.root.update()  # flush clipboard

                    # Uruchom Notepad JEDEN raz
                    proc = subprocess.Popen(["notepad.exe"])
                    time.sleep(0.3)  # krótki delay na start procesu

                    # Znajdź okno Notatnika po klasie (niezależnie od języka i wersji Windows)
                    app = Application(backend="uia").connect(process=proc.pid, timeout=5)
                    dlg = app.window(class_name="Notepad")
                    dlg.wait('visible', timeout=5)
                    dlg.set_focus()

                    # Wklej z schowka (natychmiastowe)
                    send_keys('^v')
                    return
                except Exception:
                    # Jeśli automatyzacja zawiedzie, fallback: otwórz Notatnik z plikiem tymczasowym
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w', encoding='utf-8') as tf:
                            tf.write(content)
                            temp_path = tf.name
                        subprocess.Popen(["notepad.exe", temp_path])
                    except Exception as e2:
                        messagebox.showerror('Błąd', f'Nie udało się otworzyć Notatnika: {e2}')
            else:
                # macOS / Linux: użyj lpr jeśli dostępne
                with subprocess.Popen(['which', 'lpr'], stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
                    out, _ = proc.communicate(timeout=2)
                if out.strip():
                    try:
                        lp = subprocess.Popen(['lpr'], stdin=subprocess.PIPE)
                        lp.communicate(input=content.encode('utf-8'), timeout=5)
                        if lp.returncode == 0:
                            messagebox.showinfo('Drukowanie', 'Wysłano do drukarki (lpr).')
                            return
                    except Exception:
                        pass
                # Fallback: zapisz do pliku
                save_path = filedialog.asksaveasfilename(title='Zapisz do pliku aby wydrukować ręcznie', defaultextension='.txt', filetypes=[('Plik tekstowy', '*.txt'), ('Wszystkie pliki', '*.*')])
                if save_path:
                    try:
                        with open(save_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        messagebox.showinfo('Zapisano', f'Zapisano do: {save_path}\nMożesz wydrukować plik ręcznie.')
                    except Exception as e:
                        messagebox.showerror('Błąd', f'Nie udało się zapisać pliku: {e}')
                else:
                    messagebox.showinfo('Anulowano', 'Drukowanie anulowane.')
        except Exception as e:
            messagebox.showerror('Błąd', f'Problem podczas przygotowania wydruku: {e}')


def main():
    root = tk.Tk()
    # Set a minimum size so background displays nicely
    app = ProfileCutterApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
