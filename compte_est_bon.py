#! /usr/bin/env python3

"""
Ce programme prendra sur son entrée standard les 6 cartons tirés au sort suivis du nombre à
trouver. Par exemple, si les cartons tirés sont 3 5 7 9 25 50 et que le nombre à découvrir est
859, il devra être appelé ainsi : echo 3 5 7 9 25 50 859  | ./compte_est_bon.py

Par défaut, les parcours utilisent la version améliorée de l'arbre de calculs.
Pour utiliser la version naïve : echo 3 5 7 9 25 50 859 | NAIF=1 ./compte_est_bon.py
"""

from recherche_compte_est_bon import *
import os
import sys
import time

def lire_stdin():
    """Lit l'entrée standard en invitant l'utilisateur à l'aide d'un message si le flux d'entrée n'est pas redirigé"""
    if sys.stdin.isatty():
        sys.stderr.write("Saisissez du texte (Ctrl+D pour terminer) :\n")
    return sys.stdin.read()

def lancer(nom, parcours, cartons, nombre, ameliore):
    print(f"\n=== {nom} ===")
    debut = time.perf_counter()
    expression, nb_noeuds = parcours(cartons, nombre, ameliore)
    fin = time.perf_counter()
    valide, valeur = eval_NPI_liste(expression)
    print(f"Meilleure solution : {' '.join(map(str, expression))} = {valeur}")
    eval_NPI_liste(expression, True)   # détail des calculs
    print(f"Noeuds parcourus : {nb_noeuds}")
    print(f"Taille max de la structure : {STATISTIQUES['taille_max_structure']}")
    print(f"Hauteur max de l'arbre exploré : {STATISTIQUES['hauteur_max']}")
    print(f"Largeur max de l'arbre exploré : {STATISTIQUES['largeur_max']}")
    print(f"{nom} : {fin - debut:.6f} s")

if __name__ == "__main__":
    cartons_nombre = lire_stdin()
    *cartons,nombre = map(int, cartons_nombre.split())
    ameliore = "NAIF" not in os.environ
    print(f"Recherche de {nombre} avec {cartons} (version {'améliorée' if ameliore else 'naïve'})")

    lancer("DFS", parcours_DFS, cartons, nombre, ameliore)
    lancer("DFS récursif", parcours_DFS_recursif, cartons, nombre, ameliore)
    lancer("BFS", parcours_BFS, cartons, nombre, ameliore)