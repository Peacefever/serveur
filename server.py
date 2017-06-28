#-* encoding:utf-8 -*-
from flask import Flask, request
from flask_cors import CORS
from db import Db
from random import *
import json
from mserver import *

app = Flask(__name__, static_url_path='')
app.debug = True
CORS(app)

id_game_default = 1
timestamp = 0
default_cash_game = 20.0
default_rayon_player = 1.0

@app.route("/")
def connexion():
  return app.send_static_file('connexion.html')

@app.route('/debug/db/reset')
def reset_db():
	'''
	Cette route permet de réinitialiser de la base de données
	'''
	db = Db()
	db.executeFile("database.sql")
	db.close()
	return "Done."

#Ici on considère dans un premier temps que l'ensemble des boissons dont dispose le joueur (drinksByPlayer)
#sont proposé à la vente(drinkOffred dans itemsbyPlayer)
#Dans l'idéal plus tard, il faut ajouté un attribut en base pour dire que la recette est proposé
#ou non à la vente.
@app.route('/map', methods = ['GET']) #Manque le ranking
def get_map():
	'''
	Cette route transmet au client l'ensemble des éléments de
	la map.
	'''
	db = Db()
		#Récupération des données de la table Map et mise en forme de la réponse pour la clé "region"
	map_datas = db.select("SELECT * FROM Map")

	region = {
		"center": {
			"latitude": map_datas[0]['lat_map'],
			"longitude": map_datas[0]['lon_map']
		},
		"span": {
			"latitudeSpan": map_datas[0]['lat_span_map'],
			"longitudeSpan": map_datas[0]['lon_span_map']
		}
	}

	#Récupération du jour actuel de jeu
	current_day = get_lastGameDay()

	#Récupération des joueurs connectés à la partie
	players = db.select("SELECT * FROM Player WHERE ingame_player = %d" %(id_game_default))


	#Récupération des données de la table Addspace
	#Et mise en forme de la réponse pour la clé itemsByPlayer
	itemsByPlayer = {}
	for player in players:
		#Récupération des données de la table Addspace
		addspace_datas = db.select("SELECT * FROM Addspace WHERE (id_player = %d AND day_addspace = %d)"\
			%(player['id_player'], current_day))

		#Remplissage des items Add du joueur dans un tableau
		itemsplayer = []
		for add in addspace_datas:
			itemsplayer.append({
				"kind":"add",
				"owner":player['name_player'],
				"location": {
					"latitude": add['lat_addspace'],
					"longitude": add['lon_addspace']
				},
				"influence": add['influence_addspace']
				})

		#Remplissage de l'item stand du joueur (le joueur est en fait le stand)
		itemsplayer.append({
			"kind":"stand",
			"owner": player['name_player'],
			"location": {
				"latitude":player['lat_player'],
				"longitude":player['lon_player']
			},
			"influence":player['rayon_player']
			})

		#Mise en forme du dictionnaire itemsForPlayer
		itemsByPlayer[player['name_player']] = itemsplayer

	#Récupération des données de la table Recipe calcul du profit
	#Et mise en forme de la réponse pour la clé "playerInfos"
	playerInfosValue = {}
	for player in players:
		#On récupère les données des tables Recipe et Sales
		recipe_datas = db.select("SELECT * FROM Recipe WHERE (id_player = %d)" %(player['id_player']))

		sales_quantity =db.select("SELECT quantity_sales FROM Sales\
			WHERE (day_sales = %d AND id_player = %d)" %(current_day, player['id_player']))

		#Calcul de la totalité des ventes (en quantité)
		all_sales = 0
		for asold in sales_quantity:
			all_sales = all_sales + asold['quantity_sales']

		#Mise en forme de la valeur pour la clé drinkOffered
		drinkOffredValue = []
		for arecipe in recipe_datas:
			drinkOffredValue.append({
				"name": arecipe['name_recipe'],
				"buying_price":arecipe['price_buying_recipe'],
				"cost_price":arecipe['cost_prod_recipe'],
				"isCold": arecipe['iscold_recipe'],
				"hasAlcohol":arecipe['hasalcohol_recipe']
				})

		#Mise en forme de la réponse pour la clé playerInfos
		playerInfosValue[player['name_player']] = {
			"cash": player['cash_player'],
			"sales":all_sales,
			"profit": get_profit(players, player['name_player']),
			"drinksOffered": drinkOffredValue
		}

	#Mise en forme de la réponse pour la clé drinksByPlayer
	drinksByPlayerValue = {}
	for player in players:
		#On récupère les données de la table Recipe
		recipe_datas = db.select("SELECT * FROM Recipe WHERE (id_player = %d)" %(player['id_player']))
		
		drinks = []
		for arecipe in recipe_datas:
			drinks.append({
				"name": arecipe['name_recipe'],
				"buying_price":arecipe['price_buying_recipe'],
				"cost_price":arecipe['cost_prod_recipe'],
				"isCold": arecipe['iscold_recipe'],
				"hasAlcohol":arecipe['hasalcohol_recipe']
				})


		#On remplir drinkByPlayerValue
		drinksByPlayerValue[player['name_player']] = drinks;

	db.close()


	#Mise en forme de la réponse pour la clé "map"
	theMap = {
		"region": region,
		"itemsByPlayer": itemsByPlayer,
		"playerInfo": playerInfosValue,
		"drinksByPlayer": drinksByPlayerValue
	}

	#Mise en forme de la réponse finaleRéponse finale
	resp = {
		"map": theMap
	}

	return to_make_response(resp)

