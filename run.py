from app import create_app
import webbrowser

app = create_app('config.Config')

if __name__ == '__main__':
    print("Launching web ui in browser")
    webbrowser.open('http://localhost:5000')
    app.run()