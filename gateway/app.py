"""
    for login, we're following:
        https://www.geeksforgeeks.org/python/login-and-registration-project-using-flask-and-mysql/

    and also the skycloak thingy, which explains how we should setup the application to use
    the keycloak.
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)