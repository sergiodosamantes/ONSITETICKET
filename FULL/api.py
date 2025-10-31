from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)  

DATABASE_FILE = 'servicedesk.db'

def init_db():
    """Inicializa la base de datos y crea las tablas si no existen."""
    with sqlite3.connect(DATABASE_FILE) as con:
        cur = con.cursor()
        
        # Crear tabla de tickets
        cur.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_number TEXT PRIMARY KEY,
            type TEXT,
            affected_user TEXT,
            host_name TEXT,
            short_description TEXT,
            description TEXT,
            timestamp TEXT
        )
        ''')
        
        # Crear tabla de ratings
        cur.execute('''
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rating TEXT,
            value INTEGER,
            timestamp TEXT
        )
        ''')
        con.commit()

def get_next_ticket_number(ticket_type_prefix):
    """Obtiene el siguiente número de ticket desde la base de datos."""
    with sqlite3.connect(DATABASE_FILE) as con:
        
        try:
            df = pd.read_sql_query(
                f"SELECT ticket_number FROM tickets WHERE ticket_number LIKE '{ticket_type_prefix}%' ORDER BY ticket_number DESC LIMIT 1", 
                con
            )
            if df.empty:
                return f"{ticket_type_prefix}000001"
            
            last_ticket = df['ticket_number'].iloc[0]
            last_num = int(last_ticket[len(ticket_type_prefix):])
            return f"{ticket_type_prefix}{last_num + 1:06d}"
        
        except pd.io.sql.DatabaseError:
            
            return f"{ticket_type_prefix}000001"
        except Exception as e:
            print(f"Error al obtener ticket number: {e}")
            return f"{ticket_type_prefix}000001"


#  API

@app.route('/incident', methods=['POST'])
def create_incident():
    data = request.json
    ticket_number = get_next_ticket_number('INC')
    
    new_ticket = {
        'ticket_number': ticket_number,
        'type': 'Incident',
        'affected_user': data.get('affected_user'),
        'host_name': data.get('host_name'),
        'short_description': data.get('short_description', 'On Site Ticket'),
        'description': data.get('description'),
        'timestamp': datetime.now().isoformat()
    }
    
    
    df = pd.DataFrame([new_ticket])
    
    with sqlite3.connect(DATABASE_FILE) as con:
        
        df.to_sql('tickets', con, if_exists='append', index=False)
    
    return jsonify({"ticketNumber": ticket_number}), 201

@app.route('/service-request', methods=['POST'])
def create_service_request():
    data = request.json
    ticket_number = get_next_ticket_number('REQ')

    new_ticket = {
        'ticket_number': ticket_number,
        'type': 'Service Request',
        'affected_user': data.get('request_is_for'),
        'host_name': data.get('host_name'),
        'short_description': data.get('short_description', 'On Site Ticket'),
        'description': data.get('description'),
        'timestamp': datetime.now().isoformat()
    }

    df = pd.DataFrame([new_ticket])
    
    with sqlite3.connect(DATABASE_FILE) as con:
        df.to_sql('tickets', con, if_exists='append', index=False)
    
    return jsonify({"ticketNumber": ticket_number}), 201

@app.route('/rating', methods=['POST'])
def submit_rating():
    data = request.json 
    
    
    df = pd.DataFrame([data])
    
    with sqlite3.connect(DATABASE_FILE) as con:
        df.to_sql('ratings', con, if_exists='append', index=False)
    
    print(f"Rating recibido y guardado en DB: {data}")
    return jsonify({"status": "success", "message": "Thank you for your feedback!"})

if __name__ == '__main__':
    init_db()  
    app.run(debug=True, port=5000)