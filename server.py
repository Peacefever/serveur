#-* encoding:utf-8 -*-
from flask import Flask, request
from flask_cors import CORS
from db import Db
from random import *
import json
from Map import *
from others import *

app = Flask(__name__)
app.debug = True
CORS(app)

timestamp = 0

#Database
@app.route('/debug/db/reset')
def init_db():
	'''
	Initialisation de la base de données
	'''
	db = Db()
	db.executeFile('database.sql')
	db.close()
	return 'Database OK'

#JAVA
@app.route('/map', methods=['GET'])
def get_map():
	players = get_players_ingame(default_game)

	#Il n'y a aucun joueur dans la partie
	if (len(players) == 0):
		itemsByPlayer = {}
		playerInfo = {}
		drinksByPlayer = {}

	#Il y a au moins un joueur dans la partie
	itemsByPlayer = {}
	playerInfo = {}
	drinksByPlayer = {}
	for aplayer in players:
		itemsByPlayer[aplayer['name_player']] = get_mapitems(aplayer['id_player'])
		playerInfo[aplayer['name_player']] = get_player_infos(aplayer['id_player'], default_game, "sold")
		drinksByPlayer[aplayer['name_player']] = get_drinksOffered(aplayer['id_player'], "sold")

	print(playerInfo)
	resp = {
		"map": {
			"region": get_region(),
			"ranking":get_ranking(),
			"itemsByPlayer": itemsByPlayer,
			"playerInfo":playerInfo,
			"drinksByPlayer":drinksByPlayer
		}
	}
	return to_make_response(resp, 200)

#Client html
@app.route('/map/<playerName>', methods = ['GET'])
def get_map_player(playerName):
	theplayer = get_player_fromName(playerName, default_game)
	
	#Le joueur n'existe pas dans la base de données
	if (len(theplayer) == 0):
		return to_make_response('Player do not exist', 404)

	#Formattage de la réponse
	resp = {
		"availableIngredients":get_available_ingredients(theplayer[0]['cash_player']),
		"map": {
			"region": get_region(),
			"ranking": get_ranking(),
			"itemsByPlayer": {
				playerName: get_mapitems(theplayer[0]['id_player'])
			}
		},
		"playerInfo": {
			playerName : get_player_infos(theplayer[0]['id_player'], default_game, "prod")
		}
	}

	return to_make_response(resp)

@app.route('/metrology', methods=['GET'])
def metro_get_infos():	
	#Cette fonction envoie au client des données de temps
	#et de météo relative à l'heure actuelle du jeu.
	#Cela reviens à envoyer la dernière ligne de la table Weather
	db = Db()
		#Récupération du nombre de ligne dans la table Weather
	number_elements = db.select("SELECT COUNT(*) FROM Weather")
	if (number_elements[0]['count'] == 0):
		return to_make_response('Not found', 404)

		#Récupération de l'id de la dernière ligne de la table Weather
	w_id_max = db.select("SELECT MAX(id_weather) FROM Weather")
		
		#Echec récupération id dernière ligne de la table Weather
	if (len(w_id_max) != 1 or w_id_max == None):
		return {}

		#Récupération de la dernière ligne de la table Weather
	w_last_infos = db.select("SELECT now_weather, tomorrow_weather FROM Weather \
		WHERE id_weather = %d" %(w_id_max[0]['max']))

		#Erreur récupération dernière ligne de la table Weather
	if (len(w_last_infos) == 0 or w_last_infos == None):
		return {}
	db.close()
	
	#Mise en place de la réponse au client
		#Renseignement du tableau de dictionnaire ayant pour clé "weather"
	i = 0
	w_tab = []
	while(i < 2):
		if (i == 0):
			adict = {"dfn": i, "weather":w_last_infos[0]['now_weather']}
		if (i == 1):
			adict = {"dfn": i, "weather":w_last_infos[0]['tomorrow_weather']}
		w_tab.append(adict)
		i = i + 1

	#Formattage de la réponse au client
	resp = {
		"timestamp":timestamp, #le timestamps est en nombre d'heure
		"weather": w_tab
	}
	return to_make_response(resp)

@app.route('/ingredients', methods=['GET'])
def all_ingredients():
	'''
	Cette route permet de récupérer l'ensmeble des ingrédients présents
	dans la base de données
	'''
	db = Db()

	#On compte le nombre d'ingrédients dans la table "Ingredient"
	number_ingredients = db.select("SELECT COUNT(*) FROM Ingredient")

	#Les ingrédients sont déjà entrés en base de données
	if (len(number_ingredients) != 1):
		return internal_server_error()

	#S'il n'y a aucun élément dans la base
	if (number_ingredients[0]['count'] == 0):
		return to_make_response('Aucun ingrédient enregistré',404)

	#S'il y a un ou plusieurs éléments dans la base, on les recupère et on les présente dans une liste.
	ingredients = db.select("SELECT name_ingredient as name, price_ingredient as cost FROM Ingredient")

	if (len(ingredients) == 0 or ingredients == None):
		return []
	
	db.close()
	return to_make_response(ingredients)

