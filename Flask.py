# -*- coding: utf-8 -*-
"""
Created on Wed Apr 12 16:06:39 2023

@author: tybal
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Apr 10 16:06:39 2023

@author: tybal
"""
import random
import sqlite3
import os
from flask import Flask, render_template, request, session

import datetime
from datetime import date, timedelta
import secrets

import traceback
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d
import pandas as pd
import matplotlib.image as mpimg
from flask import redirect, url_for
from aifc import Error
from matplotlib.offsetbox import TextArea, DrawingArea, OffsetImage, AnnotationBbox

app = Flask(__name__)
app.secret_key = '04a7c9f9fa49553ddd4a73798a8ccd7b947268e5b74d23b4aaddaa56484dcb08'

def temps():
    now = datetime.now()
    time_h_m = str(now.hour)+':'+str(now.minute) 
    todays = date.today()
    today = todays.strftime("%d-%m-%Y")
    return [(str(today) +' à '+ time_h_m ), todays]


#-------------------------------------------------------------------------------------------------
                        #fonction de connection
def connection():  
    if not os.path.exists('db/GoTrip.db'):
        print(f"Le fichier {'db/GoTrip.db'} n'existe pas")
        connection = None
    else:         
        try:
            connection = sqlite3.connect('db/GoTrip.db')
            print("Connection to SQLite réussi")
        except:
            print("an error occured")
    return connection
 
#--------------------------------------------------------------------------------------------------------------------------
                        #fonction pour effectuer des requêtes    
def requete(connection, SQL:str):
    try:
        cursor = connection.cursor()
        cursor.execute(SQL)
        result = cursor.fetchall()
        print(result)
    except Error as e:
       print(f"The error {e} occured")   
       
    return result
        


def CreateConnexion():
    if not os.path.exists('db/GoTrip.db'):
        print(f"Le fichier {'db/GoTrip.db'} n'existe pas")
        connection = None
    else:         
        try:
           connection = sqlite3.connect("db/GoTrip.db")
        except Error as e:
           print(f"The error {e} occured")

    return connection
           
def ExecuteQuery(connection, query:str):
    
    try:
        cursor = connection.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        print(result)
    except Error as e:
       print(f"The error {e} occured")   
       
    return result 
        
#-------------------------------------------------------------------------------------------------
                        #Direction vers la page index
@app.route("/index", methods=['GET', 'POST']) 
@app.route("/", methods=['GET', 'POST']) 
def index():
    
    mail=""
    if "mail" in session:
        connecter = True
        mail = session["mail"]
    else: 
        connecter = False
    
        if request.method == 'POST':
            session["verif"] = request.form['identifiant']
            session["verifmdp"] = request.form['password']
        
            return redirect(url_for ('login'))
    return render_template("index.html",connecter=connecter, mail=mail)




@app.route("/login")
def login():
        
    check = requete(connection(), f'''SELECT MotDePasse from CLIENT WHERE mailCli = '{session["verif"]}' ''')
    listeMail = []  
    for elem in check:
        for donnee in elem:
            listeMail.append(donnee)
    print(listeMail[0])
    mailOK=""
    if str(listeMail[0]) == session["verifmdp"]:
        session['mail'] = session["verif"]
        mailOK = session['mail']
        connecter = True
    else:
        connecter = False
    
             
    return render_template("login.html", connecter=connecter, mailOK = mailOK)    

@app.route("/logout", methods=['GET', 'POST']) 
def logout():
    
    session.pop('mail', None)
    
    if request.method == 'POST':
        session["verif"] = request.form['identifiant']
        session["verifmdp"] = request.form['password']
    
        return redirect(url_for ('login'))   
    return render_template("logout.html")    
#-------------------------------------------------------------------------------------------------
                        #Fonction pour vérifier l'adresse mail
def check_email(email):
    con = connection()
    cur = con.cursor()
    cur.execute(f"select * from client where mailcli = '{email}'")
    if cur.fetchone():
        con.close()
        return True
    else:
        con.close()
        return False
    
#--------------------------------------------------------------------------------------------------
                        #Fonction pour insérer une ligne dans la bd
    
