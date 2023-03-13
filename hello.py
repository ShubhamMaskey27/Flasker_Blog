from flask import Flask, render_template


# Creating a flask instance
app = Flask(__name__)


# Create a route decorator
@app.route('/')
def index():
    first_name = "john"
    stuff = "this is <strong><Bold></strong> Text"
    favourite_pizza = ["pepperoni", "tandoori", "veggie"]

    return render_template('index.html', first_name=first_name, stuff=stuff, favourite_pizza=favourite_pizza)


@app.route('/user/<name>')
def user(name):
    return render_template('user.html', user_name=name)


# Custom error pages
# Invalid URl
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def page_not_found(e):
    return render_template("500.html"), 500


if __name__ == "__main__":
    app.run(debug=True)
