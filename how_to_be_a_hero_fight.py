import sys
import json
import copy
import random
import re
import argparse
import logging

# Funktion zum Parsen der Kommandozeilenargumente
def parse_arguments():
    parser = argparse.ArgumentParser(description="Kampfabwicklung für Rollenspiele")
    parser.add_argument("-i", "--input-file", type=str, default=None, 
                        help="Teams und Charakterattribute aus JSON Input Datei laden")
    parser.add_argument("-o", "--output-file", type=str, default=None, 
                        help="Teams und Charakterattribute nach der Charaktereingabe in eine externe JSON Datei speichern - speichert NICHT das Ergebnis des Kampfes")
    parser.add_argument("-z", "--result-file", type=str, default=None, 
                        help="Teams und Charakterattribute nach Spielzug in eine Datei schreiben. Speichert das Endresultat des Kampfes")
    parser.add_argument("-l", "--log-file", type=str, default=None, 
                        help="Schreibt Nachrichten nicht nur in die Konsole, sondern zusätzlich in eine Logdatei")
    parser.add_argument("-a", "--armor", action="store_true", 
                        help="Aktiviert die Berücksichtigung von Rüstungswerten und -zuständen")
    parser.add_argument("-r", "--break-armor", action="store_true", 
                        help="Rüstungszustand bei kritischen Treffern anpassen")
    parser.add_argument("-d", "--damage-type", action="store_true", 
                        help="Ermöglicht variable Trefferarten (Streiftreffer, Kritischer Treffer)")
    parser.add_argument("-y", "--ammo", action="store_true", 
                        help="Aktiviert die Munitionsverwaltung für Waffen")
    return parser.parse_args()

# Liste zur Speicherung aller Teams
teams = []

# Funktion zur Eingabe eines Charakters
def charakter_eingeben(team_name, break_armor, use_armor, use_ammo):
    print(f"\nCharakter für Team '{team_name}' eingeben:")
    name = input("Name des Charakters: ")
    lebenspunkte = int(input("Lebenspunkte zum Kampfbeginn: "))

    # Rüstungswert Modul https://howtobeahero.de/index.php/R%C3%BCstung
    if use_armor:
        rustungswert = int(input("Rüstungswert (0-9): "))
        while rustungswert < 0 or rustungswert > 9:
            print("Rüstungswert muss zwischen 0 und 9 liegen!")
            rustungswert = int(input("Rüstungswert (0-9): "))
        max_ignorierte_augenpaare = int(input("Maximale Anzahl ignorierter Augenpaare: "))

        # Rüstungszustand
        if break_armor:
            rustungszustand_input = input("Aktueller Rüstungszustand (Enter für Rüstungswert): ")
            rustungszustand = rustungswert if rustungszustand_input == "" else int(rustungszustand_input)
            # Validierung des Rüstungszustands
            while rustungszustand < 0 or rustungszustand > rustungswert:
                rustungszustand = int(input("Aktueller Rüstungszustand (0 bis Rüstungswert): "))
        else:
            rustungszustand = rustungswert  # Immer gleich Rüstungswert, wenn break_armor False ist
    # don't consider armor in damage calculation
    else:
        rustungswert = 0
        rustungszustand = 0
        max_ignorierte_augenpaare = 0

    # Handeln-Wert
    handeln = int(input("Handeln-Wert: "))

    # Parade-Wert (optional, standardmäßig Handeln-Wert)
    parade_input = input("Parade-Wert (Enter für Handeln-Wert): ")
    parade = handeln if parade_input == "" else int(parade_input)

    # NSC-Status
    nsc_input = input("Ist dies ein NSC? (ja/nein): ").lower()
    ist_nsc = True if nsc_input == "ja" else False

    # Bewusstlosigkeit
    bewusstlos_input = input(f"Ist {name} zu Beginn bewusstlos? (ja/nein): ").lower()
    ist_bewusstlos = True if bewusstlos_input == "ja" else False    

    # Waffen
    waffen = []
    if use_ammo:
        while True:
            waffe_hinzufügen = input("Waffe hinzufügen? (ja/nein): ").lower()
            if waffe_hinzufügen != "ja":
                break
            waffen.append(waffe_eingeben())

    return {
        "name": name,
        "lebenspunkte": lebenspunkte,
        "rustungswert": rustungswert,
        "rustungszustand": rustungszustand,
        "max_ignorierte_augenpaare": max_ignorierte_augenpaare,
        "handeln": handeln,
        "parade": parade,
        "waffen": waffen,
        "ist_nsc": ist_nsc,
        "ist_bewusstlos": ist_bewusstlos,
        "ist_tot": False  # Neuer Status: Charakter lebt zu Beginn
    }