def insert_row_normal(con, SQL): 
    cur = con.cursor()
    try:
        cur.execute(SQL)
        con.commit()
        succes = True 
        erreur = ''
    except sqlite3.OperationalError as op:
        erreur = f"SQL error {op} occured"
        succes = False
    except sqlite3.Error as e:
        erreur = f"The error {e} occured"
        succes = False
    con.close()
    return [succes, erreur]
    

#---------------------------------------------------------------------
                       #Direction vers page formulaire inscription
@app.route("/formulaire/inscription", methods=['GET', 'POST']) 
def formulaire_inscription():
    
    if request.method == 'POST':
        session["verif"] = request.form['identifiant']
        session["verifmdp"] = request.form['password']
    
        return redirect(url_for ('login'))
    
    return render_template("SignUP.html", value=0)
    

#---------------------------------------------------------------------
                       #page formulaire : 1- vérifier l'adresse mail


@app.route("/formulaire/inscription/mail", methods=['POST'])
def Verification_mail():
    email = request.form['email']
    check = check_email(email)
    if check == True:
        text = "!!! L'adresse mail saisie existe déja !!!"
        return render_template("SignUP.html", value=0, text=text)
    else:
        session['email'] = email
        return render_template("SignUP.html", value=1)
    
#---------------------------------------------------------------------
                       #page formulaire : 2- verifier le mot de passe 
@app.route("/formulaire/inscription/mdp", methods=['POST'])
def mot_de_passe_formulaire_inscription():
    session['mdp'] = request.form['pwd']
    return render_template("SignUP.html", value=2)
    

#---------------------------------------------------------------------
                       #page formulaire : 3- info manquente 
@app.route("/formulaire/inscription/info", methods=['POST'])
def completer_inscription():
    try:
        if check_email(session['email'])==True:
            return render_template('SignUP.html', value=5)
    except:
        pass
    try:
        session['nom'] = request.form['nom']
        session['prenom'] = request.form['prenom']
        session['tel'] = request.form['tel']
        try:
            code = int(requete(connection(), "select max(idcli) from Client;")[0][0])+1
        except:
            code = 1
        SQL = f'''insert into client (IdCli ,NomCli, PrenomCli, telCli, mailCli, MotDePasse) values ('{code}', '{session['nom']}', '{session['prenom']}', '{session['tel']}', '{session['email']}', '{session['mdp']}')'''
        insert = insert_row_normal(connection(), SQL)
        if insert[0] == True:
            return render_template('SignUP.html', value=3, nom=session['nom'], prenom=session['prenom'], mail=session['email'])
        else:
            return render_template('SignUP.html', value=4)
    except:
        return render_template('SignUP.html', value=4) 
    
@app.route("/formulaire/inscription/login")
def connection_apres_inscription():
    return render_template('SignUP.html', value=5)
    
#---------------------------------------------------------------------------------------------------
                    #Fonction metadata pour le noms des colonnes

def description_metadata(connection, query:str):
    cursor = connection.cursor()
    cursor.execute(query)
    description = cursor.description
    return description

#------------------------------------------------------------------------------------------------
                    #Fonction Page Graphique 1     
               
