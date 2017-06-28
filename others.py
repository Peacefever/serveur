#-*- encoding:utf-8 -*-
import json
from flask import make_response
import random
from db import Db

default_cash = 20.0
default_rayon = 10.0
default_recipe_id = 1


def to_make_response(data, status=200):
	'''
	Formattage de la réponse du serveur
	'''
	resp = make_response(json.dumps(data), status)
	resp.mimetype = 'application/json'
	return resp

def internal_server_error():
	return to_make_response('Internal Server Error', 500)

def get_current_day():
	'''
	Obtention du jour de jeu courant
	'''
	db = Db()
	#On regarde s'il y a quelque chose dans la table
	count = db.select("SELECT COUNT(*) FROM Weather")

	if (count[0]['count'] == 0):
		return -1

	weather_max_id = db.select("SELECT MAX(id_weather) FROM Weather")

	print(weather_max_id)
	if (weather_max_id == None or len(weather_max_id) == 0):
		return -1

	current_day = db.select("SELECT day_weather FROM Weather \
	                         WHERE id_weather = %d" %weather_max_id[0]['max'])

	if (current_day == None or len(current_day) == 0):
		return -1

	db.close()
	return current_day[0]['day_weather']

def get_players_ingame(gameid):
	'''
	Obtention d'une liste de l'ensemble des joueurs d'une partie
	'''
	db = Db()
	players = db.select("SELECT * FROM Player WHERE (ingame_player = %d)" %(gameid))
	db.close()
	return players

def get_numberTot_sold(playerID):
	'''
	Obtention du nombre total de vente pour un joueur dans la journée
	'''
	#Récupération de l'ensemble des éléments vendus dans une journée
	db = Db()

	day = get_current_day()

	if (day == -1):
		return 0

	sales = db.select("SELECT * FROM Sales WHERE (id_player = %d AND day_sales = %d)" %(playerID, day))
	db.close()

	if (len(sales) == 0):
		return 0

	#Calcul des ventes totales effectuées
	soldtot = 0
	for asold in sales:
		soldtot = soldtot + int(asold['quantity_sales'])
	#soldtot = round(soldtot, 3)
	return soldtot

def get_costTot_ads(playerID, day):
	'''
	Obtention du total des charges pour la pub (en euros)
	'''
	db = Db()
	datas_add = db.select("SELECT price_adspace, number_adspace FROM Adspace WHERE (id_player = %d\
			AND day_adspace = %d)" %(playerID, day))

	if (len(datas_add) == 0):
		return 0.0

	costs = 0.0
	for add in datas_add:
		costs = costs + (float(add['number_adspace']) * float(add['price_adspace']))
	db.close()
	return costs

def get_costTot_prod(playerID, day):
	'''
	Obtention du cout total de la production (en euros)
	'''
	db = Db()
	prod_recipe_datas = db.select("SELECT quantity_production,\
			cost_prod_recipe FROM Production FULL JOIN Recipe ON recipe.id_recipe=\
			production.id_recipe WHERE (production.id_player = %d AND production.day_production = %d)"\
			%(playerID, day))

	#Scénario impossible dans notre cas car il y a toujours une recette dans la partie
	if (len(prod_recipe_datas) == 0):
		return 0.0

	db.close()

	costs = 0.0
	for aprod in prod_recipe_datas:
		costs = costs + (float(aprod['quantity_production']) * float(aprod['cost_prod_recipe']))

	return costs

def get_costTot_buyingRecipe(playerID, day):
	'''
	Cette fonction permet de calculer le cout total
	de l'achat des recettes en euros. (prixAchatRecette * nombreDeRecetteAchetées)
	'''
	db = Db()
	recipe_unblock_datas = db.select("SELECT quantity_unblock, name_recipe, price_buying_recipe FROM Unblock \
		FULL JOIN Recipe ON recipe.id_recipe = unblock.id_recipe WHERE (day_unblock =%d\
		AND unblock.id_player = %d AND Recipe.isUnblocked_recipe = %s)" %(day,playerID,\
		True))

	#Scénario impossible dans notre cas car une recette est automatiquement débloquée pour le joueur
	#au début d'une partie
	if (len(recipe_unblock_datas) == 0):
		return 0.0

	costs = 0.0
	for arecipe in recipe_unblock_datas:
		costs = costs + (float(arecipe['quantity_unblock']) * float(arecipe['price_buying_recipe']))
	db.close()
	return costs