@app.route('/map/<playerName>', methods = ['GET']) #Manque le ranking
def get_map_player(playerName):
	'''
	Cette route permet aux joeuur de visualiser le jeu
	'''
	#Récupération des données du joueur
	db = Db()
	player_datas = db.select("SELECT * FROM Player WHERE name_player = %(username)s", {
		"username":playerName
		})
	#Récupération du jour de jeu courant
	current_day = get_lastGameDay()

	#Récupération des éléments de la map
	map_datas = db.select("SELECT * FROM Map")

	#Récupération des itemps du players
		#Récupération de ses panneaux publicitaire
	addspaces = db.select("SELECT * FROM Addspace WHERE (id_player = %d AND day_addspace = %d)"\
			%(player_datas[0]['id_player'], current_day))

	#Mise en place de la réponse pour la clé map
		#Mise en place de la réponse pour la clé itemsByPlayer via le renseignement des items
		#de add et les items de stands (confondus avec le joueur)
	itemsbyPlayer = {}
	itemsplayer = []
	for add in addspaces:
		itemsplayer.append({
			"kind":"add",
			"owner":playerName,
			"location": {
				"latitude": add['lat_addspace'],
				"longitude": add['lon_addspace']
			},
			"influence": add['influence_addspace']
		})

	#Remplissage pour les items stand
	itemsplayer.append({
		"kind":"stand",
		"owner": playerName,
		"location": {
			"latitude":player_datas[0]['lat_player'],
			"longitude":player_datas[0]['lon_player']
		},
		"influence":player_datas[0]['rayon_player']
	})
	itemsbyPlayer[playerName] = itemsplayer

		#Mise en place de la réponse pour la clé map
	theMap = {
		"region": {
			"center": {
				"latitude": map_datas[0]['lat_map'],
				"longitude":map_datas[0]['lon_map']
			},
			"span": {
				"latitudeSpan": map_datas[0]['lat_span_map'],
				"longitudeSpan": map_datas[0]['lon_span_map']
			}
		},
		"itemsByPlayer":itemsbyPlayer
	}

	#Mise en forme de la réponse pour la clé playerInfos
		#Récupération de l'ensemble des joueurs de la partie
	players = db.select("SELECT * FROM Player WHERE ingame_player = %d" %(id_game_default))
		#Mise en forme de la réponse pour la clé drinksOffered
			#Récupération des données de la table Recipe
	recipe_datas = db.select("SELECT * FROM Recipe WHERE (id_player = %d)" %(player_datas[0]['id_player']))
			#Récupération des ventes
	sales_quantity =db.select("SELECT quantity_sales FROM Sales\
			WHERE (day_sales = %d AND id_player = %d)" %(current_day, player_datas[0]['id_player']))

	#Calcul de la totalité des ventes (en quantité)
	all_sales = 0
	for asold in sales_quantity:
		all_sales = all_sales + asold['quantity_sales']

		#Mise en forme de la valeur pour la clé drinkOffered
	drinkOffredValue = []
	for arecipe in recipe_datas:
		drinkOffredValue.append({
			"name": arecipe['name_recipe'],
			"buying_price":arecipe['price_buying_recipe'],
			"cost_price":arecipe['cost_prod_recipe'],
			"isCold": arecipe['iscold_recipe'],
			"hasAlcohol":arecipe['hasalcohol_recipe']
		})

	#Mise en forme de la réponse pour la clé playerInfos
	playerInfosValue = {}
	playerInfosValue[playerName] = {
		"cash": player_datas[0]['cash_player'],
		"sales": all_sales,
		"profit": get_profit(players, playerName),
		"drinkOffered": drinkOffredValue
	}

	availableIngredients = get_available_ingredients(player_datas[0]['cash_player'])
	resp = {
		"availableIngredients":availableIngredients,
		"map": theMap,
		"playerInfo": playerInfosValue
	}
	db.close()
	return to_make_response(resp)