@app.route('/metrology', methods = ['POST'])
def save_metro():
	data = request.get_json()
	#data = {"timestamp":"1","weather":[{"dfn":0, "weather":"sunny"}, {"dfn":1, "weather":"rainny"}]}

	if (isValidData(data) == False):
		return bad_request()

	if not ('timestamp' in data and 'weather' in data):
		return bad_request()

	#On ajoute au timestamp le temps recu
	global timestamp
	timestamp =  timestamp + 1 #int(data['timestamp']) #Jusqu'a ce l'on est 24
	print(timestamp)

	#Récupération de la météo.
	w_request = data['weather']
	for aweather in w_request:
		if (aweather['dfn'] == 0):
			w_now = aweather['weather']
		if (aweather['dfn'] == 1):
			w_forecast = aweather['weather']

	#Vérification du nombre d'instances Weather dans la base de données
	db = Db()
	number_elements = db.select("SELECT COUNT(*) FROM Weather")
	print(number_elements[0]['count'])
	db.close()

	#Nous n'avons aucun élément en base de données
	#Cela signifie que c'est le premier jour
	if (number_elements == None or number_elements[0]['count'] == 0):
		#On crée une instance de Weather qu'on ajoute en base
		db = Db()
		w_creation = db.select("INSERT INTO Weather (now_weather, tomorrow_weather, day_weather) \
							VALUES (%(now)s, %(tomorrow)s, %(day)s) RETURNING id_weather", {
							"now": w_now,
							"tomorrow": w_forecast,
							"day": 1
							})
		db.close()

		if (len(w_creation) == 0):
			return internal_server_error()

		db = Db()
		print(db.select("SELECT * FROM Weather"))
		db.close()

	lastGameDay = get_current_day()

	if (lastGameDay == -1):
		return internal_server_error()

	#Basculement au jour j+1
	if (timestamp % 24 == 0):
		#On incrément le jour courant
		lastGameDay = lastGameDay + 1

		#On crée une nouvelle instance de weather avec les données recues
		db = Db()
		w_creation = db.select("INSERT INTO Weather(now_weather, tomorrow_weather, day_weather)\
			VALUES (%(now)s, %(tomorrow)s, %(day)s) RETURNING id_weather", {
				"now":w_now,
				"tomorrow":w_forecast,
				"day":lastGameDay
				})
		print(db.select("SELECT * FROM Weather"))
		db.close()

		#Si la création s'est mal passé
		if (len(w_creation) == 0):
			return internal_server_error()


		#Prise en compte des actions
		db = Db()
		players = db.select("SELECT *  FROM Player WHERE ingame_player = %d" %(default_game))

		for aplayer in players:
			print(aplayer['id_player'])
			#Calcul du profit
			profit = get_profits(aplayer['id_player'], 1)

			#Calcul du cash total
			cash_player = aplayer['cash_player'] + profit

			#print("AVANT MODIFICATION DU PLAYER")
			#print(db.select("SELECT * FROM Player WHERE id_player = %d" %(aplayer['id_player'])))
			#print("FIN AVANT MODIF PLAYER")

			#On update les champs des joueurs concernant leur décision, ainsi que le cash
			db.execute("UPDATE Player SET cash_player = %(cash)s, action_buynewrecipe = %(buyRecipe)s,\
				action_buyadds = %(buyAds)s, action_prodrecipe = %(actionProd)s WHERE id_player =%(id)s",{
				"cash": cash_player,
				"buyRecipe":False,
				"buyAds":False,
				"actionProd":False,
				"id":aplayer['id_player']
				})

			#On verifie l'update
			#print("APRÈS MODIFICATION")
			#print(db.select("SELECT * FROM Player WHERE id_player = %d" %(aplayer['id_player'])))
			#print("FIN APRES MODIFICATION")
		db.close()
		return to_make_response('', 201)
	return ('', 201)

@app.route('/players', methods = ['POST']) #Requete ne fonctionnant pas une fois sur
def join_game():
	'''
	Cette route permet au client de se connecter à
	une partie
	'''
	#Recupération de la donnée
	data = request.get_json()
	print(data)

	#On détermine si la donnée peut être traité.	
	if (isValidData(data) == False):
		return bad_request()

	if not ('name' in data):
		return bad_request()

	if ((data['name'] == '') or (data['name'].isspace()==True)):
		return bad_request()

	#La donnée peut être traitée.
	db = Db()
	
	isInbd = is_present_pseudo_indb(data['name'])
	print(isInbd)

	#Le joueur est déjà présent dans la base de données
	if (isInbd == True):
		#On le connecte en lui renvoyant ses données
		player = db.select("SELECT * FROM Player WHERE (ingame_player = %(id)s AND name_player = %(name)s)", {
			"id": default_game,
			"name":data['name']
			})

		resp = {
			"name":data['name'],
			"location":{
				"latitude": player[0]['lat_player'],
				"longitude":player[0]['lon_player']
			},
			"infos": get_player_infos(player[0]['id_player'], default_game, "prod")
		}
		return to_make_response(resp)
	db.close()

	#Le joueur n'est pas présent dans la base de données
	#Alors on le crée, on le connecte et on envoie les données voulues au client
	resp = join_new_player(data['name'], default_game)
	if(resp == -1):
		return internal_server_error()
	return to_make_response(resp)


'''
@app.route('/sales', methods =['POST'])
@app.route('/actions/<playerName>', methods = ['GET'])
'''

if __name__ == '__main__':
	app.run()