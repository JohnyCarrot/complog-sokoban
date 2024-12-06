from pyswip import Prolog

# Pevne zadaná mapka
MAP = [
    "######",
    "#s   #",
    "#CCCX#",
    "#X   #",
    "######"
]

def run_solver(initial_state,final_state, max_depth):
    """Spustí riešič a dynamicky pridá počiatočný stav."""
    prolog = Prolog()

    # Načítanie základného Prolog súboru
    prolog.consult("solver.pl")

    # Spustenie dotazu
    query = list(prolog.query(f"spustac({initial_state},{final_state},Plan, {max_depth})"))
    if query:
        print("Solution found:")
        for solution in query:
            print("Plan:", solution["Plan"])
    else:
        print("No solution found.")



if __name__ == "__main__":
    initial_state = "[on(monkey,floor), on(box,floor), at(monkey,a), at(box,b), at(bananas,c), status(bananas,hanging)]"
    final_state = "[ status(bananas,grabbed) ]"

    # Maximálna hĺbka riešenia
    max_depth = "s(s(s(s(s(0)))))"

    # Spusti riešič
    run_solver(initial_state,final_state, max_depth)