def get_totalCosts(playerID, day):
	'''
	Obtention des charges totales d'un joueur à un jour de jeu
	'''
	adsCosts = float(get_costTot_ads(playerID, day))
	#print(type(adsCosts))
	prodCosts = float(get_costTot_prod(playerID, day))
	buyingCosts = float(get_costTot_buyingRecipe(playerID, day))
	#print(type(buyingCosts))
	totalCosts = adsCosts+buyingCosts+prodCosts
	#print(type(totalCosts))
	return totalCosts

def get_incomes_sold(playerID, day):
	'''
	Obtention de la totalité des ventes en euros
	'''
	db = Db()
	recipe_prod = db.select("SELECT price_sale_production, id_recipe FROM Production WHERE \
		(id_player = %d AND day_production = %d)" %(playerID, day))

	if (len(recipe_prod) == 0):
		return 0.0

	incomes = 0.0
	for arecipe in recipe_prod:
		theId = arecipe['id_recipe']
		thecost = arecipe['price_sale_production']

		solds = db.select("SELECT quantity_sales FROM Sales WHERE (id_player = %d AND day_sales = %d  AND \
			id_recipe = %d)" %(playerID, day, theId))

		incomes = incomes + (float(solds[0]['quantity_sales']) * float(thecost))

	db.close()
	return incomes

def get_profits(playerID, previousdays = 0):
	'''
	Cette fonction permet de calculer le profit d'un joueur
	à un certain jour. (total ventes (en euros) - totaldescharges(en euros))
	'''
	#Récupération du jour actuel - previousday
	day = get_current_day() - previousdays
	#calcul du profit
	costsTot = get_totalCosts(playerID, day)
	incomesTot = get_incomes_sold(playerID, day)
	profit = incomesTot - costsTot
	return profit

def get_player_fromName(nameplayer, gameid):
	db = Db()
	player = db.select("SELECT * FROM Player WHERE (name_player = %(name)s AND ingame_player = %(id)s)", {
		"name":nameplayer,
		"id":gameid
		})

	db.close()
	return player

def get_available_ingredients(player_cash):
	db = Db()
	ingredient_available = db.select("SELECT name_ingredient, price_ingredient FROM Ingredient")
	db.close()

	availableIngredients = []
	for ingredient in ingredient_available:
		if (float(ingredient['price_ingredient']) <= float(player_cash)):
			availableIngredients.append({
				"name":ingredient['name_ingredient'],
				"price":ingredient['price_ingredient']
			})
	db.close()
	return availableIngredients

def isValidData(data):
	'''
	Vérification de la validité du format de la donnée
	'''
	if (data == None):
		return False
	if not (isinstance(data, dict)):
		return False
	return True

def bad_request():
	return to_make_response('Bad Request', 400)

def is_present_pseudo_indb(playername):
	'''
	Vérifie si le joueur est présent en base de données
	'''
	db = Db()
	#Vérification que le joueur est présent en base
	player_db = db.select("SELECT * FROM Player WHERE name_player = %(name)s", {
		"name":playername
		})
	print('JE suis dans le player pseduo db')
	print(player_db)

	db.close()

	#Joueur pas en base de donnée
	if (len(player_db) == 0):
		return False

	return True

def generate_location(minimum = -100, maximum = 100):
	location = {}
	#Génération aléatoire puis arrondis
	i = 0
	while (i < 2):
		number = random.uniform(minimum, maximum)
		if (i == 0):
			location['latitude'] = round(number, 5)
		if (i == 1):
			location['longitude'] = round(number, 5)
		i = i + 1
	return location






