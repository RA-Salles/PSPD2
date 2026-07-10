"""
    for login, we're following:
        https://www.geeksforgeeks.org/python/login-and-registration-project-using-flask-and-mysql/

    
"""

from flask import *
# import auth_service_pb2 #or something like that
# import auth_service_pb2_grpc #also this one
#database configuration will come from grpc service;

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False     # Sessions expire when the browser is closed
app.config["SESSION_TYPE"] = "filesystem"     # Store session data in files

@app.route('/')
def index():
    if not session.get("user") or not session.get("token"):
        return redirect("/login")
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        pass
        #response = call_login_request(user=request.form['user'], passwd=request.form['pass'])
        # then we check response for token.
        #if response.token:
            #session["user"] = request.form['user']
            #session["token"] = response.jwt_token  
    return render_template("login.html")

def logout():
    session["user"]  = None
    session["token"] = None
    return redirect("/")


if __name__ == '__main__':
    app.run(debug=True)  # in production, this should be false