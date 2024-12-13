import clingo

class Sokoban:
    def __init__(self, cesta_suboru):
        self.cesta_suboru = cesta_suboru
        self.mapa_data = []
        self.pociatocna_pozicia = None

    def mapa_do_asp(self):
        asp_fakty = []
        with open(self.cesta_suboru, 'r') as file:
            self.mapa_data = file.readlines()

        for y, riadok in enumerate(self.mapa_data):
            for x, znak in enumerate(riadok.strip()):
                if znak == '#':
                    asp_fakty.append(f"wall({x},{y}).")
                elif znak == 'C':
                    asp_fakty.append(f"crate({x},{y}).")
                elif znak == 'X':
                    asp_fakty.append(f"storage({x},{y}).")
                elif znak == 'S':
                    asp_fakty.append(f"sokoban({x},{y}).")
                    self.pociatocna_pozicia = (x, y)
                elif znak == 's':
                    asp_fakty.append(f"sokoban({x},{y}).")
                    asp_fakty.append(f"storage({x},{y}).")
                    self.pociatocna_pozicia = (x, y)
                elif znak == 'c':
                    asp_fakty.append(f"crate({x},{y}).")
                    asp_fakty.append(f"storage({x},{y}).")

        return '\n'.join(asp_fakty)

    def vyries_pohyb(self, sekvencia):
        asp_reprezentacia = self.mapa_do_asp()

        if not self.pociatocna_pozicia:
            raise ValueError("Počiatočná pozícia Sokobana nie je definovaná v mape.")

        pravidla_pohybu = f"""
        % smery
        direction(up, 0, -1).
        direction(down, 0, 1).
        direction(left, -1, 0).
        direction(right, 1, 0).

        % Počiatočná pozícia sokobana
        move(0, {self.pociatocna_pozicia[0]}, {self.pociatocna_pozicia[1]}).

        % Pohyb chceným smerom
        move(T+1, X2, Y2) :-
            move(T, X1, Y1),
            direction(Smer, DX, DY),
            vykonaj(T, Smer),
            X2 = X1 + DX,
            Y2 = Y1 + DY,
            not wall(X2, Y2),
            not crate(X2, Y2).

        % Stopka, ak narazí na boxik / stenu
        :- move(T+1, X, Y), wall(X, Y).
        :- move(T+1, X, Y), crate(X, Y).
        """

        mapovanie_smerov = {'h': 'up', 'd': 'down', 'l': 'left', 'p': 'right'}
        sekvencia_fakty = [
            f"vykonaj({i}, {mapovanie_smerov[s]})." for i, s in enumerate(sekvencia)
        ]

        asp_program = asp_reprezentacia + "\n" + pravidla_pohybu + "\n" + "\n".join(sekvencia_fakty)

        ctl = clingo.Control()
        ctl.add("base", [], asp_program)
        ctl.ground([("base", [])])

        riesenie = []

        def na_model(model):
            riesenie.extend([str(symbol) for symbol in model.symbols(shown=True)])

        ctl.solve(on_model=na_model)

        return [fakt for fakt in riesenie if fakt.startswith("move")]


if __name__ == "__main__":
    cesta_suboru = "map1.txt"
    sokoban = Sokoban(cesta_suboru)

    sekvencia = "pppd"  # Sekvencia pohybov
    pohyby = sokoban.vyries_pohyb(sekvencia)

    for pohyb in pohyby:
        print(pohyb)
