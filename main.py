import clingo
import re
import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLabel,
    QListWidget, QPushButton, QWidget, QHBoxLayout, QStackedWidget, QGridLayout
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class Sokoban(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cesta_suboru = None
        self.mapa_data = []
        self.pociatocna_pozicia = None
        self.mapa_solved = []
        self.mapa_solved_odpad = {}
        self.init_ui()

    def mapa_do_asp(self):
        asp_fakty = []
        with open(self.cesta_suboru, 'r') as file:
            self.mapa_data = file.readlines()
        for y, riadok in enumerate(self.mapa_data):
            for x, znak in enumerate(riadok):
                if znak == '#':
                    asp_fakty.append(f"wall({x},{y}).")
                elif znak == 'C':
                    asp_fakty.append(f"crate(0, {x},{y}).")
                elif znak == 'X':
                    asp_fakty.append(f"storage({x},{y}).")
                elif znak == 'S':
                    asp_fakty.append(f"move(0, {x},{y}).")
                    self.pociatocna_pozicia = (x, y)
                elif znak == 's':
                    asp_fakty.append(f"move(0, {x},{y}).")
                    asp_fakty.append(f"storage({x},{y}).")
                    self.pociatocna_pozicia = (x, y)
                elif znak == 'c':
                    asp_fakty.append(f"crate(0, {x},{y}).")
                    asp_fakty.append(f"storage({x},{y}).")
        return '\n'.join(asp_fakty)

    def vykresli_mapu(self, riesenie):
        walls = set()
        crates = {}
        crates_odpad = {}
        move_odpad = {}
        storages = set()
        sokoban = None
        max_time = 0
        for fakt in riesenie:
            match = re.match(r"(move|crate|push)\((\d+),", fakt)
            if match:
                t = int(match.group(2))
                crates_odpad[t] = []
                move_odpad[t] = []
                if t > max_time:
                    max_time = t
        for fakt in riesenie:
            if fakt.startswith("wall"):
                match = re.match(r"wall\((\d+),(\d+)\)", fakt)
                if match:
                    x, y = map(int, match.groups())
                    walls.add((x, y))
            elif fakt.startswith("crate"):
                match = re.match(r"crate\((\d+),(\d+),(\d+)\)", fakt)
                if match:
                    t, x, y = map(int, match.groups())
                    crates_odpad[t].append((x, y))
                    if t == max_time:
                        crates[(x, y)] = t
            elif fakt.startswith("storage"):
                match = re.match(r"storage\((\d+),(\d+)\)", fakt)
                if match:
                    x, y = map(int, match.groups())
                    storages.add((x, y))
            elif fakt.startswith("move"):
                match = re.match(r"move\((\d+),(\d+),(\d+)\)", fakt)
                if match:
                    t, x, y = map(int, match.groups())
                    move_odpad[t].append((x, y))
                    if t == max_time:
                        sokoban = (x, y)
        if not sokoban:
            latest_sokoban_time = -1
            latest_sokoban_pos = None
            for fakt in riesenie:
                if fakt.startswith("move"):
                    match = re.match(r"move\((\d+),(\d+),(\d+)\)", fakt)
                    if match:
                        t, x, y = map(int, match.groups())
                        if t > latest_sokoban_time:
                            latest_sokoban_time = t
                            latest_sokoban_pos = (x, y)
            sokoban = latest_sokoban_pos
        max_width = max(
            max((x for x, _ in walls), default=0),
            max((x for x, _ in storages), default=0),
            sokoban[0] if sokoban else 0,
        ) + 1
        max_height = max(
            max((y for _, y in walls), default=0),
            max((y for _, y in storages), default=0),
            sokoban[1] if sokoban else 0,
        ) + 1
        mapa = [[" " for _ in range(max_width)] for _ in range(max_height)]
        for x, y in walls:
            mapa[y][x] = "#"
        for x, y in storages:
            if mapa[y][x] == " ":
                mapa[y][x] = "X"
        for (x, y), t in crates.items():
            if mapa[y][x] == "X":
                mapa[y][x] = "c"
            else:
                mapa[y][x] = "C"
        if sokoban:
            x, y = sokoban
            if mapa[y][x] == "X":
                mapa[y][x] = "s"
            else:
                mapa[y][x] = "S"
        for riadok in mapa:
            pass
            #print("".join(riadok))

        self.mapa_solved = mapa
        self.mapa_solved_odpad = {'walls':walls, 'crates':crates_odpad,
                                  'storages':storages,'moves':move_odpad, 'max_time':max_time-1,
                                  'max_width':max_width,
                                  'max_height':max_height}

    def vyries(self,times=10):
        asp_reprezentacia = self.mapa_do_asp()
        pravidla_pohybu = f"""
        % Pridanie času kvôli cyklom
        #const maxSteps={times}.
        time(0..maxSteps).
        
        % Smer pohybu
        direction(up, 0, -1).
        direction(down, 0, 1).
        direction(left, -1, 0).
        direction(right, 1, 0).
        
        % Ak stena -> nič|žiaden pohyb :)
        kto_ta_odblokuje_v_takom_necase(T,X,Y) :-
            time(T),
            wall(X,Y).
        
        % Ak škatuľka -> nič|žiaden pohyb :)
        kto_ta_odblokuje_v_takom_necase(T,X,Y) :-
            time(T),
            crate(T,X,Y).
        
        % Pohyb Sokobana bez škatule (bez push)
        move(T+1, X2, Y2) :-
            time(T),
            move(T,X1 ,Y1),
            direction(Smer, DX ,DY),
            vykonaj(T,Smer),
            X2=X1+ DX,
            Y2=Y1+DY,
            not wall(X2,Y2),
            not crate(T, X2, Y2).
        
        % Posun škatule (push)
        push(T, X1, Y1, X2, Y2, X3, Y3) :-
            time(T),
            move(T, X1, Y1),
            direction(Smer, DX, DY),
            vykonaj(T, Smer),
            X2 = X1+ DX,
            Y2 = Y1 + DY,
            crate(T, X2, Y2),
            X3 = X2 + DX,
            Y3 = Y2 +DY,
            not wall(X3, Y3),
            not crate(T, X3, Y3).
        
        % Aktualizácia škatul
        crate(T+1, X3, Y3) :-
            push(T,_, _, _, _, X3, Y3).
        
         % neposunute škatule ostavajú na mieste
        crate(T+1, X, Y) :-
            time(T),
            crate(T, X, Y),
            not push(T, _, _, X, Y, _, _).
        
        % Sokoban - > pozicia škatulky
        move(T+1, X2, Y2) :-
            push(T, _, _, X2, Y2, _, _).
        
        move(T+1, X, Y) :-
            time(T),
            move(T, X, Y),
            direction(Smer, DX, DY),
            vykonaj(T, Smer),
            X1 = X + DX,
            Y1 = Y + DY,
            kto_ta_odblokuje_v_takom_necase(T, X1, Y1),
            not push(T, _, _, X1, Y1, _, _).
        
        % Stena
        :- move(T+1, X, Y), wall(X, Y).
        % Nemožno vojsť do škatule ak sa neposúva
        :- move(T+1, X, Y), crate(T, X,Y), not push(T,_ ,_ ,X,Y,_ ,_).
        
        %Nejaka škatulka nie je v storidzy
        boks_out_of_storidz(T) :-
            time(T),
            crate(T,X,Y),
            not storage(X,Y).
        %Ak každá škatulka je v storidžy - > vyhral som
        theend(T) :-
            time(T),
            not boks_out_of_storidz(T).
        %Generátor na práve jeden pohyb až dokým nieje nájdený koniec
        {{ vykonaj(T, Smer) : direction(Smer,_, _) }}= 1 :-
            time(T),
            not theend(T).
        %Teraz, keď som už skončil, fakt sa netreba hýbať
        :- vykonaj(T,_) , theend(IKS), IKS<= T.
        
        %Vyberám len model, ktorý sa zmestil do počtu krokov
        :- not theend(maxSteps).
        
        %Oddelenie jedla od odpadu| už netreba :)
        %#show move/3.
        %#show push/7.
        %#show storage/2.
        %#show wall/2.
        %#show crate/3.
        """
        ctl = clingo.Control()
        ctl.add("base", [], asp_reprezentacia + "\n" + pravidla_pohybu)
        ctl.ground([("base", [])])
        riesenie = []
        def model(model):
            riesenie.extend([str(symbol) for symbol in model.symbols(shown=True)])
        ctl.solve(on_model=model)
        self.vykresli_mapu(riesenie)
        file_name = 'debug.txt'
        with open(file_name, "w") as f:
            f.write(f"% DEBUG pre mapu {self.cesta_suboru}\n\n")
            f.write("% Pravidlá na základe vstupnej mapy\n")
            f.write(asp_reprezentacia + "\n")
            f.write("% Všeobecné pravidlá na riešenie\n")
            f.write("\n".join(riadok.strip() for riadok in pravidla_pohybu.splitlines()) + "\n")

            f.write("% Nájdený model\n")
            for x in riesenie:
                f.write(f"{x}\n")

        return riesenie

    def init_ui(self):
        self.setWindowTitle("Výpočtová logika - Sokoban Solver ASP | Roman Božik")
        self.setGeometry(100, 100, 600, 400)


        self.zasobnik_widgetov = QStackedWidget()
        self.setCentralWidget(self.zasobnik_widgetov)


        self.main_menu = self.spawni_main_menu()
        self.zasobnik_widgetov.addWidget(self.main_menu)

    def spawni_main_menu(self):
        m_menu_widget = QWidget()
        m_menu_lajaut = QVBoxLayout()

        title_label = QLabel("Sokoban Solver")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 24, QFont.Bold))
        title_label.setStyleSheet("color: rgb(255, 0, 255);")  # Do budúcna náhodné farby animácia
        m_menu_lajaut.addWidget(title_label)

        vyber_mapy_label = QLabel("Výber mapy")
        vyber_mapy_label.setAlignment(Qt.AlignCenter)
        vyber_mapy_label.setFont(QFont("Arial", 18, QFont.Bold))
        vyber_mapy_label.setStyleSheet("color: rgb(0, 255, 0);")  #  Tiež pozrieť na farbu
        m_menu_lajaut.addWidget(vyber_mapy_label)

        # Zoznam názvou máp
        self.mapovy_list = QListWidget()
        self.mapovy_list.setFont(QFont("Arial", 12))
        self.mapovy_list.addItems(["map1.txt", "map4.txt", "map5.txt","map6.txt", "map8.txt"])
        self.mapovy_list.setStyleSheet("border: 1px solid #aaa;")
        m_menu_lajaut.addWidget(self.mapovy_list)

        solve_tlacidlo = QPushButton("Vyrieš")
        solve_tlacidlo.setFont(QFont("Arial", 16, QFont.Bold))
        solve_tlacidlo.setStyleSheet(
            "background-color: rgb(255, 0, 0); color: white; padding: 10px;"
        )
        solve_tlacidlo.clicked.connect(self.vyber_mapu)
        m_menu_lajaut.addWidget(solve_tlacidlo)

        m_menu_widget.setLayout(m_menu_lajaut)
        return m_menu_widget

    def vyrob_scenu_pre_mapu(self, mapa_cesta):
        mapa_w = QWidget()
        mapa_lay = QVBoxLayout()

        map_label = QLabel(f"Riešim mapu: {mapa_cesta}")
        map_label.setAlignment(Qt.AlignCenter)
        map_label.setFont(QFont("Arial", 18, QFont.Bold))
        map_label.setStyleSheet("color: rgb(0, 0, 255);")
        mapa_lay.addWidget(map_label)

        self.cesta_suboru = mapa_cesta
        self.postupnost = []
        for time in range(1, 1000):
            temp = self.vyries(times=time)
            if len(temp) != 0:
                self.postupnost = temp
                break

        self.grid_layout = QGridLayout()
        self.policka = {}

        for x in range(self.mapa_solved_odpad["max_width"]):
            for y in range(self.mapa_solved_odpad["max_height"]):
                policko = QLabel(" ")
                policko.setAlignment(Qt.AlignCenter)
                policko.setFont(QFont("Courier", 16))
                policko.setStyleSheet("border: 1px solid black; padding: 5px;")

                if (x, y) in self.mapa_solved_odpad["walls"]:
                    policko.setText("#")
                    policko.setStyleSheet("background-color: gray; color: white;")
                elif (x, y) in self.mapa_solved_odpad["storages"]:
                    policko.setText("X")
                    policko.setStyleSheet("background-color: blue; color: white;")

                self.grid_layout.addWidget(policko, y, x)
                self.policka[(x, y)] = policko

        mapa_lay.addLayout(self.grid_layout)


        navigacia = QHBoxLayout()

        s5tlacidlo = QPushButton("◀")
        s5tlacidlo.setFont(QFont("Arial", 14))
        s5tlacidlo.clicked.connect(self.predchadzajuci_krok)

        self.label_pre_kroky = QLabel("Krok 0 / 0")
        self.label_pre_kroky.setAlignment(Qt.AlignCenter)
        self.label_pre_kroky.setFont(QFont("Arial", 14))

        dalej_tlacidlo = QPushButton("▶")
        dalej_tlacidlo.setFont(QFont("Arial", 14))
        dalej_tlacidlo.clicked.connect(self.dalsi_krok)

        navigacia.addWidget(s5tlacidlo)
        navigacia.addWidget(self.label_pre_kroky)
        navigacia.addWidget(dalej_tlacidlo)

        mapa_lay.addLayout(navigacia)

        menu_tlacidl = QPushButton("Späť do menu")
        menu_tlacidl.setFont(QFont("Arial", 14))
        menu_tlacidl.setStyleSheet("background-color: rgb(0, 255, 0); color: black; padding: 10px;")
        menu_tlacidl.clicked.connect(self.nas5dohlmenu)
        mapa_lay.addWidget(menu_tlacidl)

        mapa_w.setLayout(mapa_lay)

        self.aktualny_krok = 0
        self.max_cas = self.mapa_solved_odpad["max_time"]
        self.aktualizuj_mapu()
        return mapa_w

    def aktualizuj_mapu(self):
        try:
            # Reset mapky
            for (x, y), policko in self.policka.items():
                policko.setText(" ")
                policko.setStyleSheet("background-color: white; color: black; border: 1px solid black;")

                if (x, y) in self.mapa_solved_odpad["walls"]:
                    policko.setText("#")
                    policko.setStyleSheet("background-color: gray; color: white;")
                elif (x, y) in self.mapa_solved_odpad["storages"]:
                    policko.setText("X")
                    policko.setStyleSheet("background-color: blue; color: white;")

            # Vykreslenie krabíc aktuálny čas
            for x, y in self.mapa_solved_odpad["crates"].get(self.aktualny_krok, []):
                policko = self.policka[(x, y)]
                if policko.text() == "X":
                    policko.setText("c")
                    policko.setStyleSheet("background-color: green; color: white;")
                else:
                    policko.setText("C")
                    policko.setStyleSheet("background-color: green; color: white;")

            # Vykreslenie Sokobana
            sokoban_pozicie = self.mapa_solved_odpad["moves"].get(self.aktualny_krok, [])
            for x, y in sokoban_pozicie:
                policko = self.policka[(x, y)]
                if policko.text() == "X":
                    policko.setText("s")
                    policko.setStyleSheet("background-color: yellow; color: black;")
                else:
                    policko.setText("S")
                    policko.setStyleSheet("background-color: yellow; color: black;")

        except Exception as e:
            print(f"Chyba pri aktualizácii mapky: {e}")

    def vyber_mapu(self):
        mapka_ako_item = self.mapovy_list.currentItem()
        if mapka_ako_item:
            mapka_meno = mapka_ako_item.text()
            #print(f"Riešim mapu: {mapka_meno}")


            mapova_scenka = self.vyrob_scenu_pre_mapu(mapka_meno)
            self.zasobnik_widgetov.addWidget(mapova_scenka)
            self.zasobnik_widgetov.setCurrentWidget(mapova_scenka)


            self.aktualizuj_krok_label()
        else:
            print("Žiadna mapa nebola vybraná!")

    def predchadzajuci_krok(self):
        if self.aktualny_krok > 0:
            self.aktualny_krok -= 1
            self.aktualizuj_krok_label()
            self.aktualizuj_mapu()

    def dalsi_krok(self):
        if self.aktualny_krok < self.max_cas:
            self.aktualny_krok += 1
            self.aktualizuj_krok_label()
            self.aktualizuj_mapu()

    def aktualizuj_krok_label(self):
        self.label_pre_kroky.setText(f"Krok {self.aktualny_krok} / {self.max_cas}")

    def nas5dohlmenu(self):
        self.zasobnik_widgetov.setCurrentWidget(self.main_menu)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    sokoban_app = Sokoban()
    sokoban_app.show()
    sys.exit(app.exec_())