@app.route('/login', methods = ['GET'])
def login():
	'''
	Cette route permet à un joueur de se connecter 
	à son espace gamer
	'''
	param_url = 'toto'#request.args.get('pseudo')

	db = Db()
	#On vérifie que le joueur existe en base
	pseudo = db.select("SELECT name_player FROM Player")
	db.close()
	print(pseudo)
	
	if (len(pseudo) == 0):
		return to_make_response('Internal Server Error', 510)

	indatabase = False 
	for i in xrange(0, len(pseudo)):
		if (pseudo[i]['name_player'] == param_url):
			indatabase = True

	print(indatabase)

	#Si le joueur n'existe pas en base de données
	#Retour d'une erreur 404. Il faut qu'il s'identifie ou qu'il crée un compte.
	if (indatabase == False):
		return to_make_response('Not found', 404)

	#Si le joueur existe en base de données
	db = Db()
	player_infos = db.select("SELECT * FROM Player WHERE name_player = %(user_pseudo)s", {
		"user_pseudo": param_url
		})

	db.execute("UPDATE Player SET isConnected_player = %(connected)s",{
		"connected": True
		}) 
	db.close()

	return to_make_response(player_infos)

@app.route('/metrology', methods=['GET'])
def metro_get_infos(): #A voir si l'heure affiché est heure ou bien heure:min:ss
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
		return to_make_response('Internal Server Error', 511)

		#Récupération de la dernière ligne de la table Weather
	w_last_infos = db.select("SELECT now_weather, tomorrow_weather FROM Weather \
		WHERE id_weather = %d" %(w_id_max[0]['max']))

		#Erreur récupération dernière ligne de la table Weather
	if (len(w_last_infos) == 0):
		return to_make_response('Internal Server Error', 512)
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

	if (len(number_ingredients) != 1):
		return to_make_response('Internal Server Error', 584)

	#S'il n'y a aucun élément dans la base
	if (number_ingredients[0]['count'] == 0):
		return to_make_response('Aucun ingrédient enregistré')

	#S'il y a un ou plusieurs éléments dans la base, on récupère la liste des ingrédients
	ingredients = db.select("SELECT name_ingredient as name, price_ingredient as cost FROM Ingredient")
	
	db.close()
	return to_make_response(ingredients)

#curl -X POST -H "Content-Type: application/json" -d '{"timestamp": 5, "weather": [{"dfn":0, "weather":"sunny"},{"dfn":1,"weather":"cloudy"}]}' http://127.0.0.1:5000/metrology
#ROUTE AVEC FONCTION SANS LE BASCULEMENT DES JOURS.
@app.route('/metrology', methods = ['POST'])
def metro_save_infos():
	'''
	Cette route permet de sauvegarder les données temporelles et 
	météo envoyée par l'ardwino
	'''
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
		return to_make_response('Internal Server Error', 537)

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
			return to_make_response('Internal Server Error', 553)

	#S'il y a des éléments en base de données
		#On ne crée plus d'instance tant que un jour complet n'est pas passé.
	#Récupération du dernier jour mise en base
	last_day = get_lastGameDay()

	if ((current_day != last_day)):#On est donc passé au jour numéro 2
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
			return to_make_response('Internal Server Error', 576)

		return to_make_response('', 201)

	return to_make_response(' ', 200)

