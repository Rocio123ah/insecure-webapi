import json
import random
import hashlib
import mysql.connector
import base64
import shutil
from datetime import datetime
from pathlib import Path
from bottle import route, run, template, post, request, static_file, default_app



def loadDatabaseSettings(pathjs):
	pathjs = Path(pathjs)
	sjson = False
	if pathjs.exists():
		with pathjs.open() as data:
			sjson = json.load(data)
	return sjson
	
"""
function loadDatabaseSettings(pathjs):
	string = file_get_contents(pathjs);
	json_a = json_decode(string, true);
	return json_a;

"""
def getToken():
	import secrets
	part1 = secrets.token_hex(10)
	part2 = secrets.token_hex(16)
	part3 = secrets.token_hex(10)
	return part1 + part2 + part3

"""
*/ 
# Registro
/*
 * Este Registro recibe un JSON con el siguiente formato
 * 
 * : 
 *		"uname": "XXX",
 *		"email": "XXX",
 * 		"password": "XXX"
 * 
 * */
"""
@post('/Registro')
def Registro():
	dbcnf = loadDatabaseSettings('config/db.json');
	db = mysql.connector.connect(
		host='0.0.0.0', port = dbcnf['port'],
		database = dbcnf['dbname'],
		user = dbcnf['user'],
		password = dbcnf['password']
	)
	####/ obtener el cuerpo de la peticion
	if not request.json:
		return {"R":-1}
	R = 'uname' in request.json and 'email' in request.json and 'password' in request.json
	# TODO checar si estan vacio los elementos del json
	if not R:
		return {"R":-1}
	import re
	email = request.json.get('email', '')
	email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
	if not re.match(email_pattern, email):
		return {"R": -1, "error": "Email invalido"}
	# TODO validar correo en json
	# TODO Control de error de la DB
	R = False
	try:
		with db.cursor() as cursor:
			cursor.execute('INSERT INTO Usuario VALUES(null, %s, %s, md5(%s))'
					(request.json["uname"], request.json["email"], request.json["password"]));
			R = cursor.lastrowid
			db.commit()
		db.close()
	except Exception as e:
		print(e) 
		return {"R":-2}
	return {"R":0,"D":R}




"""
/*
 * Este Registro recibe un JSON con el siguiente formato
 * 
 * : 
 *		"uname": "XXX",
 * 		"password": "XXX"
 * 
 * 
 * Debe retornar un Token 
 * */
"""

@post('/Login')
def Login():
	dbcnf = loadDatabaseSettings('config/db.json');
	db = mysql.connector.connect(
		host='localhost', port = dbcnf['port'],
		database = dbcnf['dbname'],
		user = dbcnf['user'],
		password = dbcnf['password']
	)
	###/ obtener el cuerpo de la peticion
	if not request.json:
		return {"R":-1}
	######/
	R = 'uname' in request.json  and 'password' in request.json
	# TODO checar si estan vacio los elementos del json
	if not R:
		return {"R":-1}
	
	# TODO validar correo en json
	# TODO Control de error de la DB
	R = False
	try:
		with db.cursor() as cursor:
			cursor.execute('SELECT id FROM Usuario WHERE uname = %s AND password = md5(%s)'
					(request.json["uname"], request.json["password"]));
			R = cursor.fetchall()
	except Exception as e: 
		print(e)
		db.close()
		return {"R":-2}
	
	
	if not R:
		db.close()
		return {"R":-3}
	
	T = getToken();
	#file_put_contents('/tmp/log','insert into AccesoToken values('.R[0].',"'.T.'",now())');
	with open("/tmp/log","a") as log:
		log.write(f'Delete from AccesoToken where id_Usuario = "{R[0][0]}"\n')
		log.write(f'insert into AccesoToken values({R[0][0]},"{T}",now())\n')
	
	
	try:
		with db.cursor() as cursor:
			cursor.execute('DELETE FROM AccesoToken WHERE id_Usuario = %s' (R[0][0]));
			cursor.execute('INSERT INTO AccesoToken VALUES (%s, %s, now()', (R[0][0], T));
			db.commit()
			db.close()
			return {"R":0,"D":T}
	except Exception as e:
		print(e)
		db.close()
		return {"R":-4}

