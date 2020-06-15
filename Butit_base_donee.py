
# Récupération à partir d'un fichier zip
#
from zipfile import ZipFile
import json
import re
import sqlite3
import wptools
#
# Ouverture d'une connexion avec la base de données
#
conn = sqlite3.connect('pays.sqlite')


def get_zip_info(country,continent):
    with ZipFile('{}.zip'.format(continent),'r') as z:
    
        # infobox du pays
        return json.loads(z.read('{}.json'.format(country)))

#
# Affichage des informations sur un pays
#
def print_capital(info):
    print('{}, Capital : {} - {}'.format(info['conventional_long_name'],info['capital'],info['coordinates']))

#
# Récupération du nom complet d'un pays depuis l'infobox wikipédia
#
def get_name(wp_info):
    
    # cas général
    if 'conventional_long_name' in wp_info:
        name = wp_info['conventional_long_name']
        return name

    # Aveu d'échec, on ne doit jamais se retrouver ici
    print('Could not fetch country name {}'.format(wp_info))
    return None

#
# Récupération de la capitale d'un pays depuis l'infobox wikipédia
#
def get_capital(wp_info):
    
    # cas général
    if 'capital' in wp_info:
        
        # parfois l'information récupérée comporte plusieurs lignes
        # on remplace les retours à la ligne par un espace
        capital = wp_info['capital'].replace('\n',' ')
        return capital

    # Aveu d'échec, on ne doit jamais se retrouver ici
    print(' Could not fetch country capital {}'.format(wp_info))
    return None

#
# Conversion d'une chaîne de caractères décrivant une position géographique
# en coordonnées numériques latitude et longitude
#
def cv_coords(str_coords):
    # on découpe au niveau des "|" 
    c = str_coords.split('|')

    # on extrait la latitude en tenant compte des divers formats
    lat = float(c.pop(0))
    if (c[0] == 'N'):
        c.pop(0)
    elif ( c[0] == 'S' ):
        lat = -lat
        c.pop(0)
    elif ( len(c) > 1 and c[1] == 'N' ):
        lat += float(c.pop(0))/60
        c.pop(0)
    elif ( len(c) > 1 and c[1] == 'S' ):
        lat += float(c.pop(0))/60
        lat = -lat
        c.pop(0)
    elif ( len(c) > 2 and c[2] == 'N' ):
        lat += float(c.pop(0))/60
        lat += float(c.pop(0))/3600
        c.pop(0)
    elif ( len(c) > 2 and c[2] == 'S' ):
        lat += float(c.pop(0))/60
        lat += float(c.pop(0))/3600
        lat = -lat
        c.pop(0)

    # on fait de même avec la longitude
    lon = float(c.pop(0))
    if (c[0] == 'W'):
        lon = -lon
        c.pop(0)
    elif ( c[0] == 'E' ):
        c.pop(0)
    elif ( len(c) > 1 and c[1] == 'W' ):
        lon += float(c.pop(0))/60
        lon = -lon
        c.pop(0)
    elif ( len(c) > 1 and c[1] == 'E' ):
        lon += float(c.pop(0))/60
        c.pop(0)
    elif ( len(c) > 2 and c[2] == 'W' ):
        lon += float(c.pop(0))/60
        lon += float(c.pop(0))/3600
        lon = -lon
        c.pop(0)
    elif ( len(c) > 2 and c[2] == 'E' ):
        lon += float(c.pop(0))/60
        lon += float(c.pop(0))/3600
        c.pop(0)
    
    # on renvoie un dictionnaire avec les deux valeurs
    return {'lat':lat, 'lon':lon }

#
# Récupération des coordonnées de la capitale depuis l'infobox d'un pays
#
def get_coords(wp_info):

    # S'il existe des coordonnées dans l'infobox du pays
    # (cas le plus courant)
    if 'coordinates' in wp_info:

        # (?i) - ignorecase - matche en majuscules ou en minuscules
        # ça commence par "{{coord" et se poursuit avec zéro ou plusieurs
        #   espaces suivis par une barre "|"
        # après ce motif, on mémorise la chaîne la plus longue possible
        #   ne contenant pas de },
        # jusqu'à la première occurence de "}}"
        m = re.match('(?i).*{{coord\s*\|([^}]*)}}', wp_info['coordinates'])

        # l'expression régulière ne colle pas, on affiche la chaîne analysée pour nous aider
        # mais c'est un aveu d'échec, on ne doit jamais se retrouver ici
        if m == None :
            print(' Could not parse coordinates info {}'.format(wp_info['coordinates']))
            return None

        # cf. https://en.wikipedia.org/wiki/Template:Coord#Examples
        # on a récupère une chaîne comme :
        # 57|18|22|N|4|27|32|W|display=title
        # 44.112|N|87.913|W|display=title
        # 44.112|-87.913|display=title
        str_coords = m.group(1)

        # on convertit en numérique et on renvoie
        if str_coords[0:1] in '0123456789':
            return cv_coords(str_coords)

    # Aveu d'échec, on ne doit jamais se retrouver ici
    print(' Could not fetch country coordinates')
    return None

#
# Enregistrement d'un pays dans la base de données
#
def save_country(conn,country,info):

    # préparation de la commande SQL
    c = conn.cursor()
    sql = 'INSERT OR REPLACE INTO countries VALUES (?, ?, ?, ?, ?)'

    # les infos à enregistrer
    name = get_name(info)
    capital = get_capital(info)
    coords = get_coords(info)

    # soumission de la commande (noter que le second argument est un tuple)
    c.execute(sql,(country, name, capital, coords['lat'],coords['lon']))
    conn.commit()

#
# Lecture d'un pays depuis la base de données
#
def read_country(conn,country):
    
    # préparation de la commande SQL
    c = conn.cursor()
    sql = 'SELECT * FROM countries WHERE wp=?'

    # récupération de l'information (ou pas)
    c.execute(sql,(country,))
    r = c.fetchone()
    
    return r

#
# importer les donnes de continents
#
def init_db(continent,conn):
    with ZipFile('{}.zip'.format(continent),'r') as z:
        files = z.namelist()
        for f in files:
            country = f.split('.')[0]
            print(country)
            info = json.loads(z.read(f))
            save_country(conn,country,info)

init_db('oceania',conn)
init_db('south_america',conn)