#curl -X POST -H "Content-Type: application/json" -d '{"pseudo": "babar"}' http://127.0.0.1:5000/account/create
@app.route('/account/create', methods = ['POST'])
def create_account():
	'''
	Cette route permet de créer une compte utilisateur
	pour pouvoir jouer en ligne. 
	Une fois que le joueur est créée, il n'est pas connecté.
	'''
	#Récupération de la données
	datas = request.get_json()

	#Vérification de la données pour voir si elle est conforme à ce qu'attend le serveur
	if (isValide(datas) == False):
		return to_make_response('Bad Request', 400)

	if not ('pseudo' in datas):
		return to_make_response('Bad Request', 400)

	if ((datas['pseudo'] == '') or (datas['pseudo'].isspace()==True)):
		return to_make_resp('Bad request', 400)

	#La données est conforme, donc on la traite
	#Vérification que le pseudo ne se trouve pas déjà dans la base de données
		#Compte combien d'éléments joueur on a en base
	db = Db()
	number_account = db.select("SELECT COUNT(*) FROM Player")

	if (len(number_account) != 1):
		return to_make_response('Internal Server Error')

	if (number_account[0]['count'] == 0):
		#Dans ce cas, on est sur que le joueur ne se trouve pas en base.
		#Donc on le crée.
		new_player_id = db.select("INSERT INTO Player (name_player, isConnected_player) \
							   VALUES (%(name)s, %(connected)s) RETURNING id_player", {
							   "name": datas['pseudo'], 
							   "connected": False
							   })

		#Si la création ne s'est pas correctement passé
		#if len(new_player_id) != 1:
		#	return to_make_response('Internal Server Error', 500)

		return to_make_response(new_player_id, 201)

	#Il y a au moins un joueur en base de données
	#On fait une requête pour voir si le joueur n'est pas en base
	pseudo = db.select("SELECT name_player FROM Player WHERE (name_player = %(name)s)",{
		"name":datas['pseudo']
		})
		
	#Le pseudo est présent dans la base de données. On indique au client qu'il doit en choisir un autre
	if (len(pseudo) == 1):
		return to_make_response('Pseudo not available. Choose another Pseudo', 401)

	#Le pseudo n'est pas dans la base de données. Donc on le crée
	new_player_id = db.select("INSERT INTO player (name_player, isconnected_player) VALUES (%(name)s, %(connected)s) RETURNING id_player", {
							   "name": datas['pseudo'], 
							   "connected": False
							   })

	#if (len(new_player_id) != 1):
	#	return to_make_response('Internal Server Error', 501)
	db.close()

	return to_make_response(new_player_id, 201)

