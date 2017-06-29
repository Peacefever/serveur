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
#Fonctionnel
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
#Fonctionnel
@app.route('/map', methods=['GET'])
def get_map():
	'''
	Cette fonction permet l'envoie au client de l'ensemble des 
	données concernant la map
	'''
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

#curl -X POST -i -d '{"sales":[{"player":"toto", "item":"Limonade", "quantity":10}]}' -H 'Content-Type: application/json' http://localhost:5000/sales
#Fonctionnel
@app.route('/sales',methods =['POST'])
def save_sales():
	'''
	Cette route permet la sauvegarde en base de données des ventes
	effectuées par le joueur par boisson (recette) et par jour
	'''
	data = request.get_json()

	print("DATA")
	print(data)
	print("DATA")
	if (isValidData(data) == False):
		return bad_request()

	if not ('sales' in data):
		return bad_request()

	if not (isinstance(data['sales'], list)):
		return bad_request()

	#Récupération du jour actuel
	currentday = get_current_day()

	if (currentday == -1):
		return internal_server_error()

	#La donnée est conforme, donc on la traite
	#On enregistre les données transmises par le JAVA en fonction de la valeur des clés
	#de chaque dictionnanire (dict) dans la liste [sales]
	for asold in data['sales']:
		#Récupération du nom du joueur, de l'item venu, de la quantité vendue
		the_player = asold['player']
		the_item = asold['item'] #C'est en fait une recette
		the_quantity = asold['quantity']

		#Récupération de l'id du serveur à partir de son nom
		db = Db()
		player = db.select("SELECT id_player FROM Player WHERE (name_player = %(name)s)",{
			"name":the_player
			})

		#Récupération de l'id de la recette
		recipe_id = db.select("SELECT id_recipe FROM Recipe WHERE name_recipe = %(item)s",{
			"item":the_item
			})

		print("THE RECIPE")
		print(db.select("SELECT * FROM Sales"))
		print("THE RECIPE")

		if (recipe_id == None or len(recipe_id) == 0):
			return ' ', 400

		#On suppose que le java nous donne l'ensemble des ventes à la fin de la journée.
		#Ou même heure par heure (c'est le même fonctionnement)
		#On crée une instance vente pour chaque produit, pour chaque jour, si celle-ci n'existe pas
		exist = db.select("SELECT * FROM Sales WHERE (id_player = %(p_id)s AND id_recipe = %(r_id)s)" , {
			"p_id":player[0]['id_player'],
			"r_id":recipe_id[0]['id_recipe']
			})

		#L'instance n'existe donc pas
		if (exist == None or len(exist) == 0):
			#Donc on la crée
			db.execute("INSERT INTO Sales (quantity_sales, day_sales, id_player, id_recipe) VALUES \
				(%(quantity)s, %(day)s, %(p_id)s, %(r_id)s)", {
				"quantity":the_quantity,
				"day":currentday,
				"p_id": player[0]['id_player'],
				"r_id": recipe_id[0]['id_recipe']
				})

			#Verfification de la création
			exist2 = db.select("SELECT * FROM Sales WHERE (id_player = %(p_id)s AND id_recipe = %(r_id)s)" , {
				"p_id":player[0]['id_player'],
				"r_id":recipe_id[0]['id_recipe']
				})
			print("INSERT")
			print(db.select("SELECT * FROM Sales"))
			return to_make_response(' ', 201)

		#Dans le cas où l'isntance existe, on l'update
		db.execute("UPDATE Sales SET quantity_sales = %d, day_sales = %d WHERE (id_player = %d\
		 AND id_recipe = %d)" %(the_quantity, currentday, player[0]['id_player'], recipe_id[0]["id_recipe"]))
		
		print("CE QUI EST EN update")
		print(db.select("SELECT * FROM Sales"))
		db.close()

	return to_make_response(' ', 201)

#Client HTML
@app.route('/map/<playerName>', methods = ['GET'])
def get_map_player(playerName):
	'''
	Cette route permet d'envoyer au client les données de la map
	concernant uniquement un joueur
	'''
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

#Fonctionnel
@app.route('/metrology', methods=['GET'])
def metro_get_infos():
	'''
	Cette route permet de transmettre au client les données de 
	météo.
	'''	
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
	'''
	Cette route permet de sauvegarder en base de données les données 
	concernant la météo et le temps
	'''
	data = request.get_json()
	print(data)
	#data = {"timestamp":"1","weather":[{"dfn":0, "weather":"sunny"}, {"dfn":1, "weather":"rainny"}]}

	if (isValidData(data) == False):
		return bad_request()

	if not ('timestamp' in data and 'weather' in data):
		return bad_request()

	#On ajoute au timestamp le temps recu
	global timestamp
	timestamp = int(data['timestamp'])   #timestamp + 1 #int(data['timestamp']) #Jusqu'a ce l'on est 24
	print(timestamp)
	
	#Récupération de la météo.
	w_now = data['weather'][0]['weather']
	w_forecast = data['weather'][1]['weather']
	print("on passe la")
	print(w_now)
	print(w_forecast)

	#Vérification du nombre d'instances Weather dans la base de données
	db = Db()
	number_elements = db.select("SELECT COUNT(*) FROM Weather")
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
		db.close()

	lastGameDay = get_current_day()
	print("JE passe ici")

	if (lastGameDay == -1):
		return internal_server_error()

	#Basculement au jour j+1
	if (timestamp % 24 == 0):
		print("JE passe la ")
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
		db.close()

		#Si la création s'est mal passé
		if (len(w_creation) == 0):
			return internal_server_error()

		#Prise en compte des actions
		db = Db()
		players = db.select("SELECT *  FROM Player WHERE ingame_player = %d" %(default_game))

		for aplayer in players:
			#Calcul du profit
			profit = get_profits(aplayer['id_player'], 1)

			#Calcul du cash total
			cash_player = aplayer['cash_player'] + profit

			#On update les champs des joueurs concernant leur décision, ainsi que le cash
			db.execute("UPDATE Player SET cash_player = %(cash)s, action_buynewrecipe = %(buyRecipe)s,\
				action_buyadds = %(buyAds)s, action_prodrecipe = %(actionProd)s WHERE id_player =%(id)s",{
				"cash": cash_player,
				"buyRecipe":False,
				"buyAds":False,
				"actionProd":False,
				"id":aplayer['id_player']
				})


		#Verif
		print(db.select("SELECT * FROM Weather"))
		db.close()
		return to_make_response('', 201)
	return ('', 201)