# Funktion zur Eingabe einer Waffe
def waffe_eingeben():
    name = input("Name der Waffe: ")
    ort = input("Ort der Waffe (z.B. 'in der Hand', 'Rucksack'): ")
    kaliber = input("Kaliber der Waffe: ")
    schadensformel = input("Schadensformel (z.B. '3W10+2'): ")
    lauf_kapazität = int(input("Maximale Kapazität Patronen im Lauf: "))
    patronen_im_lauf = int(input("Anzahl der Patronen im Lauf: "))
    
    magazine = []
    while True:
        magazin_hinzufügen = input("Magazin hinzufügen? (ja/nein): ").lower()
        if magazin_hinzufügen != "ja":
            break
        magazin_name = input("Name des Magazins: ")
        magazin_ort = input("Ort des Magazins (z.B. 'in Waffe', 'Magazintasche'): ")
        kaliber = input("Kaliber des Magazins: ")
        kapazität = int(input("Kapazität des Magazins: "))
        füllstand = int(input("Aktueller Füllstand: "))
        nachladegeschwindigkeit = int(input("Nachladegeschwindigkeit (Züge): "))
        magazine.append({
            "name": magazin_name,
            "ort": magazin_ort,
            "kaliber": kaliber,
            "kapazität": kapazität,
            "füllstand": füllstand,
            "nachladegeschwindigkeit": nachladegeschwindigkeit
        })
    
    return {
        "name": name,
        "ort": ort,
        "kaliber": kaliber,
        "schadensformel": schadensformel,
        "lauf_kapazität": lauf_kapazität,
        "patronen_im_lauf": patronen_im_lauf,
        "magazine": magazine
    }

# Funktion zur Eingabe eines Teams
def team_eingeben(team_nummer):
    team_name = input(f"\nName für Team {team_nummer + 1} eingeben: ")
    print(f"Team '{team_name}' wird erstellt:")
    team = {"name": team_name, "charaktere": []}
    while True:
        team["charaktere"].append(charakter_eingeben(team_name, break_armor, use_armor, use_ammo))
        noch_einer = input("Weiteren Charakter für dieses Team hinzufügen? (ja/nein): ").lower()
        if noch_einer != "ja":
            break
    return team

# Funktion zum Hinzufügen von Charakteren zu bestehenden Teams
def zusätzliche_charaktere_eingeben():
    for team in teams:
        print(f"\nTeam '{team['name']}':")
        zusatz = input("Möchtest du einen weiteren Charakter zu diesem Team hinzufügen? (ja/nein): ").lower()
        while zusatz == "ja":
            team["charaktere"].append(charakter_eingeben(team["name"], break_armor, use_armor, use_ammo))
            zusatz = input("Möchtest du einen weiteren Charakter zu diesem Team hinzufügen? (ja/nein): ").lower()