'''to test'''
@app.route('/players', methods=['POST'])
def join_game():
	'''
	Cette route permet à un joueur connecté de rejoindre
	une parie.
	'''
	#Récupération de la donnée
	datas = request.get_json()
	#print datas

	#Test de la donnée pour voir si on peut la traiter ou non
	if (isValide(datas) == False):
		return to_make_response('Bad Request', 400)

	if not ('name' in datas):
		return to_make_response('Bad Request', 401)

	if ((datas['name'] == '') or (datas['name'].isspace()==True)):
		return to_make_resp('Bad request', 402)

	#La données est conforme pour être traitée. Donc on la traite.
	#Récupération des informations du joueur
	db = Db()
	player = db.select("SELECT * FROM player WHERE name_player = %(pseudo)s", {
		"pseudo":datas['name']
		})

	#Si la récupération de la donnée s'est mal passé
	if (len(player) != 1):
		return to_make_response('Internal Server Error', 560)

	#Si la récupération de donnée s'est correctement passée
	#On vérifie si que le joueur soit dans la partie pour la première fois où bien s'il y est déjà.
	player_ingame = player[0]['ingame_player']

		#Cas où le joueur est déjà connecté à la game
	if (player_ingame == id_game_default):
		#Récupération de l'ensemble des joueurs de la game
		all_players = db.select("SELECT * FROM Player WHERE ingame_player = %d"\
			%(id_game_default))

		if (len(all_players) == 0):
			return to_make_response('Internal Server Error',501)

		#Récupération des ventes effectuées par le joueur au jour en cours
			#Récupération du jour courant
		current_day = get_lastGameDay()

			#Récupération de l'ensemble des ventes du joueur pour le jour courant
		all_sales_player = db.select("SELECT quantity_sales FROM Sales WHERE (day_sales = %d AND \
			id_player=%d)" %(current_day, player[0]['id_player']))

		if (len(all_sales_player) == 0):
			return to_make_response('Internal Server Error', 502)

		#Calcul du total des ventes
		all_sales = 0
		for asold in all_sales_player:
			all_sales = all_sales + asold['quantity_sales']

		#Mise en place de la réponse du drinksOffered (supposition que tout ce que possède le joueur
		#est porposé à la vente.
			#Récupération de l'ensemble des recettes vendues au jour en cours par le joueur
		#all_recipe_sold = db.select("SELECT name_recipe, price_buying_recipe, cost_prod_recipe, \
		#	isCold_recipe, hasAlcohol_recipe FROM Sales FULL JOIN Recipe ON sales.id_recipe = recipe.id_recipe\
		#	WHERE (id_player = %d AND day_sales = %d)" %(player[0]['id_player'], current_day))
		#print(all_recipe_sold)*/

		all_recipe = db.select("SELECT * FROM Recipe WHERE id_player = %d" %(player[0]['id_player']))
		if (len(all_recipe) == 0):
			return to_make_response('Internal Server Error', 503)

			#Mise en forme de la réponse pour la clé drinksOffered
		drinksOffered = []
		for adrink in all_recipe:
			drinksOffered.append({
				"name":adrink['name_recipe'],
				"buying_price":adrink['price_buying_recipe'],
				"cost_production":adrink['cost_prod_recipe'],
				"hasAlcohol":adrink['hasalcohol_recipe'],
				"isCold":adrink['iscold_recipe']
				})

		#Mise en forme de la réponse
		resp = {
			"name": player[0]['name'],
			"location": {
				"latitude": player[0]['lat_player'],
				"longitude":player[0]['lon_player']
			},
			"info":{
				"cash": player[0]['cash_player'],
				"sales":all_sales,
				"profit": get_profit(all_players, player[0]['name_player']),
				"drinksOffered": drinksOffered
			}
		}

		#On renvoie donc les données correspondantes
		return to_make_response(resp)

	#Cas où le joueur n'est pas déjà connecté à la game.
		#On génère les coordonnées du joueur
	coordonate_player = generate_location(-100.0, 100.1)

		#On met à jour les champs du joueur
	db.execute("UPDATE Player SET lon_player = %f, lat_player = %f, cash_player = %f, \
		rayon_player = %f, ingame_player = %d" %(coordonate_player['longitude'], coordonate_player['latitude'], \
			default_cash_game, default_rayon_player, id_game_default))


		#On crée une instance de la recette (ou bien on récupère l'instance par défaut a voir)
	recipe_creation =db.select("INSERT INTO Recipe(name_recipe, price_buying_recipe, cost_prod_recipe\
		isCold_recipe, hasAlcohol_recipe, isUnblocked_recipe, id_player VALUES (%(name)s, %(buying_price)s\
			%(cost_production)s, %(iscold)s, %(hasalcohol)s, %(unblocked)s, %(id)s RETURNING id_recipe", {
			"name": "Limonade Citron",
			"iscold":True,
			"hasalcohol":False,
			"unblocked":True,
			"id":player[0]['id_player']
			})

	if (len(recipe_creation) != 1):
		return to_make_response('Internal Server Error', 504)

		#On crée une instance de débloquer
			#On recupere le jour courant
	current_day = get_lastGameDay()
	unblock_creation = db.select("INSERT INTO Unblock(day_unblock, quantity_unblock, id_player, id_recipe)\
		VALUES (%(day)s, %(quantity)s, %(id_player)s, %(recipe_id)s)", {
		"day": current_day,
		"quantity": 1,
		"id_player":player[0]['id_player'],
		"recipe_id":recipe_creation[0]['id_recipe']
		})

		#On récupère les ingrédients nécéssaires à la recette: citron
	ingredients = db.select("SELECT * FROM Ingredient WHERE (name_ingredient = %(name)s", {
	"name": "Citron"
	})

	if (len(ingredients) != 1):
		return to_make_response('Internal Server Error', 505)

		#Création d'une instance compose, liant les ingrédients et la recette
	creation_compose = db.select("INSERT INTO Compose(id_ingredient, id_recipe) VALUES \
		(%(ingredient_id)s, %(recipe_id)s)", {
		"ingredient_id": ingredients[0]['id_ingredient'],
		"recipe_id": recipe_creation[0]['id_recipe']
		})

	if (len(creation_compose) != 1):
		return to_make_response('Internal Server Error', 506)

		#Mise à jour des données de la recette nouvellement créée (concernant le prix)
	db.execute("UPDATE Recipe SET price_buying_recipe = %f, cost_prod_recipe = %f" \
		%((float(ingredients[0]['price_ingredient'])* 2.0), (float(ingredients[0]['price_ingredient']))))

		#Récupération de l'ensemble des boissons du joueurs
	all_recipe = db.select("SELECT * FROM Recipe WHERE id_player = %d" %(player[0]['id_player']))

	db.close()

		#Mise en place de la réponse pour la clé drinksOffered
	drinksOffered = []
	for adrink in all_recipe:
		drinks.append({
			"name":adrink['name_recipe'],
			"buying_price":adrink['price_buying_recipe'],
			"cost_production":adrink['cost_prod_recipe'],
			"hasAlcohol":adrink['hasalcohol_recipe'],
			"isCold":adrink['iscold_recipe']
			})

		#Mise en place de la réponse
	resp = {
		"name":player[0]['name_player'],
		"location":{
			"latitude": player[0]['lat_player'],
			"longitude":player[0]['lon_player']
		},
		"infos":{
			"cash":player[0]['cash'],
			"sales":0,
			"profit":0.0,
			"drinksOffered": drinksOfferedS
		}
	}
	return to_make_response(resp)

	'''
	algo:
	le joueur se connecte a une partie.
	Ok.
	Si le joueur est deja dans la partie alors on lance certaines données.
	Si c'est la premiere fois que le joueur se connecte à la partie alors on renvoie d'autres données.
	'''


