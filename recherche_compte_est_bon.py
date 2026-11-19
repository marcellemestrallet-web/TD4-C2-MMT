#! /usr/bin/env python
#! /usr/bin/env python3

""" Implémentation des parcours de l'arbre de calculs à la volée :
- parcours en profondeur d'abord itératif
- parcours en profondeur d'abord récursif
- parcours en largeur d'abord itératif

Chaque noeud de l'arbre est une expression NPI partielle. Ses enfants sont obtenus
en ajoutant à la fin de l'expression soit un carton encore disponible, soit un opérateur.
L'arbre n'est jamais construit en mémoire : les noeuds sont générés à la volée.

Deux versions de chaque parcours sont disponibles (paramètre `ameliore`) :
- version naïve (ameliore=False) : tous les enfants sont générés et chaque noeud est
  évalué entièrement avec eval_NPI_liste ; les expressions invalides sont comptées puis élaguées.
- version améliorée (ameliore=True, par défaut) :
    1. on n'engendre que des expressions valides (soustraction strictement positive,
       division exacte, opérateur seulement si la pile contient au moins deux valeurs) ;
    2. on évite les expressions redondantes (commutativité de + et *, multiplication
       ou division par 1, cartons de même valeur) ;
    3. on raccourcit l'évaluation : chaque noeud transporte la pile de ses valeurs,
       calculée à partir de celle de son parent en O(1), au lieu de réévaluer
       toute l'expression.

Les statistiques du dernier parcours (taille max de la pile ou de la file, hauteur et
largeur max de l'arbre exploré, nombre de noeuds) sont disponibles dans STATISTIQUES.
"""

import os
import sys

from TAD.piles_listes_python import Pile

# Le module de files doublement chaînées importe `listes_doublement_chainees` sans
# préfixe de paquet : on ajoute le répertoire TAD au chemin de recherche des modules.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "TAD"))
from files_listes_doublement_chainees import File  # défiler en O(1), contrairement à la file sur liste python

from notation_polonaise_inverse import eval_NPI_liste

OPERATEURS = ('+', '-', '*', '/')

# Statistiques du dernier parcours effectué
STATISTIQUES = {}


# Fonctions communes aux trois parcours


def initialiser_statistiques():
    STATISTIQUES.clear()
    STATISTIQUES.update({
        "nb_noeuds": 0,
        "taille_max_structure": 0,   # taille max de la pile (DFS) ou de la file (BFS)
        "hauteur_max": 0,            # longueur max d'une expression explorée
        "noeuds_par_niveau": {},     # nombre de noeuds explorés à chaque profondeur
    })


def noter_noeud(profondeur):
    STATISTIQUES["nb_noeuds"] += 1
    STATISTIQUES["hauteur_max"] = max(STATISTIQUES["hauteur_max"], profondeur)
    niveaux = STATISTIQUES["noeuds_par_niveau"]
    niveaux[profondeur] = niveaux.get(profondeur, 0) + 1


def finaliser_statistiques():
    niveaux = STATISTIQUES["noeuds_par_niveau"]
    STATISTIQUES["largeur_max"] = max(niveaux.values()) if niveaux else 0


def racine(cartons, ameliore):
    """Noeud racine : (expression, cartons restants, pile de valeurs ou profondeur de pile)."""
    if ameliore:
        return ((), tuple(sorted(cartons)), ())
    return ((), tuple(cartons), 0)


def valeur_noeud(noeud, ameliore):
    """Renvoie (valide, valeur) pour un noeud. valeur vaut None si l'expression
    n'est pas un calcul complet (pile vide ou contenant plusieurs valeurs)."""
    expression, _, pile = noeud
    if ameliore:
        # La pile de valeurs est déjà calculée : aucune réévaluation nécessaire
        return True, (pile[0] if len(pile) == 1 else None)
    if not expression:
        return True, None
    return eval_NPI_liste(list(expression))


def enfants(noeud, ameliore):
    """Génère à la volée les enfants d'un noeud."""
    if ameliore:
        return enfants_ameliores(noeud)
    return enfants_naifs(noeud)


def enfants_naifs(noeud):
    expression, restants, profondeur_pile = noeud
    resultat = []
    for i, carton in enumerate(restants):
        resultat.append((expression + (carton,), restants[:i] + restants[i + 1:], profondeur_pile + 1))
    if profondeur_pile >= 2:
        for op in OPERATEURS:
            resultat.append((expression + (op,), restants, profondeur_pile - 1))
    return resultat