# Funktion für die Initiative-Runde mit Rückgabe der Zugreihenfolge und Überraschten
def initiative_runde():
    logging.info(f"=== Initiative-Runde ===")
    
    # Alle Charaktere sammeln
    alle_charaktere = []
    for team in teams:
        for char in team["charaktere"]:
            char["team"] = team["name"]
            alle_charaktere.append(char)
    
    # NSCs nach Handeln-Wert gruppieren
    nsc_gruppen = {}
    spieler_charaktere = []
    for char in alle_charaktere:
        if char["ist_nsc"]:
            handeln = char["handeln"]
            if handeln not in nsc_gruppen:
                nsc_gruppen[handeln] = []
            nsc_gruppen[handeln].append(char)
        else:
            spieler_charaktere.append(char)
    
    # Initiative-Werte und Würfe speichern
    initiative_werte = {}
    wurf_werte = {}
    
    # Würfelproben für NSC-Gruppen
    for handeln, gruppe in nsc_gruppen.items():
        print(f"\nNSC-Gruppe mit Handeln-Wert {handeln}:")
        for char in gruppe:
            print(f"  - {char['name']} (Team: {char['team']})")
        wurf = int(input(f"1W10-Wurf für diese Gruppe eingeben (1-10): "))
        while wurf < 1 or wurf > 10:
            print("Wurf muss zwischen 1 und 10 liegen!")
            wurf = int(input(f"1W10-Wurf für diese Gruppe eingeben (1-10): "))
        for char in gruppe:
            effektiver_wurf = max(0, wurf - char["rustungswert"])
            initiative_werte[char["name"]] = char["handeln"] + effektiver_wurf
            wurf_werte[char["name"]] = (wurf, effektiver_wurf)
    
    # Würfelproben für Spieler-Charaktere
    for char in spieler_charaktere:
        print(f"\nSpieler-Charakter: {char['name']} (Team: {char['team']}, Handeln: {char['handeln']})")
        wurf = int(input(f"1W10-Wurf für {char['name']} eingeben (1-10): "))
        while wurf < 1 or wurf > 10:
            print("Wurf muss zwischen 1 und 10 liegen!")
            wurf = int(input(f"1W10-Wurf für {char['name']} eingeben (1-10): "))
        effektiver_wurf = max(0, wurf - char["rustungswert"])
        initiative_werte[char["name"]] = char["handeln"] + effektiver_wurf
        wurf_werte[char["name"]] = (wurf, effektiver_wurf)
    
    # Zugreihenfolge sortieren
    zugreihenfolge = sorted(
        alle_charaktere,
        key=lambda char: initiative_werte[char["name"]],
        reverse=True
    )
    
    # Zugreihenfolge ausgeben
    logging.info(f"=== Zugreihenfolge ===")
    for i, char in enumerate(zugreihenfolge, 1):
        init_wert = initiative_werte[char["name"]]
        original_wurf, effektiver_wurf = wurf_werte[char["name"]]
        handeln = char["handeln"]
        rustungswert = char["rustungswert"]
        logging.info(f"{i}. {char['name']} (Team: {char['team']}, Initiative: {init_wert} [Wurf: {original_wurf} - Rüstungsmalus: {rustungswert} = {effektiver_wurf} + Handeln: {handeln}], NSC: {'Ja' if char['ist_nsc'] else 'Nein'})")


    # Überraschungsrunde
    logging.info(f"\n=== Überraschungsrunde ===")
    überraschte_charaktere = {}
    for team in teams:
        team_name = team["name"]
        überraschte_charaktere[team_name] = []
        team_überrascht = input(f"Ist Team '{team_name}' überrascht? (ja/nein): ").lower()
        if team_überrascht == "ja":
            for char in team["charaktere"]:
                überraschte_charaktere[team_name].append(char["name"])
        elif len(team["charaktere"]) > 1:
            for char in team["charaktere"]:
                char_überrascht = input(f"Ist {char['name']} (Team: {team_name}) überrascht? (ja/nein): ").lower()
                if char_überrascht == "ja":
                    überraschte_charaktere[team_name].append(char["name"])
    
    # Übersicht der überraschten Charaktere
    logging.info(f"=== Überraschte Charaktere nach Teams ===")
    for team_name, char_list in überraschte_charaktere.items():
        print(f"\nTeam '{team_name}':")
        if char_list:
            for char_name in char_list:
                logging.info(f"  - {char_name}")
        else:
            logging.info(f"  Keine Charaktere überrascht")
    
    return zugreihenfolge, überraschte_charaktere

# Funktion zur Auswahl eines Ziels
def wähle_ziel(teams, eingabe):
    if eingabe == "NIEMAND":
        return None, None
    # Prüfen, ob die Eingabe ein Teamname ist
    for team in teams:
        if team["name"].lower() == eingabe.lower():
            lebende_charaktere = [char for char in team["charaktere"] if not char["ist_tot"]]
            if lebende_charaktere and team["charaktere"]:
                ziel = random.choice(team["charaktere"])
                return ziel["name"], team["name"]
            else:
                logging.info(f"Team '{team['name']}' hat keine (lebenden) Charaktere!")
                return None, None
    # Wenn kein Team, als Charaktername interpretieren
    for team in teams:
        for char in team["charaktere"]:
            if char["name"].lower() == eingabe.lower() and not char["ist_tot"]:
                return char["name"], team["name"]
    logging.info(f"Kein (lebender) Charakter oder Team namens '{eingabe}' gefunden! Bitte erneut versuchen oder 'NIEMAND' eingeben.")
    return None, None

