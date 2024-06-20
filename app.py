import pyvespa_functions as pf
# from old_code.build_dataset import make_food_dataset
import pandas as pd
from vespa.deployment import VespaDocker
from vespa.io import VespaQueryResponse
from vespa.application import Vespa

class FindMyPasta:
    def __init__(self):
        self.package = pf.create_package(app_type="semantic-search")
        self.vespa_docker = VespaDocker()
        self.vespa_app = None
        self._df = None
        self.feeder = None

    def try_local_vespa_connection(self):
        if pf.is_application_running(url="http://localhost", port=8080):
            self.vespa_app = Vespa(url="http://localhost", port=8080)
            self.feeder = pf.VespaFeeder(self.vespa_app)
            return True
        return False

    
    def deploy_vespa(self):
        sucess = self.try_local_vespa_connection()
        
        if not sucess:
            self.vespa_app = self.vespa_docker.deploy(application_package=self.package)
            self.feeder = pf.VespaFeeder(self.vespa_app)

    def verify_loaded_data(self):
        """
        Verify if the data is loaded in Vespa

        Returns:
        {
            "status": "Data loaded" | "Data not loaded", # Status of the data
            "documents": 0, # Number of documents loaded
            "obs": [str, ...] # List of observations if any
        }
        """
        status = {"status": "Data not loaded", "documents": 0, "obs": []}
        try:
            documents = self.vespa_app.query(yql='select * from sources * where true')
            status["documents"] = documents.number_documents_indexed
            status["status"] = "Data loaded"
            return status
        except Exception as e:
            status["obs"].append(str(e))
            return status
        
    
    def search_semantic(self, query):
        results = []
        with self.vespa_app.syncio(connections=1) as session:
            response:VespaQueryResponse = session.query(
                yql="select * from sources * where ({targetHits:1000}nearestNeighbor(embedding,q)) limit 5", 
                query=query, 
                ranking="semantic", 
                body = {
                "input.query(q)": f"embed({query})"
                }
            )
            assert(response.is_successful())

            for hit in response.hits:
                record = {}
                record["relevance"] = hit["relevance"]
                for field in ['id', 'title', 'body']:
                    record[field] = hit['fields'][field]

                # replace all the \n with <br> for better visualization
                record['body'] = record['body'].replace('\n', '<br>')

                results.append(record)

        return results
    
    @property
    def df(self):
        if self._df is None:
            self._df = pd.read_csv('./input/food_dataset.csv')
        return self._df
    

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

pasta_app = FindMyPasta()

app = Flask(__name__, static_folder='static', static_url_path='/static', template_folder='templates')
CORS(app)  # Allow CORS for all routes

@app.route('/')
def index():
    return send_file('templates/index.html')

@app.route('/chat', methods=['POST'])
def chat():
    # Get the query from the request
    query = request.form['query']

    # Perform the search
    results = pasta_app.search_semantic(query)

    # Prepare the response
    response = {
        'query': query,
        'results': results
    }

    return jsonify(response)

@app.route('/deploy', methods=['POST'])
def deploy():
    pasta_app.deploy_vespa()
    status = pasta_app.verify_loaded_data()
    return jsonify(status)

@app.route('/load_data', methods=['POST'])
def load_data():
    # get the number of files to load
    num_files = int(request.form['num_files'])
    
    df = pasta_app.df[:num_files]

    # Load the data
    pasta_app.feeder.feed(df)

    # Verify if the data is loaded
    status = pasta_app.verify_loaded_data()
    return jsonify(status)
    

if __name__ == '__main__':
    app.run(debug=True)