''' to test '''
#Il manque juste à gérer l'action "Débloquer Recette" (newRecipe) pour avoir le jeu complet.
#curl -X POST -H "Content-Type: application/json" -d '{["action": {"kind": "drinks", "prepare":{"Limonade":2}, "price":{"Limonade":15}}]}' http://127.0.0.1:5000/action/toto
#Pour le moment la simulation n'est pas géré (simulated)
@app.route('/actions/<playerName>', methods = ['POST'])
def save_actions(playerName):
	'''
	Cette route permet d'enregistrer le souhait de l'utilisateur
	dans la base de données.
	'''
	#Réception de la donnée du client
	datas = request.get_json()

	#Vérification de la validité de la donnée
	if (isValide(datas) == False):
		return to_make_response('Bad Request', 400)

	if not ('actions' in datas):
		return to_make_response('Bad Request', 400)

	#On calcul le cout global des actions.
	#Si le cout global est < cash_player alors on enregistre, sinon on enregistre pas dans la BDD
		#Détermination du cout total des actions
	costs = 0.0
	for anAntion in datas['actions']:
		if (anAction['kind'] == 'drinks'): #Action de production
			costs = costs + calculate_cost_prod(anAction, playerName)
		if (anAction['kind'] == 'ad'):
			cost += cost + calculate_cost_ad(anAction, playerName)

		#On récupère les données du joueurs
	player = db.select("SELECT * FROM Player WHERE name_player = %(name)s", {
		"name":playerName
		})

	#Si le joueur n'a pas assez d'argent
	if (float(player[0]['cash_player']) < costs):
		resp = {
			"sufficientFunds":False,
			"totalCost":costs
		}
		return to_make_response(resp)

	#Le joueur a assez d'argent. Alors...
		#...On remplie la base de données
	for anAction in datas['actions']:
		if (anAction['kind'] == 'drinks'):
			filldb_playeractionsdrinks(anAction, playerName)
		if (anAction['kind'] == 'ad'):
			filldb_playeractionsAdd(anAction, playerName)

		#...On met à jour le cash disponible du joueur
			#Récupération du cash du joueur
	cash = float(player[0]['cash_player'])
			#Calcul du cash qu'il aura lorsque toutes les actions sont comptablisé
			#Aucune prise en compte des profits. En effet, les actions sur une journée n'ont pas été lancés.
	playerCashAfterActions = cash - costs #Tj positif sinon il y a une erreur

	print(playerCashAfterActions)

	db.execute("UPDATE Player SET cash_player = %(newcash)d ", {
		"newcash": playerCashAfterActions
		})

	#Mise en forme de la réponse
	resp = {
		"sufficientFunds": True,
		"totalCost": costs
	}

	return to_make_response(resp)