# Funktion zur Ermittlung des Verteidigers
def finde_verteidiger(teams, ziel_name, ziel_team):
    for team in teams:
        if team["name"] == ziel_team:
            for char in team["charaktere"]:
                if char["name"] == ziel_name:
                    return char
    return None

# Funktion zum Parsen der Schadensformel
def parse_schadensformel(formel):
    match = re.match(r"(\d+)W(\d+)(?:\+(\d+))?", formel)
    if not match:
        raise ValueError("Ungültige Schadensformel! Format: z.B. '2W10+5'")
    anzahl_würfel = int(match.group(1))
    würfeltyp = int(match.group(2))
    bonus = int(match.group(3)) if match.group(3) else 0
    return anzahl_würfel, würfeltyp, bonus

# Funktion die prüft, ob alle Spieler tot sind
def alle_spieler_tot(teams):
    for team in teams:
        for char in team["charaktere"]:
            if not char["ist_nsc"] and not char["ist_tot"]:
                return False
    return True

# Funktion die prüft, ob alle NSCs tot sind
def alle_nscs_tot(teams):
    for team in teams:
        for char in team["charaktere"]:
            if char["ist_nsc"] and not char["ist_tot"]:
                return False
    return True

# Ausgabe Spielerstatus nach Kampfende
def finale_ausgabe(teams):
    logging.info(f"Kampf beendet.")
    logging.info(f"=== Finale Übersicht ===")
    for team in teams:
        logging.info(f"\nTeam '{team['name']}':")
        for char in team["charaktere"]:
            status = "tot" if char["ist_tot"] else ("bewusstlos" if char["ist_bewusstlos"] else "bei Bewusstsein")
            logging.info(f"  {char['name']}: {char['lebenspunkte']} Lebenspunkte, {char['rustungszustand']} Rüstungszustand, {status}")

# Aktuelle Charakterwerte nach einem Spielzug in eine Datei schreiben
def save_result(teams, output_path):
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(teams, f, indent=4, ensure_ascii=False)
        logging.info(f"Zwischenstand wurde in '{output_path}' gespeichert.")
    except Exception as e:
        logging.info(f"Fehler beim Speichern der Resultatsdatei: {e}")


# Funktion zur Protokollierung in eine Logdatei
def setup_logging(log_file):
    if log_file:
        # Logging für Datei und Konsole einrichten
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file),  # Schreibt in die Logdatei
                logging.StreamHandler(sys.stdout)  # Schreibt auf die Konsole
            ]
        )
    else:
        # Nur Konsole, wenn kein Logfile angegeben
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)]
        )

