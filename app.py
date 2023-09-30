from flask import Flask, render_template, request

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("home.html")

@app.route('/licz_profile', methods=['GET', 'POST'])
def licz_profile():
    if request.method == 'POST':
        zapas = int(request.form['zapas'])
        granica = int(request.form['granica'])
        profil= int(request.form['profil'])

        pairs = []

        for x in range(1,11):
            globals()[f'dlugosc{x}'] = request.form[f'dlugosc{x}']

            if globals()[f'dlugosc{x}'] != '':
                globals()[f'dlugosc{x}'] = int(globals()[f'dlugosc{x}'])

            globals()[f'sztuka{x}'] = request.form[f'sztuka{x}']

            if globals()[f'sztuka{x}'] != '':
                globals()[f'sztuka{x}'] = int(globals()[f'sztuka{x}'])

            if globals()[f'sztuka{x}'] != '' and globals()[f'dlugosc{x}'] != '':
                pairs.append((globals()[f'dlugosc{x}'], globals()[f'sztuka{x}']))
        
        dlugosci = [dlugosc for dlugosc, _ in pairs]
        sztuki = [sztuka for _, sztuka in pairs]

        profile_dla_dostawcy, profile_dla_firmy = generuj_profile(dlugosci, sztuki, profil, granica, zapas)

        ilosc_pairs = len(pairs)
            
        return render_template('wyniki.html', zapas=zapas, granica=granica, profil=profil, pairs=pairs, ilosc_pairs=ilosc_pairs, profile_dla_dostawcy=profile_dla_dostawcy, profile_dla_firmy=profile_dla_firmy)

def generuj_profile(dlugosci, sztuki, PROFIL=6000, GRANICA=4000, ZAPAS=20):
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
            # ---------------------CZY TRZEBA WZIĄĆ NOWY PROFIL CZY KORZYSTAĆ Z RESZTY ISTNIEJĄCEGO?--------------------------------#
            if len(pociete_segmenty) > 0:
                reszty = [p['reszta'] for p in pociete_segmenty]
                using_reszta = segment <= max(reszty)

            # ----------------------KORZYSTANIE Z RESZTY----------------------------------------------------------------------------#
            if using_reszta:

                for i in range(len(pociete_segmenty)):
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

            # --------------NOWY PROFIL------------------------------------#
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

    if sum(profile_dla_dostawcy[-1]) != PROFIL:    #zrobione pod granicę 4000 - do zmiany na uniwersalny
        czesc_1, czesc_2 = ostatnia_reszta - GRANICA, GRANICA
        profile_dla_dostawcy[-1][-1] += czesc_1
        profile_dla_dostawcy[-1].append(czesc_2)


    return [profile_dla_dostawcy, pociete_segmenty]