"""
/*
 * Este subir imagen recibe un JSON con el siguiente formato
 * 
 * 
 * 		"token: "XXX"
 *		"name": "XXX",
 * 		"data": "XXX",
 * 		"ext": "PNG"
 * 
 * 
 * Debe retornar codigo de estado
 * */
"""
@post('/Imagen')
def Imagen():
	#Directorio
	tmp = Path('tmp')
	if not tmp.exists():
		tmp.mkdir()
	img = Path('img')
	if not img.exists():
		img.mkdir()
	
	###/ obtener el cuerpo de la peticion
	if not request.json:
		return {"R":-1}
	######/
	R = 'name' in request.json  and 'data' in request.json and 'ext' in request.json  and 'token' in request.json
	# TODO checar si estan vacio los elementos del json
	if not R:
		return {"R":-1}
	allowed_extensions = ['png', 'jpg', 'jpeg', 'gif', 'webp']
	ext = request.json.get('ext', '').lower()
	if ext not in alloed_extensions:
		return {"R":-1, "error": "extension de archivo no es permitida"}
	
	dbcnf = loadDatabaseSettings('config/db.json');
	db = mysql.connector.connect(
		host='localhost', port = dbcnf['port'],
		database = dbcnf['dbname'],
		user = dbcnf['user'],
		password = dbcnf['password']
	)

	# Validar si el usuario esta en la base de datos
	TKN = request.json['token'];
	
	R = False
	try:
		with db.cursor() as cursor:
			cursor.execute('SELECT id_Usuario FROM AccesoToken WHERE token = %s', (TKN,));
			R = cursor.fetchall()
	except Exception as e: 
		print(e)
		db.close()
		return {"R":-2}
	
	
	id_Usuario = R[0][0]:
	import re
	base64_str = request.json.get('data', '')
	if not re.match(r'^[A-Za-z0-9+/]*={0,2}$', base64_str):
		db.close()
		return {"R": -5, "error": "archivo muy grande"}
	with open(f'tmp/{id_Usuario}_{request.json["name"]}',"wb") as imagen:
		imagen.write(base64.b64decode(request.json['data'].encode()))
	
	############################
	############################
	# Guardar info del archivo en la base de datos
	try:
		with db.cursor() as cursor:
			cursor.execute('INSERT INTO Imagen VALUES (null, %s, %s, %s)',
					(request.json["name"], "img/", id_Usuario));
			cursor.execute('SELECT max(id) as idImagen FROM Imagen WHERE id_Usuario = %s', (id_Usuario,));
			R = cursor.fetchall()
			idImagen = R[0][0];
			cursor.execute('UPDATE Imagen SET ruta = %s WHERE id = %s',
					(f"img/{idImagen}.{request.json['ext']}", idImagen));
			db.commit()
			# Mover archivo a su nueva locacion
			shutil.move(f'tmp/{id_Usuario}_{request.json["name"]}',f'img/{idImagen}.{request.json["ext"]}')
			return {"R":0,"D":"Imagen subida exitosamente"}
	except Exception as e: 
		print(e)
		db.close()
		return {"R":-3}
	
"""
/*
 * Este Registro recibe un JSON con el siguiente formato
 * 
 * : 
 * 		"token: "XXX",
 * 		"id": "XXX"
 * 
 * 
 * Debe retornar un Token 
 * */
"""

@post('/Descargar')
def Descargar():
	dbcnf = loadDatabaseSettings('config/db.json');
	db = mysql.connector.connect(
		host='localhost', port = dbcnf['port'],
		database = dbcnf['dbname'],
		user = dbcnf['user'],
		password = dbcnf['password']
	)
	
	
	###/ obtener el cuerpo de la peticion
	if not request.json:
		return {"R":-1}
	######/
	R = 'token' in request.json and 'id' in request.json  
	# TODO checar si estan vacio los elementos del json
	if not R:
		return {"R":-1}
	
	# TODO validar correo en json
	# Comprobar que el usuario sea valido
	TKN = request.json['token'];
	idImagen = request.json['id'];
	
	R = False
	try:
		with db.cursor() as cursor:
			cursor.execute('SELECT id_Usuario FROM AccesoToken WHERE token = %s',(TKN,));
			R = cursor.fetchall()
	except Exception as e: 
		print(e)
		db.close()
		return {"R":-2}
		
	
	
	# Buscar imagen y enviarla
	
	try:
		with db.cursor() as cursor:
			#VERIFICA QUE LA IMAGEN PERTENEZCA AL USUARIO
			cursor.execute('''SELECT i.name, i.ruta
					FROM Imagen i
					JOIN AccesoToken at ON i.id_Usuario=at.id_Usuario
					WHERE i.id=%s AND at.token=%s''',
					(IdImagen,TKN))
			R = cursor.fetchall()
			#NUEVA VALIDACION
			if not R:
				db.close()
				return {"R":-4, "error": "Imagen no encontrada no tienes permisos"}
	except Exception as e: 
		print(e)
		db.close()
		return {"R":-3}
	print(Path("img").resolve(),R[0][1])
	return static_file(R[0][1],root='.')
app = application = default_app()

if __name__ == '__main__':
    run(host='0.0.0.0', port=8443, debug=True,
	server='cheroot',
        certfile='./178.128.72.88+2.pem',
        keyfile='./178.128.72.88+2-key.pem')
