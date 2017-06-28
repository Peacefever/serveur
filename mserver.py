#-*- encoding:utf-8 -*-
import json
from flask import make_response
import random
from db import Db
############
default_price_pub = 2.0
default_rayon_pub = 10.0
############


def isValide(data):
	'''
	Cette fonction permet de voir si la données
	est au bon format pour être traitée.
	'''
	if (data == None):
		return False
	if not (isinstance(data, dict)):
		return False
	return True

def to_make_response(data, status=200):
	'''
	Cette fonction permet de formatter en JSON une
	réponse à une requête.
	'''
	resp = make_response(json.dumps(data), status)
	resp.mimetype = 'application/json'
	return resp

def define_day(timestamp):
	'''
	Cette fonction permet de calculer le jour actuel
	de jeu à partir d'un timestamp en seconde.
	'''
	oneDayTS = 3600.0 * 24.0
	timestamp = float(timestamp)
	
	#On réalise le calcul en ajoutant +1 car le jeu debute au jour 1
	the_days = ((timestamp / oneDayTS) + 1)
	
	#Récupération de la partie entière, correspondant au jour de jeu
	the_days = int(the_days)

	return the_days

def define_hours(timestamp):
	'''
	Cette fonction permet de définir à partir d'un timestamp
	en seconde le nombre d'heures.
	'''
	onehour = 3600.0
	number_hours = float(timestamp) / onehour
	number_hours = int(number_hours)
	return number_hours

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

def get_lastGameDay():
	db = Db()
	w_id_max = db.select("SELECT MAX(id_weather) FROM Weather")
	nb_days_players = db.select("SELECT day_weather FROM Weather \
	                             WHERE id_weather = %d" %w_id_max[0]['max'])
	db.close()
	return nb_days_players[0]['day_weather']

def calculate_profit(playersTab):
	'''
	Cette fonction renvoie une liste de dictionnaires ayant pour chacun
	pour clé le nom du joueur et pour valeur son profit.
	'''
	profitsTab = []	#Contient les profits de l'ensemble des joueurs

	db = Db()
	#Pour chacun des joueurs de la game
	for player in playersTab:
		#Récupération de la dernière journée de jeu
		lastday = get_lastGameDay()

		#Récupération de la quantité de production, le cout de production
		#Et le prix de vente d'une recette (fixé par le joueur)
		datas_prod_recipe = db.select("SELECT quantity_production, price_sale_production,\
			cost_prod_recipe FROM Production FULL JOIN Recipe ON recipe.id_recipe=\
			production.id_recipe WHERE (production.id_player = %d AND production.day_production = %d)"\
			%(player['id_player'], lastday))

		#Récupération du nombre de panneaux à placé (choisi par le joueur) et de leur prix
		datas_add = db.select("SELECT price_addspace, number_addspace FROM Addspace WHERE (id_player = %d\
			AND day_addspace = %d)" %(player['id_player'], lastday))

		#Récupération du nb de boissons achetés, aisni que leur nom et leur prix d'achat
		#pour le jour en cours
		datas_unblock = db.select("SELECT quantity_unblock, name_recipe, price_buying_recipe FROM Unblock \
			FULL JOIN Recipe ON recipe.id_recipe = unblock.id_recipe WHERE (day_unblock =%d\
			AND unblock.id_player = %d AND Recipe.isUnblocked_recipe = %s)" %(lastday, player['id_player'],\
			True))

		#On effectue les calculs intermédiaires
		recipe_production_cost = 0.0
		pub_cost = 0.0
		recipe_purchased_cost = 0.0

			#Celui du cout total de la production (quantité produite * cout de prod) pour chaque recette
		for prod in datas_prod_recipe:
			recipe_production_cost = recipe_production_cost + \
				(float(prod['quantity_production']) * float(prod['cost_prod_recipe']))
		
			#Celui du total des recettes debloqué au moment du jour de jeu (quantité * prix d'achatUnitaire)
		for abuy in datas_unblock:
			recipe_purchased_cost = recipe_purchased_cost +\
			(float(abuy['quantity_unblock']) * float(abuy['price_buying_recipe']))

			#Celui du total des pubs acheté pour le jour en cours (nbpanneauxpub * prix)
		for pub in datas_add:
			pub_cost = pub_cost + (float(pub['number_addspace']) * float(pub['price_addspace']))

			#Calcul des charges totale
		costs = pub_cost + recipe_purchased_cost + recipe_production_cost
		
		#Calcul du total des ventes d'un joueur
		incomes_sold = 0.0
		sales = db.select("SELECT quantity_sales FROM Sales WHERE (id_player = %d AND day_sales = %d)"\
			%(player['id_player'], lastday))

		for asold in sales:
			incomes_sold = incomes_sold + (float(asold['quantity_sales']) + \
				float(datas_prod_recipe[0]['price_sale_production']))

		#Calcul des bénéfices
		profits = incomes_sold - costs

		profitsTab.append({
			"name": player['name_player'],
			"profit":profits
			})
	db.close()
	print(profitsTab)
	return profitsTab

