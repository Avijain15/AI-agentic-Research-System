import logging
import os
from flask import Flask, request, jsonify, render_template
from research_system import research_workflow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder="static", template_folder="templates")

# Ensure static directories exist
os.makedirs(os.path.join(app.root_path, 'static', 'css'), exist_ok=True)
os.makedirs(os.path.join(app.root_path, 'static', 'js'), exist_ok=True)

# Flask routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/research', methods=['POST'])
def research():
    data = request.json
    query = data.get('query', '')
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    try:
        logger.info("Starting research workflow for: %s", query)
        result = research_workflow(query)
        logger.info("Research workflow completed successfully")
        return jsonify(result)
    except Exception as e:
        logger.error("API request failed: %s", str(e), exc_info=True)
        return jsonify({"error": "Research failed", "message": str(e)}), 500

if __name__ == "__main__":
    logger.info("Starting Flask server on port 5000")
    app.run(debug=True, port=5000)