def enfants_ameliores(noeud):
    expression, restants, pile = noeud
    resultat = []

    # Ajout d'un carton : un seul enfant par valeur distincte (les cartons sont triés)
    for i, carton in enumerate(restants):
        if i > 0 and restants[i - 1] == carton:
            continue
        resultat.append((expression + (carton,), restants[:i] + restants[i + 1:], pile + (carton,)))

    # Ajout d'un opérateur : seulement s'il produit un résultat valide et non redondant
    if len(pile) >= 2:
        op2, op1 = pile[-2], pile[-1]   # op1 est au sommet, comme dans eval_NPI_liste
        base = pile[:-2]
        if op2 <= op1:                                      # a+b et b+a : on n'en garde qu'un
            resultat.append((expression + ('+',), restants, base + (op2 + op1,)))
        if op2 > op1:                                       # résultat strictement positif
            resultat.append((expression + ('-',), restants, base + (op2 - op1,)))
        if op2 <= op1 and op2 != 1 and op1 != 1:            # commutativité, et x*1 est inutile
            resultat.append((expression + ('*',), restants, base + (op2 * op1,)))
        if op1 != 1 and op2 % op1 == 0:                     # division exacte, et x/1 est inutile
            resultat.append((expression + ('/',), restants, base + (op2 // op1,)))
    return resultat


class Meilleur:
    """Mémorise la meilleure solution trouvée et affiche chaque amélioration."""

    def __init__(self, cible, afficher):
        self.cible = cible
        self.afficher = afficher
        self.ecart = None
        self.expression = []

    def proposer(self, expression, valeur):
        """Renvoie True si la cible est atteinte."""
        if valeur is None:
            return False
        ecart = abs(valeur - self.cible)
        if self.ecart is None or ecart < self.ecart:
            self.ecart = ecart
            self.expression = list(expression)
            if self.afficher:
                print(f"  {' '.join(map(str, expression))} = {valeur} (écart {ecart})")
        return ecart == 0



# Parcours en profondeur d'abord itératif : une pile de noeuds à explorer


def parcours_DFS(cartons, cible, ameliore=True, afficher=True):
    # cartons : une liste
    # cible : entier
    initialiser_statistiques()
    meilleur = Meilleur(cible, afficher)

    pile = Pile()
    pile.empiler(racine(cartons, ameliore))
    taille = 1
    STATISTIQUES["taille_max_structure"] = 1

    while not pile.est_vide():
        noeud = pile.depiler()
        taille -= 1
        noter_noeud(len(noeud[0]))

        valide, valeur = valeur_noeud(noeud, ameliore)
        if not valide:
            continue                       # une expression invalide le reste : on élague
        if meilleur.proposer(noeud[0], valeur):
            break                          # la cible est atteinte

        # Les enfants sont empilés à l'envers pour être explorés dans l'ordre
        for enfant in reversed(enfants(noeud, ameliore)):
            pile.empiler(enfant)
            taille += 1
        STATISTIQUES["taille_max_structure"] = max(STATISTIQUES["taille_max_structure"], taille)

    finaliser_statistiques()
    return meilleur.expression, STATISTIQUES["nb_noeuds"]



# Parcours en largeur d'abord itératif : une file de noeuds à explorer


def parcours_BFS(cartons, cible, ameliore=True, afficher=True):
    # cartons : une liste
    # cible : entier
    initialiser_statistiques()
    meilleur = Meilleur(cible, afficher)

    file = File()
    file.enfiler(racine(cartons, ameliore))
    taille = 1          # la méthode longueur() de la file est en O(n) : on compte nous-mêmes
    STATISTIQUES["taille_max_structure"] = 1

    while not file.est_vide():
        noeud = file.defiler()
        taille -= 1
        noter_noeud(len(noeud[0]))

        valide, valeur = valeur_noeud(noeud, ameliore)
        if not valide:
            continue
        if meilleur.proposer(noeud[0], valeur):
            break

        for enfant in enfants(noeud, ameliore):
            file.enfiler(enfant)
            taille += 1
        STATISTIQUES["taille_max_structure"] = max(STATISTIQUES["taille_max_structure"], taille)

    finaliser_statistiques()
    return meilleur.expression, STATISTIQUES["nb_noeuds"]



# Parcours en profondeur d'abord récursif : la pile est celle des appels


def parcours_DFS_recursif(cartons, cible, ameliore=True, afficher=True):
    initialiser_statistiques()
    meilleur = Meilleur(cible, afficher)
    trouve = False

    def parcours_DFSR_aux(noeud, profondeur_appels):
        # noeud = (choisis, restants, pile de valeurs ou profondeur de pile)
        nonlocal trouve
        noter_noeud(len(noeud[0]))
        STATISTIQUES["taille_max_structure"] = max(STATISTIQUES["taille_max_structure"], profondeur_appels)

        valide, valeur = valeur_noeud(noeud, ameliore)
        if not valide:
            return                                   # cas de base : expression invalide
        if meilleur.proposer(noeud[0], valeur):
            trouve = True                            # cas de base : cible atteinte
            return
        for enfant in enfants(noeud, ameliore):      # cas général : explorer chaque enfant
            parcours_DFSR_aux(enfant, profondeur_appels + 1)
            if trouve:
                return

    parcours_DFSR_aux(racine(cartons, ameliore), 1)

    finaliser_statistiques()
    return meilleur.expression, STATISTIQUES["nb_noeuds"]


if __name__ == "__main__":
    for parcours in (parcours_DFS, parcours_BFS, parcours_DFS_recursif):
        print(parcours.__name__)
        expression, nb = parcours([3, 5, 7, 9, 25, 50], 859)
        print("  ->", expression, "en", nb, "noeuds")