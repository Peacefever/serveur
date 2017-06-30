DROP TABLE IF EXISTS Recipe CASCADE;
DROP TABLE IF EXISTS Production CASCADE;
DROP TABLE IF EXISTS Unblock CASCADE;
DROP TABLE IF EXISTS Sales CASCADE;
DROP TABLE IF EXISTS Player CASCADE;
DROP TABLE IF EXISTS Weather CASCADE;
DROP TABLE IF EXISTS Map CASCADE;
DROP TABLE IF EXISTS Ingredient CASCADE;	/*a*/
DROP TABLE IF EXISTS Compose CASCADE;		/*a*/
DROP TABLE IF EXISTS Adspace CASCADE; 		/*a*/

CREATE TABLE Recipe(
	id_recipe 				SERIAL PRIMARY KEY,
	name_recipe				Varchar(25),
	price_buying_recipe		Float,		/*Prix d'achat d'une recette*/
	cost_prod_recipe		Float,		/*Cout de production d'une recette*/
	isCold_recipe			Boolean,	/*a*/
	hasAlcohol_recipe		Boolean, 	/*a*/
	isUnblocked_recipe		Boolean,	/*a. Sert a voir si une boisson a été debloqué dans la journée*/  
	/*Foreign keys*/
	id_player				Int
);

CREATE TABLE Production(
	id_production 				SERIAL PRIMARY KEY,
	quantity_production 	Int,
	price_sale_production	Float, 			/*Prix de vente d'une recette fixé par le joueur*/
	day_production			Int,
	/*Foreign keys*/
	id_recipe				Int,
	id_player 				Int
);

CREATE TABLE Unblock(
	day_unblock				Int,
	quantity_unblock		Int, /*Add*/
	/*Foreign keys*/
	id_player				Int,
	id_recipe				Int,
	PRIMARY KEY (id_player, id_recipe)
);

CREATE TABLE Sales(
	quantity_sales			Int,
	day_sales				Int,
	/*Foreign keys*/
	id_player				Int,
	id_recipe				Int,
	PRIMARY KEY (id_player, id_recipe)
);

CREATE TABLE Player(
	id_player 				SERIAL PRIMARY KEY,
	name_player 			Varchar(25),
	/*connected_player		Boolean,*/
	lon_player				Float,
	lat_player				Float,
	cash_player				Float,
	rayon_player			Float,
	isConnected_player 		Boolean, 	/*a*/
	ingame_player			Int, 		/*a*/
	action_buynewrecipe		Boolean,
	action_buyadds			Boolean,
	action_prodrecipe		Boolean
);

/*Day courant*/
CREATE TABLE Weather(
	id_weather				SERIAL PRIMARY KEY,
	now_weather				Varchar(25),
	tomorrow_weather		Varchar(25),
	day_weather				Int
);

CREATE TABLE Map(
	id_map					SERIAL PRIMARY KEY,
	lat_map					Float,
	lon_map					Float,
	lat_span_map			Float,
	lon_span_map			Float
);

/*a*/
CREATE TABLE Ingredient(
	id_ingredient 			SERIAL PRIMARY KEY,
	name_ingredient 		Varchar(25),
	price_ingredient		Varchar(25)
);

/*a*/
CREATE TABLE Compose(
	id_ingredient 			Int,
	id_recipe 				Int,
	PRIMARY KEY (id_recipe, id_ingredient)
);

/*a*/
CREATE TABLE Adspace(
	id_adspace 			SERIAL PRIMARY KEY,
	influence_adspace	Float,
	lat_adspace			Float,
	lon_adspace			Float,
	day_adspace 		Int,
	price_adspace		Float,
	number_adspace		Int,	
	id_player 			Int
);

