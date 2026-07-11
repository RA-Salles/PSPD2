from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=80) #this should be exposed in port 80!