from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow CORS for all routes

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    # Get the query from the request
    query = request.form['query']

    # Perform the search
    results = search(query)

    # Prepare the response
    response = {
        'query': query,
        'results': results
    }

    return jsonify(response)

# **Vespa Configuration**


import pyvespa_functions as pf
from build_dataset import make_food_dataset
import pandas as pd
from vespa.deployment import VespaDocker

package = pf.create_package(app_type="semantic-search")

vespa_docker = VespaDocker()
vespa_app = vespa_docker.deploy(application_package=package)

documents = vespa_app.query(yql='select * from sources * where true')
if not documents.number_documents_indexed > 0:
    print(f"Warning: The dataset is empty. Please feed the vespa!!!")

from vespa.io import VespaQueryResponse

# Search function
def search(query):
    results = []
    with vespa_app.syncio(connections=1) as session:
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
            results.append(record)

    return results

if __name__ == '__main__':
    app.run(debug=True)