@app.route('/comparaison', methods=['GET', 'POST'])
def Graphique():
    
    mail=""
    if "mail" in session:
        connecter = True
        mail = session["mail"]
    else: 
        connecter = False
    
        if request.method == 'POST':
            session["verif"] = request.form['identifiant']
            session["verifmdp"] = request.form['password']
        
            return redirect(url_for ('login'))
    
    liste = requete(connection(), '''SELECT nomP, temperaturemoy from Evolution ORDER BY temperaturemoy ASC ''')  
    Pays = []
    Temp = []
    for element in liste:
        Temp.append(element[0])
        Pays.append(element[1])
    
    fig, ax = plt.subplots(figsize=(12,11)) 
    
    plt.barh( Temp, Pays,  color=['#1533AC', '#1533AC', '#1533AC', '#1533AC', '#1533AC','#1533AC', '#1da2d8', '#1da2d8', '#1da2d8', '#def3f6','#def3f6', '#def3f6', '#def3f6', '#def3f6','#def3f6','#ffdc73', '#ffdc73', '#ffdc73', '#ffdc73', '#ffdc73','#ffbf00', '#ffbf00', '#ffbf00', '#ffbf00', '#ffbf00','#ffa500', '#ffa500', '#ffa500', '#ff5252', '#ff5252', '#ff5252'])
    
    arr_froid = mpimg.imread('static/images/froid.png')
    imagebox = OffsetImage(arr_froid, zoom=0.2)
    ab = AnnotationBbox(imagebox, (12.5, 7))
    ax.add_artist(ab)
    
    arr_chaud = mpimg.imread('static/images/soleil.png')
    imagebox = OffsetImage(arr_chaud, zoom=0.1)
    ab = AnnotationBbox(imagebox, (18,23))
    ax.add_artist(ab)
    
    ax.set_title("Température moyenne à l'année par pays") 
    plt.yticks(Temp)
    
    for index, value in enumerate(Pays):
        plt.text(value+0.25, index-0.20, str(value))
    plt.xlabel("Température")
 
    
    plt.savefig("static/images/temperatureF.png") 
    
    #--------------------------------------------------------------
    
    listet = requete(connection(), '''SELECT nomp,prixnuithotel,indicerestauration FROM Evolution''')  
    PaysBis = []
    Pnuit = []
    coutVie = []
    for element in listet:
        PaysBis.append(element[0])
        Pnuit.append(element[1])
        coutVie.append(element[2])
        
    fig, ax = plt.subplots(figsize=(12,10)) 
    ax.scatter(coutVie, Pnuit)  
    ax.set_xlim(left=20)
    ax.set_ylim(bottom=20)
    ax.set_title("Logement et Restauration  : les pays les plus et les moins chers pour voyager") 
    
    for i, txt in enumerate(PaysBis):
        if txt != "France" and txt != "Pays-Bas":
            ax.annotate(txt, (coutVie[i], Pnuit[i]))
    plt.text(68.1,68.5,"France")
    plt.text(68.6,66.7,"Pays-Bas")
    
    x=np.arange(1,120) 
    y = 130-x

    plt.fill_between(x,y,color='green',alpha=0.5)   
    plt.fill_between(x,y,np.max(y),color='#cc0000',alpha=0.5)   

    
    plt.text(61, 40, 'Pays les moins chers', fontsize = 14, bbox = dict(facecolor = 'green', alpha = 0.5))
    plt.text(88, 60, 'Pays les plus chers', fontsize = 14, bbox = dict(facecolor = '#cc0000', alpha = 0.5))
    
    plt.xlabel("Indice du côut de la vie")
    plt.ylabel("Indice des tarifs de logement")
    
    
    plt.savefig("static/images/budget.png")
    
    #--------------------------------------------------
    
    listeS = requete(connection(), '''select nomp, indicesecu from Evolution order by indicesecu DESC LIMIT 10''')  
    listeFinale = []
    for element in listeS:
        x = list(element)
        listeFinale.append(x)
    for element in listeFinale:
        element.append(listeFinale.index(element)+1)
        
    listeFr = requete(connection(), '''select nomp, indicesecu from Evolution where nomp = "France" ''')
    
    #-------------------------------------------------
    
    PaysBad = requete(connection(), '''select nomp from Evolution''')  
    PaysOK = []
    for element in PaysBad:
        for donnee in element:
            PaysOK.append(str(donnee))
            
    if request.method == 'POST':
        session['PaysInfos'] = str(request.form['PaysInfos'])
        return redirect(url_for ('InfosPaysChoisi'))
         
    return render_template('comparaison.html', plot="static/images/temperatureF.png", plot2 ="static/images/budget.png", listeFinale = listeFinale, listeFr=listeFr, PaysOK = PaysOK ,connecter=connecter, mail=mail)

@app.route('/InfosPaysChoisi', methods=['GET', 'POST']) 
def InfosPaysChoisi ():
    
    mail=""
    if "mail" in session:
        connecter = True
        mail = session["mail"]
    else: 
        connecter = False
    
        if request.method == 'POST':
            session["verif"] = request.form['identifiant']
            session["verifmdp"] = request.form['password']
        
            return redirect(url_for ('login'))
    
    req = requete(connection(), f'''select * from evolution where nomp = "{session['PaysInfos']}"''')  
    
    description = description_metadata(connection(),'''SELECT * from evolution''')
    
    return render_template('InfosPaysChoisi.html', req=req, metadata=description,connecter=connecter, mail=mail)
    