# Funktion für die Kampfmechanik
def kampf_runden(zugreihenfolge, überraschte_charaktere, break_armor, damage_type, result_file):
    runde = 1
    while True:
        logging.info(f"\n=== Kampfrunde {runde} ===")
        # Tracking der Paraden pro Runde
        paraden_diese_runde = set()
        
        for char in zugreihenfolge:
            if char["ist_tot"]:
                logging.info(f"{char['name']} ist tot.")
                continue
            if char["ist_bewusstlos"]:
                logging.info(f"{char['name']} ist bewusstlos und kann nicht handeln.")
                continue  # Überspringt den Zug dieses Charakters
            char_name = char["name"]
            team_name = char["team"]
            # Prüfen, ob der Charakter in der ersten Runde überrascht ist
            if runde == 1 and char_name in überraschte_charaktere[team_name]:
                logging.info(f"{char_name} (Team: {team_name}) ist überrascht und setzt diese Runde aus.")
                continue
            
            # Wenn nicht überrascht, normale Zugabfragen
            logging.info(f"\nZug von {char_name} (Team: {team_name}):")
            gelähmt = input("Ist der Spieler diesen Zug gelähmt? (ja/nein): ").lower()
            if gelähmt == "ja":
                logging.info(f"{char_name} ist gelähmt und kann diesen Zug nicht angreifen.")
                continue
            
            # Zielauswahl mit erneuter Abfrage bei ungültigem Ziel
            ziel_name, ziel_team = None, None
            while ziel_name is None and ziel_team is None:
                # Liste aller lebenden Charaktere ausgeben
                print("\nVerfügbare Ziele (lebende Charaktere):")
                for team in teams:
                    for char in team["charaktere"]:
                        if not char["ist_tot"]:
                            print(f"  - {char['name']} (Team: {team['name']}) {char['lebenspunkte']} HP")
                # Auswahl Angriffsziel
                ziel_eingabe = input("Wen möchtest du angreifen? (Charaktername oder Teamname): ")
                ziel_name, ziel_team = wähle_ziel(teams, ziel_eingabe)
                if ziel_name is None and ziel_team is None and ziel_eingabe != "NIEMAND":
                    continue
                break
            
            # Wenn "NIEMAND" eingegeben wurde, wird nicht angegriffen
            if ziel_eingabe == "NIEMAND":
                logging.info(f"{char_name} greift niemanden an.")
                continue
            
            # Angriffsfähigkeit
            print("Hinweis: Wenn die Angriffsfähigkeit nicht geskillt ist, gib den Handeln-Wert ein.")
            angriffsfähigkeit = int(input("Wert der Angriffsfähigkeit eingeben: "))
            
            # Erleichtern
            erleichtern_input = input("Erleichtern (Enter für 0): ")
            erleichtern = int(erleichtern_input) if erleichtern_input else 0
            
            # Würfelprobe (2W10)
            würfelprobe = int(input("Würfelprobe (2W10) eingeben: "))
            zielwert = angriffsfähigkeit + erleichtern
            
            # Erfolgsgrad ermitteln
            prozent = (würfelprobe / zielwert) * 100 if zielwert > 0 else float('inf')
            if prozent >= 110:
                ergebnis = "kritischer Misserfolg"
            elif prozent > 100:
                ergebnis = "Misserfolg"
            elif prozent <= 100 and prozent > 60:
                ergebnis = "normaler Erfolg"
            elif prozent <= 60 and prozent > 30:
                ergebnis = "guter Erfolg"
            elif prozent <= 30 and prozent > 10:
                ergebnis = "sehr guter Erfolg"
            elif prozent <= 10:
                ergebnis = "kritischer Erfolg"
            else:
                ergebnis = "Misserfolg"  # Fallback für edge cases
            
            logging.info(f"{char_name} greift {ziel_name} (Team: {ziel_team}) an: {ergebnis} (Würfelprobe: {würfelprobe}, Zielwert: {zielwert}, {prozent:.1f}%)")
            
            # Parade-Option und Schadensberechnung
            parade_erfolgreich = False
            if ergebnis in ["normaler Erfolg", "guter Erfolg", "sehr guter Erfolg"]:
                verteidiger = finde_verteidiger(teams, ziel_name, ziel_team)
                if verteidiger and ziel_name not in paraden_diese_runde and not verteidiger["ist_bewusstlos"]:
                    parade_versuchen = input(f"Möchte {ziel_name} (Team: {ziel_team}) parieren? (ja/nein): ").lower()
                    if parade_versuchen == "ja":
                        print("Hinweis: Wenn kein spezifischer Paradewert existiert, gib nichts ein, um den Handeln-Wert zu verwenden.")
                        parade_input = input(f"Paradewert von {ziel_name} eingeben (Enter für Handeln-Wert {verteidiger['handeln']}): ")
                        paradewert = verteidiger["handeln"] if parade_input == "" else int(parade_input)
                        
                        parade_erleichter_input = input("Parade erleichtern (Enter für 0): ")
                        parade_erleichter = int(parade_erleichter_input) if parade_erleichter_input else 0
                        
                        parade_würfelprobe = int(input(f"Würfelprobe (2W10) für Parade von {ziel_name} eingeben: "))
                        parade_zielwert = paradewert + parade_erleichter
                        
                        if parade_würfelprobe <= parade_zielwert:
                            logging.info(f"{ziel_name} hat den Angriff erfolgreich pariert! (Würfelprobe: {parade_würfelprobe} ≤ Zielwert: {parade_zielwert})")
                            parade_erfolgreich = True
                        else:
                            logging.info(f"{ziel_name} hat die Parade verfehlt! (Würfelprobe: {parade_würfelprobe} > Zielwert: {parade_zielwert})")
                        paraden_diese_runde.add(ziel_name)  # Parade für diese Runde markieren
                elif ziel_name in paraden_diese_runde:
                    logging.info(f"{ziel_name} hat diese Runde bereits pariert und kann nicht erneut parieren.")
                else:
                    if verteidiger["ist_bewusstlos"]:
                        logging.info(f"{verteidiger['name']} ist bewusstlos und kann nicht parieren.")
                        parade_erfolgreich = False
            
            elif ergebnis == "kritischer Erfolg":
                logging.info("Kritischer Erfolg: Keine Parade möglich!")

            # Schadensberechnung, falls Angriff erfolgreich und nicht pariert
            if ergebnis in ["normaler Erfolg", "guter Erfolg", "sehr guter Erfolg", "kritischer Erfolg"] and not parade_erfolgreich:
                while True:
                    schadensformel = input(f"Schadensformel für {char_name} eingeben (z.B. '2W10+5'): ")
                    try:
                        anzahl_würfel, würfeltyp, schadensbonus = parse_schadensformel(schadensformel)
                        break
                    except ValueError as e:
                        print(e)
                
                # Einzelne Würfel für Schaden eingeben
                while True:
                    print(f"Einzelne Würfel für Schaden von {char_name} eingeben (genau {anzahl_würfel} Werte, max {würfeltyp}):")
                    schadenswürfel_input = input("Würfelwerte (durch Komma getrennt): ")
                    schadenswürfel = [int(w) for w in schadenswürfel_input.split(",")]
                    if len(schadenswürfel) != anzahl_würfel:
                        print(f"Fehler: Du hast {len(schadenswürfel)} Würfel eingegeben, aber {anzahl_würfel} erwartet!")
                        continue
                    if any(w < 1 or w > würfeltyp for w in schadenswürfel):
                        print(f"Fehler: Würfelwerte müssen zwischen 1 und {würfeltyp} liegen!")
                        continue
                    break
                
                # Art des Treffers Modul basierend auf Abstand zwischen Wurfprobe und Fähigkeitswert
                # https://howtobeahero.de/index.php/Kampfsystem_Extension_(Neuzeit)
                if not damage_type:
                    treffer_art = "Normaler Treffer"
                    schaden_faktor = 1.0
                else:
                    abstand = zielwert - würfelprobe
                    if abstand <= 10:
                        treffer_art = "Streiftreffer"
                        schaden_faktor = 0.75
                    elif abstand > 60:
                        treffer_art = "Kritischer Treffer (Durchschuss)"
                        schaden_faktor = 1.15
                    else:
                        treffer_art = "Normaler Treffer"
                        schaden_faktor = 1.0
                
                # Basis-Schaden ohne Rüstung
                base_schaden = sum(schadenswürfel) + schadensbonus
                
                # Verteidiger bestimmen
                verteidiger = finde_verteidiger(teams, ziel_name, ziel_team)
                logging.info(f"Lebenspunkte von {verteidiger['name']} Zu Beginn: {verteidiger['lebenspunkte']}")
                logging.info(f"Rüstungszustand von {verteidiger['name']} Zu Beginn: {verteidiger['rustungszustand']}")
                # Rüstungszustand mildern bei kritischem Erfolg
                if ergebnis == "kritischer Erfolg" and use_armor and break_armor:
                    verteidiger["rustungszustand"] = max(0, verteidiger["rustungszustand"] - 1)
                    logging.info(f"Die Rüstung von {verteidiger['name']} wurde beschädigt! Neuer Rüstungszustand: {verteidiger['rustungszustand']}")
                # Schaden um Rüstungszustand mildern
                if use_armor:
                    rustungswert = verteidiger["rustungswert"]
                    rustungszustand = verteidiger["rustungszustand"]
                    max_ignorierte = verteidiger["max_ignorierte_augenpaare"]
                    
                    ignorierte_würfel = [w for w in schadenswürfel if w <= rustungszustand][:max_ignorierte]
                    effektiver_schaden = sum(w for w in schadenswürfel if w not in ignorierte_würfel) + schadensbonus
                # außer bei Rüstungsmodus aus
                else:
                    effektiver_schaden = base_schaden
                    ignorierte_würfel = []
                finaler_schaden = int(effektiver_schaden * schaden_faktor)
                verteidiger["lebenspunkte"] -= finaler_schaden
                logging.info(f"{verteidiger['name']} hat {verteidiger['lebenspunkte']} Lebenspunkte am Zugende.")
                if use_armor and break_armor:
                    logging.info(f"{verteidiger['name']} hat {verteidiger['rustungszustand']} Rüstungszustand am Zugende.")

                # Überprüfung der Bewusstlosigkeit
                if verteidiger["lebenspunkte"] < 10 or finaler_schaden > 60:
                    verteidiger["ist_bewusstlos"] = True
                    logging.info(f"{verteidiger['name']} ist jetzt bewusstlos!")

                # Überprüfung auf tot
                if verteidiger["lebenspunkte"] <= 0:
                    verteidiger["ist_tot"] = True
                    logging.info(f"{verteidiger['name']} ist gestorben!")

                # Ausgabe mit vollständigem Rechenweg
                logging.info(f"{char_name} verursacht {finaler_schaden} Schaden an {ziel_name} ({treffer_art}):")
                logging.info(f"  Schadensformel: {schadensformel}")
                logging.info(f"  Würfel: {schadenswürfel}")
                if ignorierte_würfel:
                    logging.info(f"  Ignorierte Würfel (Rüstungswert {rustungswert}, max {max_ignorierte}): {ignorierte_würfel}")
                else:
                    logging.info(f"  Keine Würfel ignoriert (Rüstungswert {rustungswert}, max {max_ignorierte})")
                logging.info(f"{char_name} verursacht {finaler_schaden} Schaden an {ziel_name} ({treffer_art}):")
                logging.info(f"  Schadensformel: {schadensformel}")
                logging.info(f"  Würfel: {schadenswürfel}")
                if use_armor:
                    logging.info(f"  Ignorierte Würfel (Rüstungswert {rustungswert}, max {max_ignorierte}): {ignorierte_würfel}")
                logging.info(f"  Effektiver Schaden vor Trefferfaktor: {sum([w for w in schadenswürfel if w not in ignorierte_würfel])} + {schadensbonus} = {effektiver_schaden}")
                logging.info(f"  Trefferfaktor ({treffer_art}, ×{schaden_faktor}): {effektiver_schaden} * {schaden_faktor} = {effektiver_schaden * schaden_faktor:.2f}")
                logging.info(f"  Finaler Schaden: {finaler_schaden} (gerundet)")
                logging.info(f"  Lebenspunkte von {ziel_name} am Zugende: {verteidiger['lebenspunkte']}")
                if use_armor and break_armor:
                    logging.info(f"  Rüstungszustand von {ziel_name} am Zugende: {verteidiger['rustungszustand']}")
                logging.info(f"  Bewusstlos: { 'Ja' if verteidiger['ist_bewusstlos'] else 'Nein' }")
                logging.info(f"  Tot: { 'Ja' if verteidiger['ist_tot'] else 'Nein' }")

                # Ende des Zuges
                ## Aktuellen Stand in Resultatsdatei schreiben
                if result_file:
                    save_result(teams, result_file)
                ## Option zum Beenden des Kampfes anzeigen, wenn eine Spielergruppe tot
                if alle_spieler_tot(teams):
                    print("Alle Spielercharaktere sind tot. Möchtest du den Kampf beenden?")
                    beenden = input("(ja/nein): ").lower()
                    if beenden == "ja":
                        finale_ausgabe(teams)
                        break
                elif alle_nscs_tot(teams):
                    print("Alle Nichtspielercharaktere sind tot. Möchtest du den Kampf beenden?")
                    beenden = input("(ja/nein): ").lower()
                    if beenden == "ja":
                        finale_ausgabe(teams)
                        break
        
        # Nächste Runde oder Kampf beenden
        weitere_runde = input("\nWeitere Runde spielen? (ja/nein): ").lower()
        if weitere_runde != "ja":
            finale_ausgabe(teams)
            break
        runde += 1
        paraden_diese_runde.clear()  # Zurücksetzen der Paraden für die nächste Runde

