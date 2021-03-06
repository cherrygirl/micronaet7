#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import os
import sys
import xmlrpclib
import csv
import ConfigParser

# Function: *******************************************************************
def Prepare(valore):  
    # For problems: input win output ubuntu; trim extra spaces
    #valore=valore.decode('ISO-8859-1')
    valore=valore.decode('cp1252')
    valore=valore.encode('utf-8')
    return valore.strip()

def PrepareDate(valore):
    if valore: # TODO test correct date format
       return valore
    else:
       return time.strftime("%d/%m/%Y")

def PrepareFloat(valore):
    valore=valore.strip() 
    if valore: # TODO test correct date format       
       return float(valore.replace(",","."))
    else:
       return 0.0   # for empty values

# Start main code *************************************************************
if len(sys.argv) != 2 :
   print """
         *** Syntax Error! ***
         *  Use the command with this syntax: python ./bom.py bom_file.csv 
         *********************
         """ 
   sys.exit()

cfg_file = os.path.join(os.path.expanduser("~"), "etl", "Fiam", "openerp.cfg")
   
# Set up parameters (for connection to Open ERP Database) *********************
config = ConfigParser.ConfigParser()
config.read([cfg_file]) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname = config.get('dbaccess', 'dbname')
user = config.get('dbaccess', 'user')
pwd = config.get('dbaccess', 'pwd')
server = config.get('dbaccess', 'server')
port = config.get('dbaccess', 'port')   # verify if it's necessary: getint
separator = config.get('dbaccess', 'separator') # test

# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy(
    'http://%s:%s/xmlrpc/common' % (server, port), allow_none=True)
uid = sock.login(dbname, user, pwd)
sock = xmlrpclib.ServerProxy(
    'http://%s:%s/xmlrpc/object' % (server, port), allow_none=True)

FileInput = sys.argv[1]

# Conversion for product (code - ID):
product = {}
lines = csv.reader(open('/home/thebrush/etl/Fiam/code.csv', 'rb'), delimiter=";")
for line in lines:
    if len(line): # jump empty lines
       item_id = int(Prepare(line[0]))
       default_code = Prepare(line[1])
       product[item_id] = default_code

lines = csv.reader(open(FileInput, 'rb'), delimiter=separator)

# BOM header:
conversion = {}
for line in lines:
    if len(line): # jump empty lines
       try:
           code = Prepare(line[0])
           name = Prepare(line[1])
           product_id = int(Prepare(line[2]))
           bom_code = Prepare(line[3])
           product_qty = PrepareFloat(line[4])

           if bom_code:
               continue

           if product_id in product:
               default_code = product[product_id]
               product_id = sock.execute( # search current ref
                   dbname, uid, pwd, 'product.product', 'search', [
                       ('default_code', '=', default_code),])
               if product_id:
                   product_id = product_id[0]        
               else: # create 
                   product_id = sock.execute( # search current ref
                       dbname, uid, pwd, 'product.product', 'create', {
                           'default_code': default_code,
                           'name': "Prod. %s" % default_code,
                           })
                   product[default_code] = product_id
                   
           else:
               print "codice non trovato", default_code
               continue    

           bom_id = sock.execute( # search current ref
               dbname, uid, pwd, 'mrp.bom', 'search', [
                   ('code', '=', code),
                   ])
            
           data = {
               'code': code,
               'name': name,
               'bom_id': False,
               'product_id': product_id,
               'product_qty': product_qty,
               'type': 'normal',    
               'product_uom': 1,
               'product_uos': 1,
               }

           if bom_id: # update
               sock.execute(
                   dbname, uid, pwd, 'mrp.bom', 'write', 
                   code, data)
               bom_id = bom_id[0]
           else: # create
               bom_id = sock.execute(
                   dbname, uid, pwd, 'mrp.bom', 'create', data) 
           conversion[code] = bom_id        
       except:
           print "Errore importando, record saltato", sys.exc_info()    

lines = csv.reader(open(FileInput, 'rb'), delimiter=separator)
import pdb; pdb.set_trace()
# -----------------------------------------------------------------------------
#                                Components
# -----------------------------------------------------------------------------
for line in lines:
    if len(line): # jump empty lines
       try:
           code = Prepare(line[0])
           name = Prepare(line[1])
           product_id = int(Prepare(line[2]))
           bom_code = Prepare(line[3])
           product_qty = PrepareFloat(line[4])

           if not bom_code: # only parent bom
               continue
           
           if product_id in product:
               default_code = product[product_id]
               product_id = sock.execute( # search current ref
                   dbname, uid, pwd, 'product.product', 'search', [
                       ('default_code', '=', default_code),])
               if product_id:
                   product_id = product_id[0]        
               else: # create 
                   product_id = sock.execute( # search current ref
                       dbname, uid, pwd, 'product.product', 'create', {
                           'default_code': default_code,
                           'name': "Prod. %s" % default_code,
                           })
                   product[default_code] = product_id                   
           else:
               print "codice non trovato", default_code
               continue    

           bom_id = sock.execute( # search current ref
               dbname, uid, pwd, 'mrp.bom', 'search', [
                   ('code', '=', code),
                   ])
           
           if bom_code not in conversion:
                print "errore con bom_code" % bom_code
           data = {
               'code': code,
               'name': name,
               'bom_id': conversion[bom_code],
               'product_id': product_id,
               'product_qty': product_qty,
               'type': 'normal',    
               'product_uom': 1,
               'product_uos': 1,
               }

           if bom_id: # update
               modify_id = sock.execute(
                   dbname, uid, pwd, 'mrp.bom', 'write', 
                   bom_id, data)
               bom_id = bom_id[0]
           else: # create
               bom_id = sock.execute(
                   dbname, uid, pwd, 'mrp.bom', 'create', data) 
       except:
           print "Errore importando, record saltato", sys.exc_info()    