@app.route('/players', methods = ['POST'])
def join_game():
	'''
	Cette route permet au client de se connecter à
	une partie
	'''
	#Recupération de la donnée
	data = request.get_json()
	
	return data['name']

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
			"info": get_player_infos(player[0]['id_player'], default_game, "prod")
		}
		return to_make_response(resp)
	db.close()

	#Le joueur n'est pas présent dans la base de données
	#Alors on le crée, on le connecte et on envoie les données voulues au client
	resp = join_new_player(data['name'], default_game)
	if(resp == -1):
		return internal_server_error()
	return to_make_response(resp)

#curl -X POST -i -d '{"actions":[{"kind":"recipe", "recipe":{"name":"Limonade", "ingredients":[{"name":"Limonade", "cost":12}]}}, {"kind":"ad", "nb":12}, {"kind":"drinks", "prepare":{"Limonade":12}, "price":{"Limonade":0.25}}]}' -H 'Content-Type: application/json' http://127.0.0.1:5000/actions/toto
@app.route('/actions/<playerName>', methods = ['POST'])
def save_action_choices(playerName):
	'''
	Cette route permet d'enregistré en base de données les choix
	d'un joueur durant la partie
	'''
	#Récupération du choix du joueur
	data = request.get_json()

	print("je recois quelque cjhose")
	print(data)
	print("hello")

	#Validation de la donnée pour traitement
	if (isValidData(data) == False):
		return bad_request()

	if not ('actions' in data):
		return bad_request()

	if not (isinstance(data['actions'], list)):
		return bad_request()

	if len(data['actions']) == 0:
		return bad_request()

	#Récupération de l'id du player à partir de son nom
	db = Db()
	player = db.select("SELECT * FROM Player WHERE name_player = %(name)s", {
		"name": playerName
		})
	db.close()

	#Récupération du jour courant
	currentday = get_current_day()

	if (currentday == -1):
		return {}

	#Sauvegarde des données en base de données en fonction du kind.
	#La sauvegarde des données se fera au jour j+1, pour que les choix du joueur
	#soient appliqués le jour suivant la décision.

		#On parcours l'ensemble du tableau d'action
	for anAction in data['actions']:
		if (anAction['kind'] == 'ad'):
			save_kind_ad_action(anAction, player[0]['id_player'], (currentday + 1))
		if (anAction['kind'] == 'drinks'):
			save_kind_prod_action(anAction, player[0]['id_player'], (currentday + 1))
		#if (anAction['kind'] == 'recipe'):
		#	save_kind_buy_recipe_action(anAction, player[0]['id_player'], (currentday + 1))
	
	#Détermination du cout total des actions
	tot_cost_actions = get_totalCosts(player[0]['id_player'], (currentday + 1))

	#Récupération du cash total du joueur. Son cash est toujour au jour actuel
	player_cash = player[0]['cash_player']

	#Formattage de la réponse suivant le cash du joueur
	#Le joueur n'a pas assez d'argent
	if (player_cash < tot_cost_actions):
		resp = {
			"sufficientFunds":False,
			"totalCost":tot_cost_actions
		}

		db = Db()
		print("fin 1")
		table1 = db.select("SELECT * FROM Production")
		table2 = db.select("SELECT * FROM Adspace")
		print(table1)
		print(table2)
		print("Fin 2")
		db.close()
		return to_make_response(resp)

	#Le joueur a assez d'argent
	diff = player_cash - tot_cost_actions

	db = Db()
		#On met à jour le cash du joueur en question dans la base de données
	db.execute("UPDATE Player SET cash_player = %f WHERE id_player = %d" %(diff, player[0]['id_player']))
	db.close()

	#Fromattage de la réponse au client de la réponse au client
	resp = {
		"sufficientFunds": True,
		"totalCost":tot_cost_actions
	}


	db = Db()
	print("fin 1")
	table1 = db.select("SELECT * FROM Production")
	table2 = db.select("SELECT * FROM Adspace")
	print(table1)
	print(table2)
	print("Fin 2")
	db.close()
	return to_make_response(resp)

if __name__ == '__main__':
	app.run(host = "0.0.0.0", port = 5000) 