# Kommandozeilen-Parameter verarbeiten
input_file = None
output_file = None

if not input_file and not output_file:
    print("Hinweis: Mit '-i <Dateipfad>' kannst du Teams aus einer Datei laden.")
    print("         Mit '-o <Dateipfad>' kannst du die Teams in eine Datei speichern.")

args = parse_arguments()
use_armor = args.armor
break_armor = args.break_armor
damage_type = args.damage_type
input_file = args.input_file
output_file = args.output_file
result_file = args.result_file
use_ammo = args.ammo
setup_logging(args.log_file)
logging.info("Programm gestartet.")

# Ursprüngliche Teams für Vergleich speichern (falls -i und -o kombiniert)
original_teams = None

# Teams laden oder neu erstellen
if input_file:
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            teams = json.load(f)
            original_teams = copy.deepcopy(teams)
        logging.info(f"Teams aus '{input_file}' geladen.")
        
        logging.info("\n=== Übersicht aller Teams ===")
        for team in teams:
            logging.info(f"\nTeam '{team['name']}':")
            for char in team["charaktere"]:
                logging.info(f"  Name: {char['name']}")
                logging.info(f"  Lebenspunkte: {char['lebenspunkte']}")
                if use_armor:
                    logging.info(f"  Rüstungswert: {char['rustungswert']}")
                    logging.info(f"  Max. ignorierte Augenpaare: {char['max_ignorierte_augenpaare']}")
                    logging.info(f"  Rüstungszustand: {char['rustungszustand']}")
                if use_ammo:
                    logging.info(f"  Waffen: {char['waffen']}")
                logging.info(f"  Handeln: {char['handeln']}")
                logging.info(f"  Parade: {char['parade']}")
                logging.info(f"  NSC: {'Ja' if char['ist_nsc'] else 'Nein'}")
                logging.info(f"  Bewusstlos: { 'Ja' if char['ist_bewusstlos'] else 'Nein' }")
                print("  ---")
        
        zusatz = input("\nMöchtest du manuell weitere Charaktere hinzufügen? (ja/nein): ").lower()
        if zusatz == "ja":
            zusätzliche_charaktere_eingeben()
    except FileNotFoundError:
        logging.info(f"Fehler: Datei '{input_file}' nicht gefunden. Programm wird beendet.")
        sys.exit(1)
    except json.JSONDecodeError:
        logging.info(f"Fehler: '{input_file}' enthält kein gültiges JSON. Programm wird beendet.")
        sys.exit(1)
