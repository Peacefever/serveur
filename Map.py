#-*- encoding:utf-8 -*-
from db import Db
from others import *

default_game = 1

def get_region():
	'''
	Obtention des informations de coordonnées
	à propos de la map
	'''
	db = Db()
	the_map = db.select("SELECT * FROM Map")

	if(len(the_map) == 0):
		return internal_server_error()
	db.close()

	region = {
		"center": {
			"latitude": the_map[0]['lat_map'],
			"longitude": the_map[0]['lon_map']
		},
		"span": {
			"latitudeSpan": the_map[0]['lat_span_map'],
			"longitudeSpan": the_map[0]['lon_span_map']
		}
	}
	return region

def get_ranking():
	'''
	Obtention du ranking pour les joueurs d'une partie
	'''
	the_ranking = []
	db = Db()
	ranking = db.select("SELECT name_player FROM Player WHERE ingame_player = %d ORDER BY cash_player DESC"\
		%(default_game))

	if (len(ranking) == 0):
		return []
	db.close()

	for arank in ranking:
		the_ranking.append(arank['name_player'])
	return the_ranking

def get_mapitems(playerID):
	'''
	Obtention des items d'un joueur présent dans une partie
	'''
	db = Db()
	itemsPlayer = []

	#Récupération du jour courant
	day = get_current_day()

	if day == -1:
		return [] #Erreur. Pas de jour alors pas de mapsItemps possible

	#Récupération du joueur à partir de son id
	player = db.select("SELECT * FROM Player WHERE id_player = %d" %(playerID))

	if (len(player) != 1):
		return []

	#Récupération ads items
	items_ads = db.select("SELECT * FROM Adspace WHERE (id_player = %d AND day_adspace = %d)"\
		%(playerID, day))

	#Le joueur a choisi de ne pas prendre de support pub
	if (len(items_ads) == 0):
		itemsPlayer.append({
				"kind":"stand",
				"owner":player[0]['name_player'],
				"location": {
					"latitude": player[0]['lat_player'],
					"longitude": player[0]['lon_player']
				},
				"influence": player[0]['rayon_player']
			})

	if (len(items_ads) > 0):
		for anAdd in items_ads:
			itemsPlayer.append({
				"kind": "ad",
				"owner":player[0]['name_player'],
				"location": {
					"latitude": anAdd['lat_adspace'],
					"longitude":anAdd['lon_adspace']
				},
				"influence":anAdd['influence_adspace']
				})

		itemsPlayer.append({
					"kind":"stand",
					"owner":player[0]['name_player'],
					"location": {
						"latitude": player[0]['lat_player'],
						"longitude": player[0]['lon_player']
					},
					"influence": player[0]['rayon_player']
				})

	db.close()
	return itemsPlayer

def get_drinksOffered(playerID, stringProdOrSellingPrice):
	'''
	En fonction du stringProdOrSellingPrice, la fonction renvoie une liste
	de dictionnaire contenant:
		Nom de la recette,
		isCold :Bool, (si elle est froide ou chaude)
		hasalcohol:Bool (si elle contient de l'alcool),
		prix: vente (si stringProdOrSellingPrice = sold -JAVA) et production(si stringProdOrSellingPrice = prod)
	'''
	db = Db()

	drinksOffered = []
	
	#Cas du client JAVA -> selling_price
	if (stringProdOrSellingPrice == "sold"):
		#Récupération de l'ensemble des recette produites au jour j.
		#Toutes les recettes produites sont proposées au à la vente à un prix défini par le joueur
		day = get_current_day()

		print(day)

		if (day == -1):
			return []

		recipe_prod = db.select("SELECT * FROM Production WHERE (day_production = %d AND id_player = %d\
		)" %(day, playerID))

		#Cas dans lequel le joueur n'a rien produit => scénario impossible dans notre cas
		if (len(recipe_prod) == 0):
			return []
		
		#Pour chaque élément produition
		for aprod in recipe_prod:
			#On récupère la recette
			therecipe = db.select("SELECT * FROM Recipe WHERE id_recipe = %d AND id_player = %d"\
				%(aprod['id_recipe'], aprod['id_player']))

			#Mauvaise récupération
			if (len(therecipe) != 1):
				return []

			#Remplissage de la liste drinksOffered
			drinksOffered.append({
				"name": therecipe[0]['name_recipe'],
				"price":aprod['price_sale_production'], #Prix de vente
				"isCold":therecipe[0]['iscold_recipe'],
				"hasAlcohol":therecipe[0]['hasalcohol_recipe']
				})

	#Cas du client html -> price = cost_production_recipe
	if (stringProdOrSellingPrice == "prod"):
		#On récupère l'ensemble des recettes qui sont débloquées
		recipe_unlock = db.select("SELECT * FROM Recipe WHERE (isUnblocked_recipe = %(unblocked)s AND \
			id_player = %(id)s)", {
			"unblocked": True,
			"id":playerID
		})

		#Cas où le joueur n'a aucune recette de débloquée ==> impossible dans notre cas.
		#En effet, une recette est automatiquement débloquée lorsque le joueur débute une partie.
		if (len(recipe_unlock) == 0):
			return []

		for arecipe in recipe_unlock:
			#Remplissage de la liste drinksOffered
			drinksOffered.append({
				"name": arecipe['name_recipe'],
				"price": arecipe['cost_prod_recipe'], #Cout de production
				"isCold": arecipe['iscold_recipe'],
				"hasAlcohol": arecipe['hasalcohol_recipe']
				})

	db.close()
	return drinksOffered

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

def join_new_player(playername, gameid):
	'''
	Cette fonction permet à un joueur de rejoindre une partie
	'''

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

	print(citron_ingredient)
	print("Fin recup citron")

	eau_de_source_ingredient = db.select("SELECT * FROM Ingredient WHERE name_ingredient = %(name)s", {
		"name":'Eau de source'
		})

	if (len(eau_de_source_ingredient) == 0 or eau_de_source_ingredient == None):
		return -1

	print(eau_de_source_ingredient)
	print("fin eaux de source")

	#Création deux instances de Compose
	print("Commencement")

	for index in xrange(1, 3):
		#Vérification de l'existence
		exist = db.select("SELECT COUNT(*) FROM Compose WHERE (id_ingredient = %(ing_id)s AND id_recipe = %(rec_id)s)", {
			"ing_id":index,
			"rec_id":default_recipe_id
			})

		#Si cela existe pas
		if (exist == None or len(exist) == 0 or exist[0]['count'] == 0):
			db.execute("INSERT INTO Compose(id_ingredient, id_recipe) VALUES \
					(%(ingr_id)s, %(r_id)s)", {
					"ingr_id": index,
					"r_id": default_recipe_id
					})

			print("Fin de la création affichage")
			print(db.select("SELECT * FROM Compose"))
			print("OK")

	print(db.select("SELECT * FROM Compose"))
	print("Fin")
	db.close()

	resp = {
		"name":playername,
		"location":{
			"latitude": player[0]['lat_player'],
			"longitude":player[0]['lon_player']
		},
		"info": get_player_infos(player[0]['id_player'], default_game, "prod")
	}
	return resp
