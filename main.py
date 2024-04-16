import datetime
import math
import os

import pandas as pd
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from math import ceil

from calculator import rounder
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
            return TAUX[pays][2]
        if sku[0] == '2' or sku[0] == '3':
            return TAUX[pays][1]
    else :
        return None


def get_produit_details(value):

    date_vente = value[0]
    nom_produit = value[1]
    quantite = value[3]
    prix_unitaire = value[4]
    prix_total = value[11]
    monnaie = value[12]

    sku = value[32]
    pays = value[23]

    taux = get_taux_from_sku_pays(sku, pays)

    if taux :
        prix_total_ht = rounder(quantite * prix_unitaire * (1 - taux / 100),2)
    else:
        prix_total_ht = rounder(quantite * prix_unitaire,2)

    return  [
                date_vente,
                nom_produit,
                quantite,
                prix_unitaire,
                prix_total,
                prix_total_ht,
                monnaie,
                sku
    ]


def generate_pdf_from_csv(csv_file, html_template, output_dir):

    total_factures_generees = 0
    # Lecture du fichier CSV
    df = pd.read_csv(csv_file)

    # Chargement du template HTML
    env = Environment(loader=FileSystemLoader('.'),
                      comment_start_string='{=',
                      comment_end_string='=}',
                      )
    template = env.get_template(html_template)

    # Création du répertoire de sortie s'il n'existe pas déjà
    os.makedirs(output_dir, exist_ok=True)

    hashmap = create_hashmap_from_csv(csv_file)

    # Afficher la hashmap résultante
    for key, value in hashmap.items():

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
            total_produits_ht += produit[5]
            frais_port += value[x][9]

        tva_applicable = value[0][23] in TAUX
        total_produits_ht = round(total_produits_ht,2)

        taux = None

        if tva_applicable:
            taux = get_taux_from_sku_pays(value[0][32], value[0][23])
            total_produits_tva = round(total_produits_ht*taux/100,2)
            total_produits_ttc = total_produits_ht + total_produits_tva
        else :
            total_produits_tva = total_produits_ht
            total_produits_ttc = total_produits_ht

        discount = value[0][5]
        if not is_nan(discount):
            taux_discount = float(DISCOUNT[discount])
            total_discount = round(total_produits_ttc * taux_discount / 100,2)
        else :
            discount = None

        prix_final = round(total_produits_ttc - total_discount + frais_port ,2)

        html_content = template.render(

            nom=value[0][17],
            adresse1=value[0][18],
            adresse2= None if is_nan(value[0][19]) else value[0][19],
            ville=value[0][20],
            etat=value[0][21],
            code_postal=value[0][22],
            pays=value[0][23],
            date_facture=value[0][0],
            num_facture=str(key),
            produits= produits,
            tva_applicable=tva_applicable,
            discount=discount,
            total_produits_ht=total_produits_ht,
            total_produits_ttc=total_produits_ttc,
            total_produits_tva=total_produits_tva,
            taux=taux,
            taux_discount=taux_discount,
            total_discount=total_discount,
            prix_final = prix_final,
            pays_label = TAUX[value[0][23]][0] if value[0][23] in TAUX else '',
            frais_port = frais_port
        )

        output_pdf_path = os.path.join(output_dir, f"facture_{key}.pdf")
        HTML(string=html_content).write_pdf(output_pdf_path)
        total_factures_generees +=1

    print('Total factures générées : ')
    print(total_factures_generees)
    print('---------------------------')
    print('')

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

print(rounder(0.012,2))
print(ceil(0.012))

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


