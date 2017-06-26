#-*- encoding:utf-8 -*-
import json
from flask import make_response
import random
from db import Db

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

def generate_location(minimum, maximum):
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

def playerActionDrinks(datas, playername):
	'''
	Cette fonction permet de gérer pour le joueur la production
	de recette qu'il a deja débloqué.
	'''
	print('passage dans la fonction qui gere les actions des joueurs')
	#La données est-elle conforme pour traitement
	if not ('kind' in datas and 'prepare' in datas and 'price' in datas):
		return to_make_response('Bad Request', 400)

	#La donnée est conforme, on la traite
	db = Db()
		#On récupère les données du joueur
	player = db.select("SELECT * FROM Player WHERE name_player = %(name)s", {
		"name":playername
		})

	if (len(player) != 1):
		return to_make_response("Internal Server Error", 500)

		#On regarde si le joueur a deja pris une décision pour cette action aujourd'hui
	decision_prod = player[0]['action_prodrecipe']

		#Cas où c'est la premiere decision du joueur
	if (decision_prod == None or decision_prod == False):*
		#Récupération du nom de la recette, qui est en clé dans un dictionnaire de la clé "prepare" de la data
		recipeName = datas['prepare'].keys()
		therecipeName = datas[0]

		print("the recipe name")
		print(therecipeName)
		print ("end")

		#Crée une instance production qui restera toute seule pendant toute une journée.
			#Récupération de l'id de la recette
		recipeID = db.select("SELECT id_recipe FROM Recipe WHERE name_recipe = %(name)s and id_player = %(id)s",{
			"name": therecipeName,
			"id": player[0]['id_player']
		})


		if (len(recipeID) != 1):
			return to_make_response('Internal Server Error', 500)



		#On crée alors une instance production qui restera seule jusqu'au jour suivant
		#D'abbord on récupère l'id de la recette, l'id du joueur
		#Ainsi que le jour suivant (actuel pour la bdd). Sur lequel on va enregistrer la decision de prod

		#Récupération du nom de la recette qui est une clé.




	if (len(recipeID) != 1):
		return to_make_response('Internal Server Error', 500)



	#On doit renvoyer le total des cout ainsi que le fonds necessaire présent (true) ou non (false)
	db.close()