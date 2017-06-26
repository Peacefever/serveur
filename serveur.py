#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask, request
from flask import render_template
from db import Db # voyez db.py

import json
import random
import os
import psycopg2
import urlparse

app = Flask(__name__, static_url_path='')
app.debug = True
db = Db()
# Fonction de réponse
def jsonResponse(data, status=200):
  return json.dumps(data), status, {'Content-Type': 'application/json'}
@app.route("/")
def connexion():
  return app.send_static_file('connexion.html')
# Requête R8 - Reset
@app.route("/reset", methods=["GET"])
def reset():
    #return json.dumps(json_table[len(json_table)-1])
    return "OK:RESET"

# Requête R4 - Rejoindre une partie
@app.route("/players", methods=["POST"])
def addPlayer():
    data = request.get_json()
    if 'name' in data:
        test = db.select("SELECT * FROM Monster WHERE Aquatique=1")
        table = "{\"name\": \""+data['name']+"\",\"infoPlayer\": {\"location\": [{\"latitude\": 25}, {\"longitude\": 50}],\"argent\": [{\"dispo\": 1.0}, {\"ventes\": 0.0}, {\"profit\": 0.0}]}}"
        #table = "{\"name\": \""+db.rowcount+"\",\"infoPlayer\": {\"location\": [{\"latitude\": 25}, {\"longitude\": 50}],\"argent\": [{\"dispo\": 1.0}, {\"ventes\": 0.0}, {\"profit\": 0.0}]}}"
    print table
    return json.dumps(table), 200, { "Content-Type": "application/json" }

# Requête R4 - Quitter une partie
@app.route("/players/<playerName>", methods=["DELETE"])
def deletePlayer(playerName):
    #if (playerName == ""):
    return "OK:DELETE " + playerName

# Requête R1/R7 - Metrology
@app.route("/metrology", methods=["GET", "POST"])
def metrology():
    global json_table
    if request.method == "GET":
        return "OK:GET_METROLOGY"
    elif request.method == "POST":
        return "OK:POST_METROLOGY"

    #return json.dumps(json_table), 200, {'Content-Type': 'application/json'}

# Requête R3 - Sales
@app.route("/sales", methods=["POST"])
def sales():
    global json_table
    get_json = request.get_json()
    #json_table[value].update(get_json)
    print (get_json)

    return "OK:POST_SALES"

# Requête R6 - Instructions du joueur
@app.route("/actions", methods=["POST"]) #/action/<playername>
def actionsPlayer():#playerName):
    #global json_table
    #return json.dumps(json_table[value])
    data = request.get_json()
    return json.dumps(data), 200, { "Content-Type": "application/json" }

# Requête R2 -  Map
@app.route("/map", methods=["GET"])
def map():
    #return json.dumps(json_table)
    return "OK:GET_MAP"

# Requête R5 - Détails d'une partie
@app.route("/map/<playerName>", methods=["GET"])
def mapPlayer(playerName):
    return "GET:OK_MAP_PLAYER" + playerName

# Requête R9 - Liste ingrédients
@app.route("/ingredients", methods=["GET"])
def ingredients():
    return "GET:OK_INGREDIENTS"

if __name__ == "__main__":
    app.run(host="0.0.0.0",debug=True)