@app.route("/menu", methods=['GET', 'POST']) 
def menu():
    
    mail=""
    if "mail" in session:
        connecter = True
        mail = session["mail"]
    else: 
        connecter = False
    
        if request.method == 'POST':
            session["verif"] = request.form['identifiant']
            session["verifmdp"] = request.form['password']
        
            return redirect(url_for ('login'))
    
    return render_template("menu.html", connecter=connecter, mail=mail)


@app.route("/about", methods=['GET', 'POST']) 
def about():
    
   mail=""
   if "mail" in session:
       connecter = True
       mail = session["mail"]
   else: 
       connecter = False
   
       if request.method == 'POST':
           session["verif"] = request.form['identifiant']
           session["verifmdp"] = request.form['password']
       
           return redirect(url_for ('login'))
           
   return render_template("about.html", connecter=connecter, mail=mail)


@app.route("/conditions", methods=['GET', 'POST']) 
def conditions():
    
    mail=""
    if "mail" in session:
        connecter = True
        mail = session["mail"]
    else: 
        connecter = False 
    
        if request.method == 'POST':
            session["verif"] = request.form['identifiant']
            session["verifmdp"] = request.form['password']
        
            return redirect(url_for ('login'))
           
    return render_template("conditions.html", connecter=connecter, mail=mail)


def requeteSansRetour(connection,query,data):
    cursor = connection.cursor
    try:
        cursor.executemany(query,data)
        connection.commit()
        succes = True
    except sqlite3.OperationalError as op:
        print(f"SQL error {op} occured")
        print(query)
        succes = False 
    except sqlite3.Error as e:
        print(f"The Error {e} occured")
        print(traceback.print_exc())
        succes = False 
        
    return succes    


@app.route("/book", methods=['GET', 'POST'])
def book():
    
   mail=""
   if "mail" in session:
       connecter = True
       mail = session["mail"]
   else: 
       connecter = False
   
       if request.method == 'POST':
           session["verif"] = request.form['identifiant']
           session["verifmdp"] = request.form['password']
       
           return redirect(url_for ('login'))
   
    
   listePays = requete(connection(), '''SELECT nomP from Evolution ''') 
    
   listePaysOK = []  
   for elem in listePays:
       for donnee in elem:
            listePaysOK.append(donnee)
    
   if request.method == 'POST':
            session['nb'] = request.form['nb']
            session['datedebut'] = request.form['datedebut']
            session['datefin'] = request.form['datefin']
            session['choix'] = request.form['choix_base']
            session['choixcircuit'] = request.form['choix_circuit']
            session['pays1'] = str(request.form['pays1'])
            session['durée1'] = request.form['durée1']
            session['pays2'] = str(request.form['pays2'])
            session['durée2'] = request.form['durée2']
            session['choixExistant'] = request.form['choixExistant']
            
            print(session['nb'])
            print(session['datedebut'] )
            print(type(session['datefin']))
            print(session['choix'] )
            print(session['choixcircuit'] )
            print(session['pays1'] )
            print(session['durée1'] )
            print(session['pays2'] )
            print(session['durée2'] )
            print(session['choixExistant'] )
                                                        
            return redirect(url_for ('Confirmation'))
    
   return render_template("book.html", listePaysOK=listePaysOK , connecter=connecter, mail=mail)

