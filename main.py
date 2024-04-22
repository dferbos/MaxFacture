import datetime
import math
import os

import pandas as pd
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from calculator import rounder, calcul_frais_port, calcul_total_tva_par_taux
from settings import TAUX, DISCOUNT


def is_nan(value):
    try:
        return math.isnan(float(value))
    except ValueError:
        return False


def create_hashmap_from_csv(csv_file):
    nombre_lignes = 0

    df = pd.read_csv(csv_file)
    hashmap = {}

    for _, row in df.iterrows():
        nombre_lignes += 1
        key = row[24]  # Utiliser la 3e colonne comme clé
        row_list = list(row)  # Convertir la ligne en liste
        if key in hashmap:
            hashmap[key].append(row_list)
        else:
            hashmap[key] = [row_list]

    print('nombres de lignes dans le fichier : ')
    print(nombre_lignes)
    print('------------------------')
    print('nombres de factures à générer : ')
    print(len(hashmap))
    print('------------------------')
    return hashmap


def get_taux_from_sku_pays(sku, pays):
    sku=str(sku)
    if pays in TAUX:
        if sku[0] == '1' or sku[0] == '4':
            print(f'Pays ={pays} et SKU commence par {sku[0]} => taux = {TAUX[pays][1]}')
            return TAUX[pays][2]
        if sku[0] == '2' or sku[0] == '3':
            print(f'Pays ={pays} et SKU commence par {sku[0]} => taux = {TAUX[pays][1]}')
            return TAUX[pays][1]
    else :
        print("Pays hors UE => pas de taux applicable")
        return None



def get_produit_details(value):

    date_vente = value[0]
    nom_produit = value[1]
    quantite = value[3]
    prix_unitaire = value[4]
    prix_total = value[11]
    monnaie = value[12]
    prix_tva = 0

    sku = value[32]
    pays = value[23]

    print('-------------------------')
    print("calcul du taux")
    taux = get_taux_from_sku_pays(sku, pays)


    print('-------------------------')
    print("calcul du prix total HT")
    if taux :
        prix_tva = rounder(prix_total * taux / 100,2)
        print(f'taxe à payer : prix_total x (taux / 100) => {prix_total} x {taux} /100  = {prix_total *taux / 100 } ')
        print(f'Arrondi superieur pour la taxe :{prix_tva}')
        prix_total_ht = rounder(prix_total - prix_tva,2)
        print(f"Prix total HT = prix_total - taxe à payer => {prix_total} - {prix_tva}  = {prix_total_ht} ")
    else:
        print(f"Pas de taux : prix_total_ht = prix_total donc {prix_total}")
        prix_total_ht = prix_total

    return  {
        'date_vente' : date_vente,
        'nom_produit' : nom_produit ,
        'quantite' : quantite,
        'prix_unitaire' : prix_unitaire,
        'prix_total' : prix_total,
        'prix_total_ht' : prix_total_ht,
        'monnaie' : monnaie,
        'taux' : taux,
        'sku' : sku,
        'prix_tva': prix_tva
    }


