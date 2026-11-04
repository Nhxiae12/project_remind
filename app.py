from flask import Flask, jsonify, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to Project REMIND!"

@app.route('/manifest.json')
def manifest():
    return jsonify({
      "name": "Project REMIND",
      "short_name": "REMIND",
      "start_url": "/",
      "id": "/",
      "display": "standalone",
      "background_color": "#ffffff",
      "theme_color": "#1A202C",
      "description": "Real-time Educational Messaging and Information Notification Dashboard",
      "icons": [
        {
          "src": "https://via.placeholder.com/512",
          "sizes": "512x512",
          "type": "image/png"
        }
      ]
    })

@app.route('/sw.js')
def service_worker():
    sw_code = "self.addEventListener('fetch', function(event) {});"
    return sw_code, 200, {'Content-Type': 'application/javascript'}

if __name__ == '__main__':
    app.run(debug=True)