else:
    anzahl_teams = int(input("Wie viele Teams sollen erstellt werden? "))
    for i in range(anzahl_teams):
        teams.append(team_eingeben(i))

# Übersicht anzeigen (falls nicht schon durch -i geschehen)
if not input_file:
    print("\n=== Übersicht aller Teams ===")
    for team in teams:
        logging.info(f"\nTeam '{team['name']}':")
        for char in team["charaktere"]:
            logging.info(f"  Name: {char['name']}")
            logging.info(f"  Lebenspunkte: {char['lebenspunkte']}")
            if use_armor:
                logging.info(f"  Rüstungswert: {char['rustungswert']}")
                logging.info(f"  Rüstungszustand: {char['rustungszustand']}")
                logging.info(f"  Max. ignorierte Augenpaare: {char['max_ignorierte_augenpaare']}")
            logging.info(f"  Handeln: {char['handeln']}")
            logging.info(f"  Parade: {char['parade']}")
            logging.info(f"  NSC: {'Ja' if char['ist_nsc'] else 'Nein'}")
            print("  ---")

# Bestätigung abfragen
zufrieden = input("\nBist du mit deiner Eingabe zufrieden? (ja/nein): ").lower()
if zufrieden == "ja":
    print("Eingabe bestätigt.")
    
    if output_file:
        if input_file and original_teams != teams:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(teams, f, indent=4, ensure_ascii=False)
            logging.info(f"Teams wurden in '{output_file}' gespeichert (Änderungen gegenüber '{input_file}' erkannt).")
        elif not input_file:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(teams, f, indent=4, ensure_ascii=False)
            logging.info(f"Teams wurden in '{output_file}' gespeichert.")
        else:
            logging.info(f"Keine Änderungen gegenüber '{input_file}'. Keine neue Datei erstellt.")
    
    # Initiative-Runde durchführen und Kampf starten
    zugreihenfolge, überraschte_charaktere = initiative_runde()
    kampf_runden(zugreihenfolge, überraschte_charaktere, break_armor, damage_type, result_file)
else:
    print("Eingabe abgebrochen. Bitte starte das Programm neu, um es nochmal zu versuchen.")