def generate_pdf_from_csv(csv_file, html_template, output_dir):

    # compteur de factures générées
    total_factures_generees = 0

    # Préparation de l'environnement + recupération template
    template = get_template(html_template, output_dir)

    # Tri des données du CSV
    hashmap = create_hashmap_from_csv(csv_file)

    # Afficher la hashmap résultante
    for key, value in hashmap.items():

        print('')
        print(f'COMMANDE {key}')

        taux = None
        # Déduction si commande soumise à TVA
        # pays de commande
        pays_commande = value[0][23]
        tva_applicable = pays_commande in TAUX
        if tva_applicable:
            taux = get_taux_from_sku_pays(value[0][32], pays_commande)
        frais_port = 0

        produits = []
        total_produits_ht = 0
        total_produits_ttc = 0
        total_produits_tva = 0
        total_discount = 0
        taux_discount = 0

        for x in range(len(value)):

            produit = get_produit_details(value[x])
            produits.append(produit)
            total_produits_ht += produit['prix_total_ht']
            total_produits_ttc += produit['prix_total']
            total_produits_tva += produit['prix_tva']
            frais_port += value[x][9]
            total_discount += value[x][7]


        total_produits_ht = rounder(total_produits_ht,2)

        # frais de port conditionnés à la TVA
        print('-------------------------')
        print("calcul des frais de port")
        if tva_applicable :
            frais_port_final, taux_retenu = calcul_frais_port(produits, frais_port)
            total_par_taux = calcul_total_tva_par_taux(produits)
        else:
            frais_port_final = frais_port
            total_par_taux = None

        if total_par_taux and len(total_par_taux) == 1:
            total_produits_tva1 = rounder(list(total_par_taux.values())[0] + frais_port - frais_port_final, 2)
            taux1 = list(total_par_taux.keys())[0]
            total_produits_tva2 = None
            taux2 = None
        elif total_par_taux and len(total_par_taux) == 2:
            if list(total_par_taux.values())[0] == taux_retenu:
                total_produits_tva1 = rounder(list(total_par_taux.values())[0]+ frais_port - frais_port_final, 2)
                taux1 = list(total_par_taux.keys())[0]
                total_produits_tva2 = rounder(list(total_par_taux.values())[1], 2)
                taux2 = list(total_par_taux.keys())[1]
            else:
                total_produits_tva1 = rounder(list(total_par_taux.values())[0], 2)
                taux1 = list(total_par_taux.keys())[0]
                total_produits_tva2 = rounder(list(total_par_taux.values())[1] + frais_port - frais_port_final, 2)
                taux2 = list(total_par_taux.keys())[1]
        else:
            total_produits_tva1 = None
            taux1 = None
            total_produits_tva2 = None
            taux2 = None

        # if tva_applicable:
        #     taux = get_taux_from_sku_pays(value[0][32], pays_commande)
        #     total_produits_tva = round(total_produits_ht*taux/100,2)
        #     total_produits_ttc = total_produits_ht + total_produits_tva
        # else :
        #     total_produits_tva = total_produits_ht
        #     total_produits_ttc = total_produits_ht

        discount = value[0][5]
        if not is_nan(discount):
            taux_discount = float(DISCOUNT[discount])
        else :
            discount = None

        prix_final = rounder(total_produits_ttc - total_discount + frais_port,2)

        html_content = template.render(

            nom=value[0][17],
            adresse1=value[0][18],
            adresse2= None if is_nan(value[0][19]) else value[0][19],
            ville=value[0][20],
            etat=value[0][21],
            code_postal=value[0][22],
            pays=pays_commande,
            date_facture=value[0][0],
            num_facture=str(key),
            produits= produits,
            tva_applicable=tva_applicable,
            discount=discount,
            total_produits_ht=total_produits_ht,
            total_produits_ttc=total_produits_ttc,
            total_produits_tva1=total_produits_tva1,
            total_produits_tva2=total_produits_tva2,
            taux1=taux1,
            taux2=taux2,
            taux_discount=taux_discount,
            total_discount=total_discount,
            prix_final = prix_final,
            pays_label = TAUX[pays_commande][0] if pays_commande in TAUX else '',
            frais_port = frais_port,
            frais_port_final = frais_port_final
        )

        output_pdf_path = os.path.join(output_dir, f"facture_{key}.pdf")
        HTML(string=html_content).write_pdf(output_pdf_path)
        total_factures_generees +=1
        print('')
        print(f' FIN COMMANDE {key}')

    print('')
    print('Total factures générées : ')
    print(total_factures_generees)
    print('---------------------------')
    print('')



'''
Préparation de l'environnement + recupération template
'''
def get_template(html_template, output_dir):
    # Chargement du template HTML
    env = Environment(loader=FileSystemLoader('.'),
                      comment_start_string='{=',
                      comment_end_string='=}',
                      )
    template = env.get_template(html_template)
    # Création du répertoire de sortie s'il n'existe pas déjà
    os.makedirs(output_dir, exist_ok=True)
    return template


date_debut = datetime.datetime.now()

# Exemple d'utilisation
csv_file = "test.csv"

mois = str(datetime.datetime.now().month) + '_' + str(datetime.datetime.now().year)


# Utilisation de la fonction pour générer le PDF
generate_pdf_from_csv(csv_file, "t.html", 'factures_'+mois)

date_fin = datetime.datetime.now()

print('Temps de calcul : ')
print(date_fin-date_debut)
print()
print('Penser à vérifer les données dans les factures')

#    date_vente = value[0][0],
#    nom_produit = value[0][1],
#    quantite = value[0][3],
#    prix_unitaire = value[0][4],  TTC
#    prix_total = value[0][11],
#    monnaie = value[0][12],
#    sku = value[0][32],


# total HT = ( prix unitaire * quantité ) - % TVA

# TVA =
# SKU  1 => 5.5


