#-*- encoding:utf-8 -*-
import json
from flask import make_response
import random
from db import Db

default_cash = 20.0
default_rayon = 10.0

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
	weather_max_id = db.select("SELECT MAX(id_weather) FROM Weather")
	current_day = db.select("SELECT day_weather FROM Weather \
	                         WHERE id_weather = %d" %weather_max_id[0]['max'])
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
	sales = db.select("SELECT * FROM Sales WHERE (id_player = %d AND day_sales = %d)" %(playerID, day))
	db.close()

	if (len(sales) == 0):
		return 0.0

	#Calcul des ventes totales effectuées
	soldtot = 0.0
	for asold in sales:
		soldtot = soldtot + float(asold['quantity_sales'])
	soldtot = round(soldtot, 3)
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
		return internal_server_error()
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
		return internal_server_error()

	costs = 0.0
	for arecipe in recipe_unblock_datas:
		costs = costs + (float(arecipe['quantity_unblock']) * float(arecipe['price_buying_recipe']))
	db.close()
	return costs

def get_totalCosts(playerID, day):
	'''
	Obtention des charges totales d'un joueur à un jour de jeu
	'''
	adsCosts = get_costTot_ads(playerID, day)
	#print(type(adsCosts))
	prodCosts = get_costTot_prod(playerID, day)
	#print(type(prodCosts))
	buyingCosts = get_costTot_buyingRecipe(playerID, day)
	#print(type(buyingCosts))
	totalCosts = adsCosts + buyingCosts + prodCosts
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
		return internal_server_error()

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



#A voir avec le pro parce que sincerement je ne comprebd pas pk cela beaugue
def join_new_player(playername, gameid):
	'''
	Crée et connecte un joueur à une partie
	'''
	db  = Db()
		#Génération des coordonnées du joueur dans la map
	location = generate_location()

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

	#Vérification
	player = db.select("SELECT * FROM Player WHERE id_player = %d" %(player_creation[0]['id_player']))
	if (len(player) != 1):
		return "Error -500"
	print(player)

	#Fin

	#Le joueur débloque tout de suite une recette rentrée dans la base de données
	#Cette recette est une limonade au citron et à l'eau
		#Récupération de la recette par défaut
	if (len(player_creation) == 1):
		default_recipe = db.select("SELECT * FROM Recipe WHERE id_player = %d" %(player_creation[0]['id_player']))

		if (default_recipe):
			return "Error -500"

		#La recette a bien été récupérée
		#On crée une instance de débloquer
	current_day = get_current_day()
	unblock_creation = db.select("INSERT INTO Unblock(day_unblock, quantity_unblock, id_player, id_recipe)\
		VALUES (%(day)s, %(quantity)s, %(player_id)s, %(recipe_id)s)", {
		"day": current_day,
		"quantity": 1,
		"player_id":player_creation[0]['id_player'],
		"recipe_id":default_recipe[0]['id_recipe']
		})

	#verif
	print(db.select("SELECT * FROM Unblock WHERE unblock_creation[0]['id_recipe']"))
	#Récupération des ingredients nécessaire à la requete pour update: citron
	ingredients = db.select("SELECT * FROM Ingredient WHERE id_ingredient = 1" )

	if (len(ingredients) == 0):
		return "Error -500"

	print(ingredients)

	#Création d'une instance compose
	creation_compose = db.select("INSERT INTO Compose(id_ingredient, id_recipe) VALUES \
		(%(ingredient_id)s, %(recipe_id)s)", {
		"ingredient_id": ingredients[0]['id_ingredient'],
		"recipe_id": recipe_creation[0]['id_recipe']
		})

	print(creation_compose)

	if (len(creation_compose) == 0):
		return "Error -500"

	print("je suis arrivé jusqu'a ici bordel de merde")
	#drinksOffered = get_drinksOffered(player_creation[0]['player_id'], "prod")
	resp = {
		"name":playername,
		"location": {
			"latitude": location[0]['lat_player'], 
			"longitude": location[0]['lon_player']
		},
		"playerInfo":get_player_infos(playername[0]['id_player'], gameid, "prod")

	}
	db.close()
	return resp


def get_player_infos(playerID, gameid, stringProdOrSellingPrice):
    '''
    Obtention des informations concernant un joueur
    qui se trouve dans la partie
    '''
    #Récupération de l'id du joueur
    db= Db()
    player = db.select("SELECT * FROM Player WHERE (id_player = %d AND ingame_player = %d)"\
        %(playerID, gameid))

    print(playerID)
    print(player)
    print(len(player))

    if (len(player) == 0):
        return {}

    playerInfos = {
        "cash": player[0]['cash_player'],
        "sales": get_numberTot_sold(playerID),
        "profit": get_profits(playerID), 
        "drinksOffered": get_drinksOffered(playerID, stringProdOrSellingPrice)
    }
    db.close()
    return playerInfos










'''
app.route('/players', methods=['POST'])
def join_game():

		#Cas où le joueur est déjà connecté à la game
	if (player_ingame == id_game_default):
		#Récupération de l'ensemble des joueurs de la game
		all_players = db.select("SELECT * FROM Player WHERE ingame_player = %(idgame)d"\
			%(id_game_default))

		if (len(all_players) == 0):
			return to_make_response('Internal Server Error')

		#Récupération des ventes effectuées par le joueur au jour en cours
			#Récupération du jour courant
		current_day = get_lastGameDay()

			#Récupération de l'ensemble des ventes du joueur pour le jour courant
		all_sales_player = db.select("SELECT quantity_sales FROM Sales WHERE (day_sales = %d AND \
			id_player=%d)" %(current_day, player[0]['name_player']))

		if (len(all_sales_player) == 0):
			return to_make_response('Internal Server Error', 500)

		#Calcul du total des ventes
		all_sales = 0
		for asold in sales:
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
			return to_make_response('Internal Server Error', 500)

			#Mise en forme de la réponse pour la clé drinksOffered
		drinksOffered = []
		for adrink in all_recipe:
			drinks.append({
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
	return to_make_response(resp)
'''
