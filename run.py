import os
from app import create_app

app = create_app('config.Config')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Use Render's assigned PORT, default to 5000
    print(f"Starting server on port {port}...")
    app.run(host="0.0.0.0", port=port)
