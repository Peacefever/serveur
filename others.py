#-*- encoding:utf-8 -*-
import json
from flask import make_response
import random
from db import Db

default_cash = 20.0
default_rayon = 10.0
default_recipe_id = 1
default_influency_pub = 10.0
default_price_pub = 20.0

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

	if (weather_max_id == None or len(weather_max_id) == 0):
		return -1

	current_day = db.select("SELECT day_weather FROM Weather \
	                         WHERE id_weather = %d" %weather_max_id[0]['max'])

	if (current_day == None or len(current_day) == 0):
		return -1

	db.close()
	var toReturn = current_day[0]['day_weather']
	toReturn = toReturn - 1
	return toReturn

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

def generate_location():
	location = {}
	#Génération aléatoire puis arrondis
	lat = -100.0
	lon = 200.0
	lat_span = 20.0
	lon_span = 40.0
	db = Db()
	themap = db.select("SELECT * FROM Map")
	db.close()

	x_location_min = themap[0]['lon_map'] - themap[0]['lat_span_map']
	x_location_max = themap[0]['lon_map'] + themap[0]['lat_span_map']

	y_location_min = themap[0]['lat_map'] - themap[0]['lat_span_map']
	y_location_max = themap[0]['lat_map'] + themap[0]['lat_span_map']

	#Génération de la location aleatoire
	x_location = random.uniform(x_location_min, x_location_max)
	y_location = random.uniform(y_location_min, y_location_max)

	print(x_location)
	print(y_location)

	location['latitude'] = round(x_location, 5)
	location['longitude'] = round(y_location, 5)
	
	return location


#Fonctionnelle
def save_kind_ad_action(datas, playerID, day):

	db = Db()
	print('passage dans le add')
	print(datas)
	print('fin affichage datas')

	#On regarde si une instance de la table Adspace existe déjà pour le jour day
	exist = db.select("SELECT COUNT(*) FROM Adspace WHERE (day_adspace = %d AND id_player = %d)"\
		%(day, playerID))

	print('exist')
	print(exist)
	print('fin exist')

	#Pour le moment, le joueur ne peut pas placer ses panneaux, docn on génère leur localisation dans la map
	ad_coor = generate_location()
	
	#L'instance n'existe pas en base, donc on la crée
	if (exist[0]['count']==0 or len(exist) == 0 or exist == None):
		print('Joueur existe pas')
		db.execute("INSERT INTO Adspace (influence_adspace, lat_adspace, lon_adspace, day_adspace, \
			price_adspace, number_adspace, id_player) VALUES (%(influence)s, %(lat)s, %(lon)s, %(day)s,\
		%(price)s, %(nb)s, %(p_id)s)", {
		"influence": default_influency_pub,
		"lat": ad_coor['latitude'],
		"lon":ad_coor['longitude'],
		"day":day,
		"price":default_price_pub,
		"nb": datas['nb'],          #Si possible il faut que le nb soit envoyé par le joueur
		"p_id": playerID
		})
		print('Fin création')

	#L'isntance existe en base, on l'update
	if (exist[0]['count'] == 1):
		db.execute("UPDATE Adspace SET number_adspace = %d" %(int(datas['nb'])))

	print("Verification")
	print(db.select("SELECT * FROM Adspace"))
	db.close()

#Fonctionnelle
def save_kind_prod_action(datas, playerID, day):
	print("passage dans le prod")
	db = Db()
	exist = db.select("SELECT COUNT(*) FROM Production WHERE (day_production = %d AND id_player = %d)"\
		%(day, playerID))

	#Le joueur ne peut mettre à disposition des clients que ce qu'il vends.
	#Le joueur ne peut produire que les recettes qui ont été débloquées.
	#Récupération du nom de la recette préparée
	therecipe = datas['prepare'].keys()[0]
	theprod_quantity = datas['prepare'][therecipe]
	theprice_selling = datas['price'][therecipe]

	print(exist[0]['count'])

	#La decision de prod existe en base. Donc on update l'instance en question
	if (exist[0]['count'] == 1):
		recipe = db.select("SELECT * FROM Recipe WHERE (name_recipe = %(name)s AND id_player = %(id)s)", {
			"name":therecipe,
			"id":playerID
			})

		print("le choix existe")
		db.execute("UPDATE Production SET quantity_production = %d, price_sale_production = %f\
			WHERE (id_recipe = %d AND id_player = %d)" %(int(theprod_quantity), int(theprice_selling),\
				int(recipe[0]['id_recipe']), int(playerID)))

		#Vérification de l'update
		print(db.select("SELECT * FROM Production WHERE (id_player = %d AND id_recipe = %d)"\
			%(playerID, recipe[0]['id_recipe'])))

	print("enregistrement du choix de production")
	print(exist)

	#Le choix de la décision n'existe pas dans la base de données
	if (exist[0]['count'] == 0 or len(exist) == 0 or exist == None):
		print("chiox n'existe pas")
		recipe = db.select("SELECT * FROM Recipe WHERE (name_recipe = %(name)s AND id_player = %(id)s)", {
			"name":therecipe,
			"id":playerID
			})

		#Si la recette existe en base
		if (len(recipe) > 0 and recipe != None):
			#Création de la table production
			db.execute("INSERT INTO Production(quantity_production, \
				price_sale_production, day_production, id_recipe, id_player) VALUES (%(quantity)s, \
					%(price)s, %(day)s, %(r_id)s, %(p_id)s)", {
			"quantity": theprod_quantity,
			"price": theprice_selling,
			"day": day,
			"r_id": recipe[0]['id_recipe'],
			"p_id": playerID
			})

			#Vérification de création
			print("VERIF CREATUION")
			print(db.select("SELECT * FROM Production WHERE (id_player = %d AND id_recipe = %d)"\
				%(playerID, recipe[0]['id_recipe'])))
			print("NON VERIF")
	db.close()

def save_kind_buy_recipe_action(datas, playerID, day):
	print("a implémenter si le temps nous le permet")