def get_profit(playersTab, playerName):
	'''
	Cette fonction permet d'obtenir le profit
	d'un joueur connu parmis l'ensemble des joueurs
	de la partie.
	'''
	#On récupère la liste des profits de chaque joueur
	playersProfit = calculate_profit(playersTab)

	#On défini le profit de joueur en parcourant la liste
	profit = 0.0
	for aplayer in playersProfit:
		if (aplayer['name'] == playerName):
			profit = aplayer['profit']
	print(profit)
	return profit

def get_available_ingredients(player_cash):
	db = Db()
	ingredient_datas = db.select("SELECT name_ingredient, price_ingredient FROM Ingredient")
	db.close()

	availableIngredients = []
	for ingredient in ingredient_datas:
		if (float(ingredient['price_ingredient']) <= float(player_cash)):
			availableIngredients.append({
				"name":ingredient['name_ingredient'],
				"price":ingredient['price_ingredient']
			})
	return availableIngredients

#Ces données gère des actions des joueurs
def addActionNewRecipe(datas, playername):
	'''
	Cette fonction gère le addAction
	'''
	print('coucou')

#A tester
def calculate_cost_prod(datas, playername):
	if not ('kind' in datas and 'prepare' in datas and 'price' in datas):
		return to_make_response('Bad Request', 400)

	db = Db()
	player = db.select("SELECT * FROM Player WHERE name_player = %(name)s", {
		"name":playername
		})

	if (len(player) != 1):
		return to_make_response('Internal Server Error', 500)

	#Récupération de la recette
		#Récupération du nom de la recette
	recipeName = datas['prepare'].keys()
	therecipeName = datas[0]

		#Récupération des données sur la recette
	recipe = db.select("SELECT * FROM Recipe WHERE (name_recipe = %(name)s and id_player = %(id)s)",{
		"name": therecipeName,
		"id": player[0]['id_player']
		})

	if (len(recipe) != 1):
		return to_make_response('Internal Server Error')

	#Calcul des couts de production (prix untaire d'une recette * quantité désiré par le gamer)
	cost = 0.0
	cost = float(recipe[0]['cost_prod_recipe']) * float(datas['prepare'])
	db.close()
	return cost

def calculate_cost_ad(datas, playername):
	if not ('nb_add' in datas):
		return to_make_response('Bad Request', 400)

	#Récupération du joueur
	player = db.select("SELECT * FROM Player WHERE name_player = %(name)s", {
		"name":playername
		})

	if (len(player) != 1):
		return to_make_response('Internal Server Error', 500)

	#Calcule des données en fonction des valeurs par défaut des pubs (prix * nb_pub defini par le client)
	cost = 0.0
	cost = float(default_price_pub) * datas['nb_add']

	db = Db()
	db.close()
	return cost

