from math import ceil, floor


def rounder(num, up=True):
    digits = 2
    mul = 10**digits
    if up:
        return ceil(num * mul)/mul
    else:
        return floor(num*mul)/mul



def calcul_frais_port(produits, frais_port):

    total_par_taux = {}

    for p in produits:
        if not p['taux'] in total_par_taux:
            total_par_taux.update({p['taux']:p['prix_total']})
        else:
            ancien_total = total_par_taux[p['taux']]
            total_par_taux.update({p['taux']:p['prix_total']+ancien_total})


    max_value = max(total_par_taux.values())


    taux_retenu = 0

    for key, value in total_par_taux.items():
        if value == max_value:
            # en cas d'égalité, on prend le taux le plus haut.
            if taux_retenu == 0:
                taux_retenu = key
            elif key > taux_retenu:
                taux_retenu = key



    print(f'taux retenu : {taux_retenu}  pour {max_value} parmi les valeurs {total_par_taux}')

    # on recupere les frais de ports avec leatxu retenu
    frais_port_final = rounder((1 - taux_retenu/100) * frais_port, 2)

    print(f'frais de port final : {frais_port} - {taux_retenu}%  = {(1-taux_retenu/100) * frais_port} arrondi à {frais_port_final}')

    return frais_port_final, taux_retenu


def calcul_total_tva_par_taux(produits):
    total_par_taux = {}

    for p in produits:
        if not p['taux'] in total_par_taux:
            total_par_taux.update({p['taux']: p['prix_tva']})
        else:
            ancien_total = total_par_taux[p['taux']]
            total_par_taux.update({p['taux']: p['prix_tva'] + ancien_total})

    return total_par_taux