################## ESSAIE ######################
'''
def join_new_player(playername, gameid):

	print('je passe dans le join player car je ne suis pas en cas')
	db = Db()
	
	#Génération des coordonnées du joueur de la map
	location = generate_location()

	#On crée un joueur
	player_creation = db.select("INSERT INTO Player (name_player, isConnected_player, ingame_player,\
		action_buyadds, action_buynewrecipe, action_prodrecipe, lon_player, lat_player, cash_player, rayon_player )\
							   VALUES (%(name)s, %(connected)s, %(game)s, %(ads)s, %(buy)s, %(prod)s, %(lon)s, %(lat)s, %(cash)s, %(rayon)s) RETURNING id_player", {
							   "name": playername, 
							   "connected": True,
							   "game":gameid,
							   "ads":False,
							   "buy":False,
							   "prod":False,
							   "lon":location['longitude'],
							   "lat":location['latitude'],
							   "cash":default_cash,
							   "rayon":default_rayon
							   })

	print("creation id")
	print(player_creation)
	print("fin creation id")
	if (len(player_creation) == 0 or player_creation == None):
		print("je passe dans erreur")
		return -1

	#Récupère les données du joueurs
	player = db.select("SELECT * FROM Player WHERE id_player = %d" %(player_creation[0]['id_player']))

	print("the player")
	print(player)
	print("Fin player")
	if (len(player) != 1 or player == None):
		return -1

	#Le joueur débloque de la limonade tout de suite
	#Cette recette est une limonade au citron et à l'eau
		#Récupération de la recette par défault
	print("debut recipe")
	recipe_default = db.select("SELECT * FROM Recipe WHERE name_recipe = %(name)s AND id_recipe = %(id)s",{
		"name":"Limonade",
		"id":default_recipe_id
		})
	print(recipe_default)
	print("fin")

	if (len(recipe_default) == 0 or recipe_default == None):
		return -1

	#Récupération du jour actuel de jeu
	day = get_current_day()

	if (day == -1):
		return -1

	#Création d'une instance Unblock
	db.execute("INSERT INTO Unblock (day_unblock, quantity_unblock, id_player, id_recipe)\
		VALUES (%(day)s, %(quantity)s, %(id_p)s, %(id_r)s)", {
		"day": day,
		"quantity": 1,
		"id_r":default_recipe_id,
		"id_p": player[0]['id_player']
		})

	#Mise à jour de champs de la recette
	db.execute("UPDATE Recipe SET isUnblocked_recipe = %(unblocked)s, id_player = %(id)s\
		WHERE id_recipe = %(id_r)s", {
				"unblocked": True,
				"id":player[0]['id_player'],
				"id_r":default_recipe_id
				})

	print("voila")
	print(db.select("SELECT * FROM Player WHERE id_player = %d" %(player[0]['id_player'])))
	print("hello")


	#Récupération des ingrédients eaux de source et citron.
		#Citron
	citron_ingredient = db.select("SELECT * FROM Ingredient WHERE name_ingredient = %(name)s",{
		"name":'Citron'
		})

	if (len(citron_ingredient) == 0 or citron_ingredient == None):
		return -1

	eau_de_source_ingredient = db.select("SELECT * FROM Ingredient WHERE name_ingredient = %(name)s", {
		"name":'Eau de source'
		})

	if (len(eau_de_source_ingredient) == 0 or eau_de_source_ingredient == None):
		return -1

	#Création deux instances de Compose
	for n in xrange(0, 2):
		if (n == 0):
			db.execute("INSERT INTO Compose(id_ingredient, id_recipe) VALUES \
				(%(ingr_id)s, %(r_id)s)", {
				"ingr_id": eau_de_source_ingredient[0]['id_ingredient'],
				"r_id": default_recipe_id
				})
		if (n == 1):
			db.execute("INSERT INTO Compose(id_ingredient, id_recipe) VALUES \
				(%(ingr_id)s, %(r_id)s)", {
				"ingr_id": citron_ingredient[0]['id_ingredient'],
				"r_id": default_recipe_id
				})

		print(db.select("SELECT * FROM Compose"))

	db.close()

	resp = {
		"name":recipe_default[0]['name_recipe'],
		"location":{
			"latitude": player[0]['lat_player'],
			"longitude":player[0]['lon_player']
		},
		"infos": get_player_infos(player[0]['id_player'], default_game, "prod")
	}
	return resp
'''

################################################
'''
def define_day(timestamp):

	#Cette fonction permet de calculer le jour actuel
	#de jeu à partir d'un timestamp en seconde.
	#
	oneDayTS = 3600.0 * 24.0
	timestamp = float(timestamp)
	
	#On réalise le calcul en ajoutant +1 car le jeu debute au jour 1
	the_days = ((timestamp / oneDayTS))# + 1)
	
	#Récupération de la partie entière, correspondant au jour de jeu
	the_days = int(the_days)

	return the_days

def define_hours(timestamp):
	
	#Cette fonction permet de définir à partir d'un timestamp
	#en seconde le nombre d'heures.
	
	onehour = 3600.0
	number_hours = float(timestamp) / onehour
	number_hours = int(number_hours)
	return number_hours

'''