ALTER TABLE Recipe 	ADD CONSTRAINT FK_recipe_id_player FOREIGN KEY (id_player) REFERENCES Player(id_player);
ALTER TABLE Production ADD CONSTRAINT FK_production_id_recipe FOREIGN KEY (id_recipe) REFERENCES Recipe(id_recipe);
ALTER TABLE Production ADD CONSTRAINT FK_production_id_player FOREIGN KEY (id_player) REFERENCES Player(id_player);
ALTER TABLE Sales ADD CONSTRAINT FK_sales_id_player FOREIGN KEY (id_player) REFERENCES Player(id_player);
ALTER TABLE Sales ADD CONSTRAINT Fk_sales_id_recipe FOREIGN KEY (id_recipe) REFERENCES Recipe(id_recipe);
ALTER TABLE Unblock ADD CONSTRAINT Fk_unblock_id_player FOREIGN KEY (id_player) REFERENCES Player(id_player);
ALTER TABLE Unblock ADD CONSTRAINT Fk_unblock_id_recipe FOREIGN KEY (id_recipe) REFERENCES Recipe(id_recipe);

/*a*/
ALTER TABLE Compose ADD CONSTRAINT FK_compose_id_recipe FOREIGN KEY (id_recipe) REFERENCES Recipe(id_recipe);
ALTER TABLE Compose ADD CONSTRAINT FK_compose_id_ingredient FOREIGN KEY (id_ingredient) REFERENCES Ingredient(id_ingredient);
ALTER TABLE Adspace ADD CONSTRAINT Fk_addspace_id_player FOREIGN KEY (id_player) REFERENCES Player (id_player);

/*a*/

INSERT INTO Player (name_player, lon_player, lat_player, cash_player, rayon_player, isConnected_player,ingame_player) VALUES
	('toto', 75, 10, 100, 100.0, true, 1), 
	('babar', 50, 25, 200, 100.0, true, 1);

INSERT INTO Recipe (name_recipe, price_buying_recipe, cost_prod_recipe, isCold_recipe, hasAlcohol_recipe, isUnblocked_recipe, id_player) VALUES
	('Limonade', 10.0, 2.0, true, false, true,1),
	('Cafe', 1.0, 2.3, true, true, true, 1),
	('Coca-cola', 0.5, 1, true, false, true,2);

INSERT INTO Ingredient(name_ingredient, price_ingredient) VALUES
	('Citron', 0.2),
	('Eau de source', 0.1),
	('Vodka', 2.0), 
	('Annanas', 0.2),
	('Cafe Arabica', 3.0),
	('Sel guerande', 1000);

/*INSERT INTO Compose (id_ingredient, id_recipe) VALUES 
	(1, 1),
	(2, 1), 
	(5, 2),
	(4, 3);*/


INSERT INTO Unblock(day_unblock, quantity_unblock, id_player, id_recipe) VALUES
	(1, 0, 1, 1),
	(1, 0, 1, 2),
	(1, 0, 2, 3);

/*Sales production est le prix de vente choisi par l'utilisateur*/
/*INSERT INTO Production(quantity_production, price_sale_production, day_production, id_recipe, id_player) VALUES
	(2, 10.0, 1, 1, 1),
	(2, 10.0, 1, 2, 1),
	(4, 5.0, 1, 3, 2);*/

/*Les ventes simulent le programme JAVA. C'est une table pour la fin de journée(recap)*/
/*INSERT INTO Sales(quantity_sales, day_sales, id_player, id_recipe) VALUES 
	(2, 1, 1, 1),
	(3, 1, 1, 2),
	(3, 1, 2, 3); */

INSERT INTO Weather(now_weather, tomorrow_weather, day_weather) VALUES
	('Sunny', 'Cloudy', 1),
	('Sunny', 'Rainy', 2);

INSERT INTO Map (lat_map, lon_map, lat_span_map, lon_span_map) VALUES 
	(100, 100.0, 200.0, 200.0);

/*
INSERT INTO Adspace (influence_adspace, lat_adspace, lon_adspace, day_adspace, price_adspace, number_adspace, id_player) VALUES 
	(2.3, 13.5, 14.6, 1, 25.0, 2 ,1),
	(2.37, 45, 56, 1, 5.0, 2 ,1),
	(6.5, 1.2, 16.5, 1, 36.0, 3, 2);
*/
