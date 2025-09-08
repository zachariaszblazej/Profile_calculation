import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText


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

        mainframe = ttk.Frame(root, padding='10')
        mainframe.grid(row=0, column=0, sticky='nsew')

        ttk.Label(mainframe, text='Nowy profil [mm]:').grid(row=0, column=0, sticky='w')
        self.profil_var = tk.StringVar(value='6000')
        self.profil_entry = ttk.Entry(mainframe, textvariable=self.profil_var, width=10)
        self.profil_entry.grid(row=0, column=1, sticky='w')

        ttk.Label(mainframe, text='Zapas [mm]:').grid(row=0, column=2, sticky='w')
        self.zapas_var = tk.StringVar(value='0')
        self.zapas_entry = ttk.Entry(mainframe, textvariable=self.zapas_var, width=8)
        self.zapas_entry.grid(row=0, column=3, sticky='w')

        # create 11 pairs of inputs
        self.dlugosci_vars = []
        self.sztuki_vars = []
        for i in range(11):
            r = i + 1
            ttk.Label(mainframe, text=f'Długość {r} [mm]:').grid(row=r, column=0, sticky='w')
            dv = tk.StringVar()
            sv = tk.StringVar()
            self.dlugosci_vars.append(dv)
            self.sztuki_vars.append(sv)
            ttk.Entry(mainframe, textvariable=dv, width=8).grid(row=r, column=1, sticky='w')
            ttk.Label(mainframe, text='Ilość:').grid(row=r, column=2, sticky='w')
            ttk.Entry(mainframe, textvariable=sv, width=6).grid(row=r, column=3, sticky='w')

        btn_frame = ttk.Frame(mainframe)
        btn_frame.grid(row=13, column=0, columnspan=4, pady=(10, 0))

        ttk.Button(btn_frame, text='Tnij profile', command=self.compute).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text='Wyczyść', command=self.clear).grid(row=0, column=1, padx=5)

        self.output = ScrolledText(mainframe, width=70, height=20)
        self.output.grid(row=14, column=0, columnspan=4, pady=(10, 0))

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
        for dv, sv in zip(self.dlugosci_vars, self.sztuki_vars):
            d = dv.get().strip()
            s = sv.get().strip()
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
        for dv, sv in zip(self.dlugosci_vars, self.sztuki_vars):
            dv.set('')
            sv.set('')
        self.output.delete('1.0', tk.END)


def main():
    root = tk.Tk()
    app = ProfileCutterApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