def filldb_playeractionsdrinks(datas, playername):
	#On récupère le jour actuel de la game. Et on ajoute un car les décisions se font au jour "j+1"
	day = get_lastGameDay()+1

	#Recupération des données du player
	player = db.select("SELECT * FROM Player WHERE name_player = %(name)s", {
		"name":playername
		})

	if (len(player) != 1):
		return to_make_response("Internal Server Error", 500)

	#Récupération de l'ensemble de la recette, qui en clé dans le dictionnaire "prepare"
	recipename = datas['prepare'].keys()
	the_recipe = datas[0]

	#Récupère l'id de la recette
	recipeID = db.select("SELECT id_recipe FROM Recipe WHERE name_recipe = %(name)s and id_player = %(id)s",{
		"name": the_recipe,
		"id": player[0]['id_player']
		})

	if (len(recipeID) != 1):
		return to_make_response('Internal Server Error', 500)

	#Récupération de la décision du joueur
	decision = player[0]['action_prodrecipe']

	#Si le joueur fait sa premiere décision
	if (decision == None or decision == False):
		#On crée une instance de la table Production
		product_creation = db.select("INSERT INTO Production(quantity_production,price_sale_production\
			day_production, id_recipe,id_player) VALUES(%(prod_quant)s, %(sellingprice)s,%(day)s\
			%(recipeid)s, %(idplayer)s) RETURNING id_production", {
				"prod_quant": datas['prepare'][the_recipe],
				"sellingprice": datas['price'][the_recipe],
				"recipeid": recipeID,
				"day": day, 
				"idplayer": player[0]['id_player']
			})

		if (len(product_creation) != 1):
			return to_make_response('Internal Server Error', 500)

		#Update des éléments du joueur comme quoi il a pris sa décision
		db.execute("UPDATE Player SET action_prodrecipe = %(prodaction)s", {
			"prodaction":True
			})

	#Si le joueur a déjà pris une décision aujourd'hui, donc on ecrase son ancienne décision
		#Récupération de l'élément à mettre à updaté
	prod_instance = db.select("SELECT * FROM Production WHERE (day_production = %(day)s AND\
		id_player = %(playerid)s AND id_recipe = %(recipeid)s)", {
		"day": day,
		"playerid":player[0]['id_player'],
		"recipeid": recipeID
	})

	if (len(prod_instance) != 1):
		return to_make_response('Internal Server Error', 500)

		#Update de l'élément (instance prod)
	db.execute("UPDATE Production SET quantity_production = %d, price_sale_production = %f\
	 day_production = %d, id_recipe = %d, id_player = %d" %(datas['prepare'][therecipeName],\
	 	datas['price'][therecipeName], theday, recipeID, player[0]['id_player']))

def filldb_playeractionsAdd(datas, playername):
	#On récupère les données du joueur
	db = Db()
		#Récupération du jour actuel et on ajoute +1 car les décisions sont exécutées au jour j+1
	day = get_lastGameDay()+1

		#Récupération du nombre de publicité que veut acheter le joueur
	nbPub = datas['nb_add']
	print(nbPub)

		#Récupération des données du player
	player = db.select("SELECT * FROM Player WHERE name_player = %(name)s", {
		"name":playername
		})

	if (len(playerID) != 1):
		return to_make_response('Internal Server Error', 500)

		#Récupération de la decision du joueur
	decision = player[0]['action_buyadds']

		#Si le joueur n'a jamais pris de décision
	if (decision == None or decision == False):
		index = 0
		while (index < datas['nb_add']):
			#On génère les coordonnées des panneaux dans la map
			location = generate_location()

			#On crée les panneaux publicitaires demandés par le joueur
			pub_creation = db.select("INSERT INTO Addspace(influence_addspace, lat_addspace, lon_addspace\
				day_addspace, price_addspace, id_player) VALUES %(influence)s, %(latitude)s, %(longitude)s\
				%(day)s, %(price)s, %(id)s RETURNING id_addspace", {
				"influence": default_rayon_pub,
				"latitude": location['latitude'],
				"longitude": location['longitude'],
				"day":day,
				"price":default_price,
				"id":player[0]['id_player']
			})

			if (len(pub_creation)!= 1):
				return to_make_response('Internal Server Error', 500)

			index = index + 1

		#On indique au joueur qu'il a pris une decision
		db.execute("UPDATE Player SET action_buyadds = %(buyaction)s", {
			"buyaction":True
			})

	#Si le joueur ne choisi pas pour la premier fois
		#On récupère l'id des différentes pubs au joueur.
	pubsID = db.select("SELECT id_addspace FROM Addspace WHERE (id_player = %(id)s AND day_addspace = \
		%(day)s", {
		"id":player[0]['id_player'], 
		"day":day
		})

	if(len(pubID) == 0):
		return to_make_response('Internal Server Error', 500)

		#On supprime l'intégralité des pubs qui ont été au préalable choisis.
	for anID in pubsID:
		db.execute("DELETE FROM Addspace WHERE id_pub = %(id)s",{
			"id":anID['id_addspace']
			})

		#On remplie la base avec le nombre de pub voulues par le joueur.
	index = 0
	while (index < datas['nb_add']):
		pub_creation = db.select("INSERT INTO Addspace(influence_addspace, lat_addspace, lon_addspace\
			day_addspace, price_addspace, id_player) VALUES %(influence)s, %(latitude)s, %(longitude)s\
			%(day)s, %(price)s, %(id)s RETURNING id_addspace", {
			"influence": default_rayon_pub,
			"latitude": location['latitude'],
			"longitude": location['longitude'],
			"day":day,
			"price":default_price,
			"id":player[0]['id_player']
		})

		if (len(pub_creation)!= 1):
			return to_make_response('Internal Server Error', 500)

		index = index + 1
	db.close()