''' to test '''
@app.route('/sales', methods =  ['POST'])
def collect_sales():
	'''
	Cette route permet de sauvegarder le nombre de ventes
	de chaque boissons pour un joeuur donné
	'''
	datas = request.get_json()

	if (isValide(datas) == False):
		return to_make_response('Bad Request', 400)

	if not ('sales' in datas):
		return to_make_response('Bad Request')

	#Récupération du jour courant de jeu
	currentDay = get_lastGameDay()

	#La donnée est conforme a ce que nous attendions, on la traite. (concerne la table Sales)
	#Le but est de créer une instance de Sales par boisson et par jour pour un joueur donné
	db = Db()

	for dictObject in datas['sales']:
		#Récupération de l'id du joueur
		playerID = db.select("SELECT id_player FROM Player WHERE (id_player = %(id)s)", {
			"id":dictObject['player']
		})

		if (len(playerID) != 1):
			return to_make_response('Internal Server Error', 550)

		#Récupération de l'id de la recette vendue
		recipeID = db.select("SELECT id_recipe FROM Recipe WHERE (name_recipe = %(name)s)", {
			"name":dictObject['item']
			})

		if (len(recipeID) != 1):
			return to_make_response('Internal Server Error', 558)

		#Requete A TESTER À PART EN PRIORITÉ
		#Vérification que l'instance de la table Sales que l'on va créer n'est pas déjà présente en base
		presentInDB = db.select("SELECT COUNT(*) FROM Sales WHERE (day_sales = %(day)s,\
			id_player = %(p_id)s, id_recipe = %(r_id)s)", {
		"day_sales": currentDay,
		"p_id": playerID,
		"r_id": recipeID
		})

		if (presentInDB != 1):
			return to_make_response('Internal Server Error', 570)


		#Cas où il n'y a aucune ligne vente pour ce jour, cet id_recipe et cet id_joueur
		if (presentInDB[0]['count'] == 0):
			#Alors on crée une nouvelle instance de Sales, qui sera représentée en base par une ligne
			sold_creation = db.select("INSERT INTO sales (quantity_sales, day_sales, id_player, id_recipe)\
				VALUES (%(quantity)s, %(day)s, %(p_id)s, %(r_id)s)", {
				"quantity":dictObject['quantity'],
				"day": currentDay,
				"p_id":playerID,
				"r_id":recipeID
				})

		#Cas où il y a déjà une ligne, on la récupère et on effectue dessus une mise à jour
			#Récupération de la ligne
		soldToModify = db.select("SELECT * FROM Sales WHERE (day_sales = %(day)s, id_player = %(p_id)s\
			id_recipe = %(r_id)s)", {
		"day":currentDay,e
		"p_id":playerID,
		"r_id":recipeID
		})

		if (len(soldToModify) != 1):
			return to_make_response('Internal Server Error', 594)

			#Update de la ligne en question
		db.execute("UPDATE Sales SET (quantity_sales = %(quantity)s, day_sales =%(day)s, \
			id_player = %(p_id)s, id_recipe = %(r_id)s)",{
			"quantity": dictObject['quantity'],
			"day": currentDay,
			"p_id": playerID,
			"r_id": recipeID
			})
	db.close()
	return to_make_response('', 201)



if __name__ == '__main__':
	app.run()


'''
#playerActionNewRecipe pour géré l'achat d'une nouvelle recette
#playerActionAd pour gérer tout ce qui est relatif a la publicité
#playerActionDrinks pour tout ce qui est relif à la création de boissons
'''

'''
Reste a faire:
	Le ranking qu'il faut mettre dans le module mserver.py
	Le get /reset qui permet de remettre l'ensemble des joueur au même niveau d'argent
	En post:
		/actions/playername
		/sales
'''
