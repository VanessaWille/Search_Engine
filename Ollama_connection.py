import requests
import json
import time

class OllamaConnection:
    def __init__(self, model_name, ollama_host, max_tokens=50, stream=False):
        # checks if ollama_host ends in /
        if ollama_host[-1] != "/":
            ollama_host += "/"  # add / to the end of the host

        self.model_name = model_name
        self.ollama_host = ollama_host
        self.max_tokens = max_tokens
        self.stream = stream
        self.headers = {
            "Content-Type": "application/json"
        }

        assert requests.get(ollama_host).text == "Ollama is running"  # check if the server is running

        self.url = ollama_host + "api/generate"

    def ask_the_llm(self, prompt, show_time=False):
        data = {
            "model": self.model_name,
            "prompt": prompt,
            "max_tokens": self.max_tokens,
            "stream": self.stream
        }

        start = time.time()
        response = requests.post(self.url, headers=self.headers, data=json.dumps(data))
        end = time.time()
        time_taken = end - start
        if show_time:
            print("Time taken: ", round(time_taken, 2), "seconds")

        if response.status_code == 200:
            response_text = response.text
            data = json.loads(response_text)
            actual_response = data["response"]
            return actual_response
        else:
            return "Error in response: ", response.status_code, response.text