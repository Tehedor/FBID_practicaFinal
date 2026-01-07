import sys, os, re
import json
import iso8601
import datetime
import uuid
import threading 

from flask import Flask, render_template, request
from pymongo import MongoClient
from bson import json_util
from kafka import KafkaProducer, KafkaConsumer 
from flask_socketio import SocketIO, emit, join_room 

# Configuration details
import config
import predict_utils

# --- CONFIGURACIÓN DE ENTORNO ---
MONGO_HOST = os.environ.get('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.environ.get('MONGO_PORT', 27017))

KAFKA_HOST = os.environ.get('KAFKA_HOST', 'localhost')
KAFKA_PORT = int(os.environ.get('KAFKA_PORT', 9092))
KAFKA_BOOTSTRAP_SERVER = f"{KAFKA_HOST}:{KAFKA_PORT}"

# Topics
TOPIC_REQUEST = 'flight-delay-ml-request'
TOPIC_RESPONSE = 'flight-delay-ml-response'

# --- INICIALIZACIÓN DE LA APP ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!' 
socketio = SocketIO(app, cors_allowed_origins="*")

# Clientes
client = MongoClient(MONGO_HOST, MONGO_PORT)
producer = KafkaProducer(bootstrap_servers=[KAFKA_BOOTSTRAP_SERVER], api_version=(0,10))

from pyelasticsearch import ElasticSearch
elastic = ElasticSearch(config.ELASTIC_URL)

# --- LÓGICA DE FONDO: CONSUMIDOR DE KAFKA ---
def kafka_response_listener():
    """Escucha respuestas de Spark y las manda por WebSocket"""
    print(f"🎧 Iniciando listener de Kafka en {TOPIC_RESPONSE}...")
    # Damos tiempo a que Kafka arranque si el contenedor es muy rápido
    import time
    time.sleep(10) 
    
    try:
        consumer = KafkaConsumer(
            TOPIC_RESPONSE,
            bootstrap_servers=[KAFKA_BOOTSTRAP_SERVER],
            auto_offset_reset='latest', 
            enable_auto_commit=True,
            # group_id='flask-pyspark-group',
            group_id=f'flask-pyspark-{uuid.uuid4()}',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )

        for message in consumer:
            prediction_data = message.value
            user_uuid = prediction_data.get('UUID')
            print(f"📥 Mensaje RAW recibido de Kafka: {prediction_data}")
            if user_uuid:
                print(f"⚡ Predicción para {user_uuid}: {prediction_data.get('Prediction')}")
                socketio.emit('prediction_result', prediction_data, to=user_uuid)
    except Exception as e:
        print(f"❌ Error en listener de Kafka: {e}")

# Arrancamos el hilo de fondo
bg_thread = threading.Thread(target=kafka_response_listener)
bg_thread.daemon = True 
bg_thread.start()


# --- RUTAS EXISTENTES (NO TOCAR, SIRVEN PARA LA WEB) ---
# ... (Mantén aquí todas tus rutas de on_time_performance, total_flights, airplanes, etc.) ...
# ... Solo voy a poner las que cambian abajo ...

@app.route("/on_time_performance")
def on_time_performance():
  carrier = request.args.get('Carrier')
  flight_date = request.args.get('FlightDate')
  flight_num = request.args.get('FlightNum')
  flight = client.agile_data_science.on_time_performance.find_one({
    'Carrier': carrier, 'FlightDate': flight_date, 'FlightNum': flight_num
  })
  return render_template('flight.html', flight=flight)

@app.route("/flights/<origin>/<dest>/<flight_date>")
def list_flights(origin, dest, flight_date):
  flights = client.agile_data_science.on_time_performance.find(
    {'Origin': origin, 'Dest': dest, 'FlightDate': flight_date},
    sort = [('DepTime', 1), ('ArrTime', 1)]
  )
  flight_count = flights.count()
  return render_template('flights.html', flights=flights, flight_date=flight_date, flight_count=flight_count)

@app.route("/total_flights")
def total_flights():
  total_flights = client.agile_data_science.flights_by_month.find({}, sort = [('Year', 1), ('Month', 1)])
  return render_template('total_flights.html', total_flights=total_flights)

@app.route("/total_flights.json")
def total_flights_json():
  total_flights = client.agile_data_science.flights_by_month.find({}, sort = [('Year', 1), ('Month', 1)])
  return json_util.dumps(total_flights, ensure_ascii=False)

@app.route("/total_flights_chart")
def total_flights_chart():
  total_flights = client.agile_data_science.flights_by_month.find({}, sort = [('Year', 1), ('Month', 1)])
  return render_template('total_flights_chart.html', total_flights=total_flights)

@app.route("/airplanes")
@app.route("/airplanes/")
def search_airplanes():

  search_config = [
    {'field': 'TailNum', 'label': 'Tail Number'},
    {'field': 'Owner', 'sort_order': 0},
    {'field': 'OwnerState', 'label': 'Owner State'},
    {'field': 'Manufacturer', 'sort_order': 1},
    {'field': 'Model', 'sort_order': 2},
    {'field': 'ManufacturerYear', 'label': 'MFR Year'},
    {'field': 'SerialNumber', 'label': 'Serial Number'},
    {'field': 'EngineManufacturer', 'label': 'Engine MFR', 'sort_order': 3},
    {'field': 'EngineModel', 'label': 'Engine Model', 'sort_order': 4}
  ]

  # Pagination parameters
  start = request.args.get('start') or 0
  start = int(start)
  end = request.args.get('end') or config.AIRPLANE_RECORDS_PER_PAGE
  end = int(end)

  # Navigation path and offset setup
  nav_path = predict_utils.strip_place(request.url)
  nav_offsets = predict_utils.get_navigation_offsets(start, end, config.AIRPLANE_RECORDS_PER_PAGE)

  print("nav_path: [{}]".format(nav_path))
  print(json.dumps(nav_offsets))

  # Build the base of our elasticsearch query
  query = {
    'query': {
      'bool': {
        'must': []}
    },
    'sort': [
      {'Owner': {'order': 'asc'} },
      # {'Manufacturer': {'order': 'asc', 'ignore_unmapped' : True} },
      # {'Model': {'order': 'asc', 'ignore_unmapped': True} },
      # {'EngineManufacturer': {'order': 'asc', 'ignore_unmapped' : True} },
      # {'EngineModel': {'order': 'asc', 'ignore_unmapped': True} },
      # {'TailNum': {'order': 'asc', 'ignore_unmapped' : True} },
      '_score'
    ],
    'from': start,
    'size': config.AIRPLANE_RECORDS_PER_PAGE
  }

  arg_dict = {}
  for item in search_config:
    field = item['field']
    value = request.args.get(field)
    print(field, value)
    arg_dict[field] = value
    if value:
      query['query']['bool']['must'].append({'match': {field: value}})

  # Query elasticsearch, process to get records and count
  results = elastic.search(query)
  airplanes, airplane_count = predict_utils.process_search(results)

  # Persist search parameters in the form template
  return render_template(
    'all_airplanes.html',
    search_config=search_config,
    args=arg_dict,
    airplanes=airplanes,
    airplane_count=airplane_count,
    nav_path=nav_path,
    nav_offsets=nav_offsets,
  )

@app.route("/airplanes/chart/manufacturers.json")
def airplane_manufacturers_chart():
  mfr_chart = client.agile_data_science.airplane_manufacturer_totals.find_one()
  return json.dumps(mfr_chart)

@app.route("/airplane/<tail_number>")
@app.route("/airplane/flights/<tail_number>")
def flights_per_airplane(tail_number):
  flights = client.agile_data_science.flights_per_airplane.find_one(
    {'TailNum': tail_number}
  )
  return render_template(
    'flights_per_airplane.html',
    flights=flights,
    tail_number=tail_number
  )

@app.route("/airline/<carrier_code>")
def airline(carrier_code):
  airline_summary = client.agile_data_science.airlines.find_one(
    {'CarrierCode': carrier_code}
  )
  airline_airplanes = client.agile_data_science.airplanes_per_carrier.find_one(
    {'Carrier': carrier_code}
  )
  return render_template(
    'airlines.html',
    airline_summary=airline_summary,
    airline_airplanes=airline_airplanes,
    carrier_code=carrier_code
  )

@app.route("/")
@app.route("/airlines")
def airlines():
  airlines = client.agile_data_science.airplanes_per_carrier.find()
  return render_template('all_airlines.html', airlines=airlines)


@app.route("/flights/search")
@app.route("/flights/search/")
def search_flights():

  # Search parameters
  carrier = request.args.get('Carrier')
  flight_date = request.args.get('FlightDate')
  origin = request.args.get('Origin')
  dest = request.args.get('Dest')
  tail_number = request.args.get('TailNum')
  flight_number = request.args.get('FlightNum')

  # Pagination parameters
  start = request.args.get('start') or 0
  start = int(start)
  end = request.args.get('end') or config.RECORDS_PER_PAGE
  end = int(end)

  # Navigation path and offset setup
  nav_path = predict_utils.strip_place(request.url)
  nav_offsets = predict_utils.get_navigation_offsets(start, end, config.RECORDS_PER_PAGE)

  # Build the base of our elasticsearch query
  query = {
    'query': {
      'bool': {
        'must': []}
    },
    'sort': [
      {'FlightDate': {'order': 'asc', 'ignore_unmapped' : True} },
      {'DepTime': {'order': 'asc', 'ignore_unmapped' : True} },
      {'Carrier': {'order': 'asc', 'ignore_unmapped' : True} },
      {'FlightNum': {'order': 'asc', 'ignore_unmapped' : True} },
      '_score'
    ],
    'from': start,
    'size': config.RECORDS_PER_PAGE
  }

  # Add any search parameters present
  if carrier:
    query['query']['bool']['must'].append({'match': {'Carrier': carrier}})
  if flight_date:
    query['query']['bool']['must'].append({'match': {'FlightDate': flight_date}})
  if origin:
    query['query']['bool']['must'].append({'match': {'Origin': origin}})
  if dest:
    query['query']['bool']['must'].append({'match': {'Dest': dest}})
  if tail_number:
    query['query']['bool']['must'].append({'match': {'TailNum': tail_number}})
  if flight_number:
    query['query']['bool']['must'].append({'match': {'FlightNum': flight_number}})

  # Query elasticsearch, process to get records and count
  results = elastic.search(query)
  flights, flight_count = predict_utils.process_search(results)

  # Persist search parameters in the form template
  return render_template(
    'search.html',
    flights=flights,
    flight_date=flight_date,
    flight_count=flight_count,
    nav_path=nav_path,
    nav_offsets=nav_offsets,
    carrier=carrier,
    origin=origin,
    dest=dest,
    tail_number=tail_number,
    flight_number=flight_number
    )

@app.route("/delays")
def delays():
  return render_template('delays.html')

# --- RUTAS MODIFICADAS PARA WEBSOCKETS ---

@app.route("/flights/delays/predict/classify_realtime", methods=['POST'])
def classify_flight_delays_realtime():
  """
  Recibe el formulario, envía a Kafka y devuelve el UUID.
  YA NO ESPERA A MONGO.
  """
  api_field_type_map = {
      "DepDelay": float, "Carrier": str, "FlightDate": str,
      "Dest": str, "FlightNum": str, "Origin": str
  }
  api_form_values = {}
  for api_field_name, api_field_type in api_field_type_map.items():
    api_form_values[api_field_name] = request.form.get(api_field_name, type=api_field_type)
  
  prediction_features = {}
  for key, value in api_form_values.items():
    prediction_features[key] = value
  
  # Calculamos distancia (necesita Mongo)
  prediction_features['Distance'] = predict_utils.get_flight_distance(client, api_form_values['Origin'], api_form_values['Dest'])
  
  date_features_dict = predict_utils.get_regression_date_args(api_form_values['FlightDate'])
  for api_field_name, api_field_value in date_features_dict.items():
    prediction_features[api_field_name] = api_field_value
  
  prediction_features['Timestamp'] = predict_utils.get_current_timestamp()
  
  # Generamos UUID único para esta petición
  unique_id = str(uuid.uuid4())
  prediction_features['UUID'] = unique_id
  
  # Enviamos a Kafka (Request Topic)
  message_bytes = json.dumps(prediction_features).encode()
  producer.send(TOPIC_REQUEST, message_bytes)

  # Devolvemos OK y el ID. El cliente usará este ID para escuchar el socket.
  return json_util.dumps({"status": "OK", "id": unique_id})

@app.route("/flights/delays/predict_kafka")
def flight_delays_page_kafka():
  """Renderiza la página HTML"""
  form_config = [
    {'field': 'DepDelay', 'label': 'Departure Delay', 'value': 5},
    {'field': 'Carrier', 'value': 'AA'},
    {'field': 'FlightDate', 'label': 'Date', 'value': '2016-12-25'},
    {'field': 'Origin', 'value': 'ATL'},
    {'field': 'Dest', 'label': 'Destination', 'value': 'SFO'}
  ]
  # OJO: Aquí cargamos una plantilla nueva o modificada
  return render_template('flight_delays_predict_kafka.html', form_config=form_config)

# --- EVENTO SOCKET: JOIN ROOM ---
@socketio.on('join')
def on_join(data):
    """El JS del navegador nos manda esto para unirse a su sala privada"""
    uuid_room = data['uuid']
    join_room(uuid_room)
    print(f"🔌 Cliente conectado a sala: {uuid_room}")

# --- SHUTDOWN ---
@app.route('/shutdown')
def shutdown():
  func = request.environ.get('werkzeug.server.shutdown')
  if func is None: raise RuntimeError('Not running with the Werkzeug Server')
  func()
  return 'Server shutting down...'

if __name__ == "__main__":
    # IMPORTANTE: Usar socketio.run
    socketio.run(
      app,
      debug=True,
      host='0.0.0.0',
      port=5001,
      # allow_unsafe_werkzeug=True
    )