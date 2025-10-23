from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Permite la comunicación con HTML

# Base de Datos Temporal (CSV
TICKETS_FILE = 'tickets.csv'
RATINGS_FILE = 'ratings.csv'

# Crear archivos solo si no existen o los borre jeje
if not os.path.exists(TICKETS_FILE):
    pd.DataFrame(columns=[
        'ticket_number', 'type', 'affected_user', 'host_name', 
        'short_description', 'description', 'timestamp'
    ]).to_csv(TICKETS_FILE, index=False)

if not os.path.exists(RATINGS_FILE):
    # 
    # Añadi la columna para la frafica lineal
    pd.DataFrame(columns=['rating', 'value', 'timestamp']).to_csv(RATINGS_FILE, index=False)

# Lógica para Generar Tickets 
def get_next_ticket_number(ticket_type_prefix):
    if not os.path.exists(TICKETS_FILE) or os.path.getsize(TICKETS_FILE) == 0:
        return f"{ticket_type_prefix}000001"
    
    df = pd.read_csv(TICKETS_FILE)
    df_type = df[df['ticket_number'].str.startswith(ticket_type_prefix, na=False)]
    
    if df_type.empty:
        return f"{ticket_type_prefix}000001"
    
    last_ticket = df_type['ticket_number'].iloc[-1]
    last_num = int(last_ticket[len(ticket_type_prefix):])
    return f"{ticket_type_prefix}{last_num + 1:06d}"

# Endpoints de la API

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
    
    df = pd.read_csv(TICKETS_FILE)
    df = pd.concat([df, pd.DataFrame([new_ticket])], ignore_index=True)
    df.to_csv(TICKETS_FILE, index=False)
    
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

    df = pd.read_csv(TICKETS_FILE)
    df = pd.concat([df, pd.DataFrame([new_ticket])], ignore_index=True)
    df.to_csv(TICKETS_FILE, index=False)
    
    return jsonify({"ticketNumber": ticket_number}), 201

@app.route('/rating', methods=['POST'])
def submit_rating():
    data = request.json 
    
    df = pd.read_csv(RATINGS_FILE)
    df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
    df.to_csv(RATINGS_FILE, index=False)
    
    print(f"Rating recibido y guardado: {data}")
    return jsonify({"status": "success", "message": "Thank you for your feedback!"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)