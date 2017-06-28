#-* encoding:utf-8 -*-
from flask import Flask, request
from flask_cors import CORS
from db import Db
from random import *
import json
from Map import *
from others import *

app = Flask(__name__, static_url_path='')
app.debug = True
CORS(app)

timestamp = 0

@app.route("/")
def connexion():
   return app.send_static_file('connexion.html')

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
	'''
	Cette fonction envoie au client des données de temps
	et de météo relative à l'heure actuelle du jeu.
	'''
	#Cela reviens à envoyer la dernière ligne de la table Weather
	db = Db()
		#Récupération du nombre de ligne dans la table Weather
	number_elements = db.select("SELECT COUNT(*) FROM Weather")
	print(number_elements[0]['count'])
	if (number_elements[0]['count'] == 0):
		return to_make_response('Not found', 404)

		#Récupération de l'id de la dernière ligne de la table Weather
	w_id_max = db.select("SELECT MAX(id_weather) FROM Weather")
		
		#Echec récupération id dernière ligne de la table Weather
	if (len(w_id_max) != 1):
		return to_make_response('Internal Server Error', 500)

		#Récupération de la dernière ligne de la table Weather
	w_last_infos = db.select("SELECT now_weather, tomorrow_weather FROM Weather \
		WHERE id_weather = %d" %(w_id_max[0]['max']))

		#Erreur récupération dernière ligne de la table Weather
	if (len(w_last_infos) == 0):
		return internal_server_error()
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

	print (w_tab)

	#Formattage de la réponse au client
	resp = {
		"timestamp":define_hours(timestamp),
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
		return to_make_response('Aucun ingrédient enregistré')

	#S'il y a un ou plusieurs éléments dans la base, on les recupère et on les présente dans une liste.
	ingredients = db.select("SELECT name_ingredient as name, price_ingredient as cost FROM Ingredient")
	
	db.close()
	return to_make_response(ingredients)



#A TESTER
#ROUTE AVEC FONCTION PRENANT EN COMPTE LE BASCULEMENT DES JOURS.
#A TESTER
#ROUTE AVEC FONCTION PRENANT EN COMPTE LE BASCULEMENT DES JOURS.
#A tester mais sans aucun doute fonctionnelle.
@app.route('/metrology', methods = ['POST'])
def metro_save_infos():
	#Réception de la donnée
	datas = request.get_json()

	#Vérficiation de la donnée
	if (isValide(datas) == False):
		return to_make_response('Bad Request', 400)

	if not('timestamp' in datas and 'weather' in datas):
		return to_make_response('Bad Request', 400)

	#La donnée est conforme pour être traitée
	#Stockage du timestamp dans une variable globale du serveur
	global timestamp
	timestamp = (timestamp + datas['timestamp']) * 3600

	#Récupération de la météo actuelle (0) et prévisionnelle(1)
	w_request = datas['weather']
	for aweather in w_request:
		if (aweather['dfn'] == 0): #Météo actuelle
			w_now =  aweather['weather']
		if (aweather['dfn'] == 1): #Prévision pour le lendemain
			w_forecast = aweather['weather']

	#Détermination du jour actuel en fonction de la nouvelle valeur du timestamp
	current_day = define_day(timestamp)

	#Verification du nombre d'éléments dans la base de données
	db = Db()
	number_elements = db.select("SELECT COUNT(*) FROM Weather")
	print(number_elements)
	db.close()

	if (len(number_elements) != 1):
		return to_make_response('Internal Server Error', 500)

	#S'il n'y a aucun éléments en base de données
	#Cela signifie que c'est le premier jour
	if (number_elements[0]['count'] == 0):
		db = Db()
		w_creation = db.select("INSERT INTO Weather (now_weather, tomorrow_weather, day_weather) \
							VALUES (%(now)s, %(tomorrow)s, %(day)s) RETURNING id_weather", {
							"now": w_now,
							"tomorrow": w_forecast,
							"day": current_day
							})
		db.close()

		#Si l'instance de la table n'est pas créée
		if (len(w_creation) != 1):
			return to_make_response('Internal Server Error', 500)

	#S'il y a des éléments en base de données
		#On ne crée plus d'instance tant que un jour complet n'est pas passé.
	#Récupération du dernier jour mise en base
	last_day = get_lastGameDay()

	if ((current_day != last_day)):#On est donc passé au jour (j+1)
		#On incrémente ce jour de 1
		last_day = last_day + 1

		#On crée une nouvelle instance les nouvelles données reçues
		db = Db()
		w_creation = db.select("INSERT INTO Weather(now_weather, tomorrow_weather, day_weather)\
			VALUES (%(now)s, %(tomorrow)s, %(day)s) RETURNING id_weather", {
				"now":w_now,
				"tomorrow":w_forecast,
				"day":last_day
				})
		print(w_creation)
		db.close()

		if (len(w_creation) == 0):
			return to_make_response('Internal Server Error', 500)

		#PRIS EN COMPTE DES ACTIONS
			#On met à jour les champs de l'ensemble des joueurs.
				#Récupération de l'ensemble des joueurs de la partie
		db = Db()
		players = db.select("SELECT * FROM Player WHERE ingame_player= %d" %(id_game_default))

		#Pour chacun des joueurs de la partie
		for aplayer in players:
			#On calcule le profit du jour précédent
			profit = get_profit(players, aplayer['name_player'], day = 1)

			#On récupère le cash du player et on calcule "profit + cash"
			cashTotal = aplayer['cash_player'] + profit

			#On update les champs des joueurs concernant leur décision, ainsi que le cash
			db.execute("UPDATE Player SET cash_player = %(cash)s, action_buynewrecipe = %(buyRecipe)s,\
				action_buyadds = %(buyAds)s, action_prodrecipe = %(actionProd)s",{
				"cash": cashTotal,
				"buyRecipe":False,
				"action_buyadds":False,
				"actionProd":False 
				})
		db.close()


		return to_make_response('', 201)

	return to_make_response(' ', 200)
#Non fonctionnel (allez savoir pk)
#Avoir zvec les autres pour les tests 
#curl -X POST -H "Content-Type: application/json" -d '{"sales":[{"toto", "limonade", "quantity"}]}' http://127.0.0.1:5000/sales
@app.route('/sales', methods =  ['POST'])
def collect_sales():
	'''
	Cette route permet de sauvegarder le nombre de ventes
	de chaque boissons pour un joeuur donné
	'''
	#datas = request.get_json()
	datas = {"sales":[{"player":"toto", "item":"Limonade", "quantity":2}]}

	if (isValidData(datas) == False):
		return bad_request()

	if not ('sales' in datas):
		return bad_request()

	#Récupération du jour courant de jeu
	currentDay = get_current_day()

	#La donnée est conforme a ce que nous attendions, on la traite. (concerne la table Sales)
	#Le but est de créer une instance de Sales par boisson et par jour pour un joueur donné
	db = Db()
	print("debug")
	print(db.select("SELECT * FROM Sales"))
	print("FIN")

	print(datas['sales'])
	for dictObject in datas['sales']:
		#Récupération de l'id du joueur
		playerID = db.select("SELECT id_player FROM Player WHERE (name_player = %(name)s)", {
			"name":dictObject['player']
		})

		if (len(playerID) != 1):
			print("1")
			return internal_server_error()

		#Récupération de l'id de la recette vendue
		recipeID = db.select("SELECT id_recipe FROM Recipe WHERE (name_recipe = %(name)s)", {
			"name":dictObject['item']
			})

		print(recipeID)

		if (len(recipeID) != 1):
			print("2")
			return internal_server_error()

		#Requete A TESTER À PART EN PRIORITÉ
		#Vérification que l'instance de la table Sales que l'on va créer n'est pas déjà présente en base
		presentInDB = db.select("SELECT * FROM Sales WHERE (day_sales = %d AND \
			id_player = %d AND id_recipe = %d)" %(currentDay, playerID[0]['id_player'], recipeID[0]['id_recipe']))

		print(presentInDB)

		if (len(presentInDB) != 1):
			print("3")
			return internal_server_error()


		#Cas où il n'y a aucune ligne vente pour ce jour, cet id_recipe et cet id_joueur
			#Alors on crée une nouvelle instance de Sales, qui sera représentée en base par une ligne
		sold_creation = db.select("INSERT INTO sales (quantity_sales, day_sales, id_player, id_recipe) VALUES (%(quantity)s, %(day)s, %(p_id)s, %(r_id)s)",{"quantity":dictObject['quantity'],"day": currentDay, "p_id":playerID[0]['id_player'], "r_id":recipeID[0]['id_recipe']}
					#"p_id":playerID[0]['id_player'],
		#Cas où il y a déjà une ligne, on la récupère et on effectue dessus une mise à jour
			#Récupération de la ligne
		soldToModify = db.select("SELECT * FROM Sales WHERE (day_sales = %(day)s AND id_player = %(p_id)s\
			AND id_recipe = %(r_id)s)", {
		"day":currentDay,
		"p_id":playerID[0]['id_player'],
		"r_id":recipeID[0]['id_recipe']
		})

		if (len(soldToModify) != 1):
			print('4')
			return to_make_response('Internal Server Error', 500)

			#Update de la ligne en question
		db.execute("UPDATE Sales SET (quantity_sales = %(quantity)s, day_sales =%(day)s, \
			id_player = %(p_id)s, id_recipe = %(r_id)s WHERE day_sales = %(old)s ANd id_player = %(old_p)s AND\
			id_recipe = %(old_r)s",{
			"quantity": dictObject['quantity'],
			"day": currentDay,
			"p_id": playerID,
			"r_id": recipeID,
			"old":soldToModify[0]['day_sales'],
			"old_p":soldToModify[0]['id_player'],
			"old_r":soldToModify[0]['id_recipe']
			})

		print(db.select("SELECT * FROM Sales"))
	db.close()
	return to_make_response('', 201)


#pas du tout fonctionnelle (pk? un grand mystere)
#curl -X POST -H "Content-Type: application/json" -d '{"name":" "}' http://127.0.0.1:5000/players
@app.route('/players', methods = ['POST'])
def join_game():
	'''
	Rejoindre une partie
	'''
	data = request.get_json()

	#Vérification de la donnée reçue
	if (isValidData(data) == False):
		return bad_request()

	if not ('name' in data):
		return bad_request()

	if ((data['name'] == '') or (data['name'].isspace()==True)):
		return bad_request()

	db = Db()
	print(db.select("SELECT * FROM Player"))

	#Verif que le player est dans la base ou non
	in_db = is_present_pseudo_indb(data['name'])
	print(in_db)
	print("\n")
	print(db.select("SELECT * FROM Player"))

	if (in_db == True):
		player = db.select("SELECT * FROM Player WHERE (ingame_player = %(id_game)s AND  name_player = %(name)s)", {
			"id_game": default_game,
			"name":data['name']
		})

		resp = {
		'name': data['name'],
		"location": {
				"latitude": player[0]['lat_player'],
				"longitude": player[0]['lon_player']
		},
		"infos" :get_player_infos(player[0]['id_player'], default_game, "prod")
		}
		return to_make_response(resp)

	print("je suiio la ")
	join = join_new_player(data['name'], default_game)
	print(join)
'''
	print(is_present_pseudo_indb(data['name']))
	#La donnée peut être traitée
		#Le joueur est absent de la base de données
	if (is_present_pseudo_indb(data['name']) == False):
		#On le crée, et on le connecte à la partie
		thenewplayer = join_new_player(data['name'],default_game)

		if(thenewplayer == "Error -500"):
			return internal_server_error()
		
		return thenewplayer

	resp = {}
	print("je passe la ")
		#Le joueur est déjà présent dans la game
		#On récuère son id
	db = Db()
	player = db.select("SELECT * FROM Player WHERE (ingame_player = %(id_game)s AND  name_player = %(name)s)", {
		"id_game": default_game,
		"name":data['name']
		})
	db.close()

	print(player)
	resp = {
		'name': data['name'],
		"location": {
				"latitude": player[0]['lat_player'],
				"longitude": player[0]['lon_player']
		},
		"infos" :get_player_infos(player[0]['id_player'], default_game, "prod")
		}
	'''

if __name__ == '__main__':
	app.run()




'''
S'il y a le pseudo en base de données on envoie les données du joeuur
Sinon on crée le joueur et tout ce qui est necessaire à son commencement dans la partie.
S'il n'est pas connecté on le connecte aussi.

Le serveur fonctionne de la facon suivante:
	Quand on se connecte on se connecte
	Quand on quitte la partie on quitte définitivement. 
'''