@app.route("/Confirmation", methods=['GET', 'POST'])
def Confirmation():
    
    mail = session["mail"]
    maximum = requete(CreateConnexion(),  '''select Id_Dep from Deplacement''')
    maximumR = requete(CreateConnexion(), '''select max(NumResa) from Reservation''')
    idcli = requete(CreateConnexion(), f'''SELECT IdCli from CLIENT WHERE mailCli = '{mail}' ''')
    
    if session['choix'] == "pays":
     
        liste = []  
        for elem in maximum:
            for donnee in elem:
                 liste.append(donnee)
        code = liste[-1]
        
        connection = sqlite3.connect("db/GoTrip.db")
        
        query2 = ''' 
           INSERT INTO Deplacement (Id_Dep,nomp_dep,nomp_arr,date_depart,DureeSurPlace) VALUES (?,?,?,?,?) 
           '''
        depla_tuple = [(code+1,"France",session['pays1'],session['datedebut'],session['durée1'])]
        
        connection.executemany(query2, depla_tuple)
        connection.commit()
        
        date = datetime.date.today()
        
        connection = sqlite3.connect("db/GoTrip.db")
        
        listeR = []  
        for elem in maximumR:
            for donnee in elem:
                 listeR.append(donnee)
        codeR = listeR[0]
        

        listeID = []  
        for elem in idcli:
            for donnee in elem:
                 listeID.append(donnee)
        codeID = listeID[0]

        query3 = ''' 
           INSERT INTO Reservation (NumResa,IdCli,DateResa, type_circuit) VALUES (?,?,?,?) 
           '''
        resa_tuple = [(codeR+1,codeID,date,session['choix'])]
        
        connection.executemany(query3, resa_tuple)
        connection.commit()
        
        connection = sqlite3.connect("db/GoTrip.db")
        
        query = ''' 
           INSERT INTO Comporter VALUES (?,?) 
           '''   
        comporter_tuple = [(codeR+1,code+1)]
        connection.executemany(query, comporter_tuple)
        connection.commit()

    else:
        if session['choixcircuit'] == "libre":
            
            chiffre = int(session['durée1'])
            
            date_debut = str(session['datedebut'])
            date_obj = datetime.date.fromisoformat(date_debut)
            end_date = date_obj + timedelta(days=chiffre)
            print(end_date)
            
            liste = []  
            for elem in maximum:
                for donnee in elem:
                     liste.append(donnee)
            code = liste[-1]
            
            listeR = []  
            for elem in maximumR:
                for donnee in elem:
                     listeR.append(donnee)
            codeR = listeR[0]
            

            listeID = []  
            for elem in idcli:
                for donnee in elem:
                     listeID.append(donnee)
            codeID = listeID[0]
            
            connection = sqlite3.connect("db/GoTrip.db")
        
            query2 = ''' 
               INSERT INTO Deplacement (Id_Dep, nomp_dep,nomp_arr,date_depart,DureeSurPlace) VALUES (?,?,?,?,?) 
               '''
            circuit_tuple = [(code+1,"France",session['pays1'],session['datedebut'],session['durée1']),(code+2,session['pays1'],session['pays2'],end_date,session['durée2'])]
            
            connection.executemany(query2, circuit_tuple)
            connection.commit()
            
            date = datetime.date.today()
            
            connection = sqlite3.connect("db/GoTrip.db")

            query3 = ''' 
               INSERT INTO Reservation (NumResa, IdCli,DateResa, type_circuit) VALUES (?,?,?,?) 
               '''
            resa_tuple = [(codeR+1,codeID,date,session['choixcircuit'])]
            
            connection.executemany(query3, resa_tuple)
            connection.commit()
            
            connection = sqlite3.connect("db/GoTrip.db")

            query = ''' 
               INSERT INTO Comporter VALUES (?,?) 
               '''   
            comporter_tuple = [(codeR+1,code+1),(codeR+1,code+2)]
            connection.executemany(query, comporter_tuple)
            connection.commit()
            
        else:
            
            liste = []  
            for elem in maximum:
                for donnee in elem:
                     liste.append(donnee)
            code = liste[-1]
            
            listeR = []  
            for elem in maximumR:
                for donnee in elem:
                     listeR.append(donnee)
            codeR = listeR[0]
            

            listeID = []  
            for elem in idcli:
                for donnee in elem:
                     listeID.append(donnee)
            codeID = listeID[0]
            
            date = datetime.date.today()
            
            connection = sqlite3.connect("db/GoTrip.db")

            query3 = ''' 
               INSERT INTO Reservation (NumResa, IdCli,DateResa, type_circuit) VALUES (?,?,?,?) 
               '''
            resa_tuple = [(codeR+1,codeID,date,session['choixcircuit'])]
            
            connection.executemany(query3,resa_tuple)
            connection.commit()
            
            date_debut = str(session['datedebut'])
            date_fin = str(session['datefin'])
            
            date_1 = datetime.date.fromisoformat(date_debut)
            date_2 = datetime.date.fromisoformat(date_fin)
            
            difference = (date_2 - date_1).days
            
            nbjours = random.randrange(difference)
            date_aleatoire = date_1 + timedelta(days=nbjours)

            
            connection = sqlite3.connect("db/GoTrip.db")
            
            query2 = ''' 
               INSERT INTO Deplacement (Id_Dep,nomp_dep,nomp_arr,date_depart,DureeSurPlace) VALUES (?,?,?,?,?) 
               '''
              
            if session['choixExistant'] == "scan":
                
                circuit_tuple = [(code+1, "France","Norvège",session['datedebut'],nbjours),(code+2,"Novège","Finlande",date_aleatoire,(difference-nbjours))]
                
                connection.executemany(query2, circuit_tuple)
                connection.commit()
                
                connection = sqlite3.connect("db/GoTrip.db")

                query = ''' 
                   INSERT INTO Comporter VALUES (?,?) 
                   '''   
                comporter_tuple = [(codeR+1,code+1),(codeR+1,code+2)]
                connection.executemany(query, comporter_tuple)
                connection.commit()
                
            elif session['choixExistant'] == "benelux":
                
                circuit_tuple = [(code+1,"France","Belgique",session['datedebut'],nbjours),(code+2,"Belgique","Pays-Bas",date_aleatoire,(difference-nbjours))]
                
                connection.executemany(query2, circuit_tuple)
                connection.commit()
                
                connection = sqlite3.connect("db/GoTrip.db")
                
                query = ''' 
                   INSERT INTO Comporter VALUES (?,?) 
                   '''   
                comporter_tuple = [(codeR+1,code+1),(codeR+1,code+2)]
                connection.executemany(query, comporter_tuple)
                connection.commit()
            
            elif session['choixExistant'] == "ibere":
                
                circuit_tuple = [(code+1,"France","Espagne",session['datedebut'],nbjours),(code+2,"Espagne","Portugal",date_aleatoire,(difference-nbjours))]
                
                connection.executemany(query2, circuit_tuple)
                connection.commit()
                
                connection = sqlite3.connect("db/GoTrip.db")
                
                query = ''' 
                   INSERT INTO Comporter VALUES (?,?) 
                   '''   
                comporter_tuple = [(codeR+1,code+1),(codeR+1,code+2)]
                connection.executemany(query, comporter_tuple)
                connection.commit()
                
            elif session['choixExistant'] == "baltes":
                
                circuit_tuple = [(code+1,"France","Lituanie",session['datedebut'],nbjours),(code+2,"Lituanie","Lettonie",date_aleatoire,(difference-nbjours))]
                
                connection.executemany(query2, circuit_tuple)
                connection.commit()
                
                connection = sqlite3.connect("db/GoTrip.db")

                query = ''' 
                   INSERT INTO Comporter VALUES (?,?) 
                   '''   
                comporter_tuple = [(codeR+1,code+1),(codeR+1,code+2)]
                connection.executemany(query, comporter_tuple)
                connection.commit()
                
            elif session['choixExistant'] == "itaslo":
                
                circuit_tuple = [(code+1,"France","Croatie",session['datedebut'],nbjours),(code+2,"Croatie","Slovénie",date_aleatoire,(difference-nbjours))]
                
                connection.executemany(query2, circuit_tuple)
                connection.commit()
                
                connection = sqlite3.connect("db/GoTrip.db")

                query = ''' 
                   INSERT INTO Comporter VALUES (?,?) 
                   '''   
                comporter_tuple = [(codeR+1,code+1),(codeR+1,code+2)]
                connection.executemany(query, comporter_tuple)
                connection.commit()
                
            else:
            
                circuit_tuple = [(code+1,"France","Pologne",session['datedebut'],nbjours),(code+2,"Pologne","Slovaquie",date_aleatoire,(difference-nbjours))]
                
                connection.executemany(query2, circuit_tuple)
                connection.commit()
                
                connection = sqlite3.connect("db/GoTrip.db")
                
                query = ''' 
                   INSERT INTO Comporter VALUES (?,?) 
                   '''   
                comporter_tuple = [(codeR+1,code+1),(codeR+1,code+2)]
                connection.executemany(query, comporter_tuple)
                connection.commit()
    
    
    return render_template("Confirmation.html", mail=mail)


        




idcli = requete(CreateConnexion(), '''SELECT IdCli from CLIENT WHERE mailCli = '{session["mail"]}' ''')







