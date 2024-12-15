import clingo
import re

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
        storages = set()
        sokoban = None
        max_time = 0
        for fakt in riesenie:
            match = re.match(r"(move|crate|push)\((\d+),", fakt)
            if match:
                t = int(match.group(2))
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
            print("".join(riadok))

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
        #show move/3.
        #show push/7.
        #show storage/2.
        #show wall/2.
        #show crate/3.
        """
        ctl = clingo.Control()
        ctl.add("base", [], asp_reprezentacia + "\n" + pravidla_pohybu)
        ctl.ground([("base", [])])
        riesenie = []
        def model(model):
            riesenie.extend([str(symbol) for symbol in model.symbols(shown=True)])
        ctl.solve(on_model=model)
        self.vykresli_mapu(riesenie)
        return riesenie

if __name__ == "__main__":
    cesta_suboru = "map8.txt"
    sokoban = Sokoban(cesta_suboru)
    pohyby = sokoban.vyries()
    for p in pohyby:
        pass
