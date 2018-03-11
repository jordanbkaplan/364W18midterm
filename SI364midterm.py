###############################
####### SETUP (OVERALL) #######
###############################

## Import statements
# Import statements
import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, ValidationError, IntegerField# Note that you may need to import more here! Check out examples that do what you want to figure out what.
from wtforms.validators import Required,  Length # Here, too
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import Form
from flask_script import Manager, Shell
import requests
import json
## App setup code
app = Flask(__name__)
app.debug = True
app.use_reloader = True

## All app.config values


## Statements for db setup (and manager setup if using Manager)

app.config['SECRET_KEY'] = 'hard to guess string from si364'

######################################
######## HELPER FXNS (If any) ########
######################################
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://jordankaplan@localhost:5432/Midtermdb7"
## Provided:
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

manager=Manager(app)
db = SQLAlchemy(app) 

##################
##### MODELS #####
##################

class Movie(db.Model):
    __tablename__ = "movies"
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(64))
    rating=db.Column(db.Integer)
    director_id=db.Column(db.Integer, db.ForeignKey('Director.director_id'))
    plot= db.Column(db.String(64))



    def __repr__(self):
        return "{} (ID: {})".format(self.title, self.id)
class Director(db.Model):
    __tablename__ = 'Director'
    director_id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(64), unique=True)
    movies=db.relationship('Movie', backref='movie', lazy=True)

    def __repr__(self):
        return"{}(id:{})".format(self.name, self.director_id)

class User(db.Model):
    __tablename__ = 'User'
    user_id=db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(64), unique=True)

    def __repr__(self):
        return"{}(id:{})".format(self.username, self.user_id)


    def __repr__(self):
        return"{}(id:{})".format(self.name, self.director_id)

###################
###### FORMS ######
###################

class MovieNameForm(FlaskForm):
    name = StringField("Please enter the title of the movie.",validators=[Required()])
    rating = IntegerField('What would you rate the movie on a scale from 1-5', validators=[Required()])
    def validate_rating(form, field):
        if field.data >5:
            raise ValidationError("Please rate on a scale from 1-5, nothing above!")
    submit = SubmitField()
def get_or_create_director(director_name):
    # Query the director table and filter using artist_name
    # If director exists, return the director object
    # Else add a new director to the Director table
    dir1=Director.query.filter_by(name=director_name).first()
    if dir1:
        return dir1
    else: 
        dir2=Director(name=director_name)
        db.session.add(dir2)
        db.session.commit()
        print ("added director successfully")
        return dir2
def get_or_create_movie(movie_title, director, plot, rating):
    # Query the song table using song_title
    # If song exists, return the song object
    # Else add a new song to the song table.
    # NOTE : You will need artist id because that is the foreign key in the song table.
    # So if you are adding a new song, you will have to make a call to get_or_create_artist function using song_artist
    moviequery=Movie.query.filter_by(title=movie_title).first()
    if moviequery:
        return moviequery
    else:
        dir_id=Director.query.filter_by(name=director).first()
        mov1=Movie(title=movie_title, director_id=dir_id.director_id, plot=plot, rating=rating)
        db.session.add(mov1)
        db.session.commit()
        print ("added movie successfully")
        return mov1


#######################
###### VIEW FXNS ######
#######################
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@app.route('/', methods=['GET', 'POST'])
def home():
    form = MovieNameForm()
    name=None
    if request.method=="GET":


        return render_template("index.html", form=form) # User should be able to enter name after name and each one will be saved, even if it's a duplicate! Sends data with GET
    if form.validate_on_submit():
        title=form.name.data
        rating=form.rating.data
        apirequest=requests.get('http://www.omdbapi.com/?apikey=abf924e8&t='+str(title))
        dictionary=json.loads(apirequest.text)
        if "Error" in dictionary:
            flash("Please check your spelling or enter another title. That title was not found in the api :(")
            return render_template('index.html', form=form)
        else:
            director=str(dictionary['Director'])
            plot_long=str(dictionary['Plot'])
            plot=plot_long[0:63]
            movquery=Movie.query.filter_by(title=title).first()
            if movquery:
                flash("someone already rated this movie in the db")
                return render_template('index.html', form=form)
            else:
                q= get_or_create_director(director)
                b=get_or_create_movie(title,director,plot,rating)
                print (name, plot)
                flash("title successfully added to the db")
                return redirect(url_for('home'))
        ## Get the data from the form
        ## Query the Song table using the song name to check if song exists.
        #####   If song exists, reload the form and flash("You've already saved a song with that title!")
        #####   Else use get_or_create_song function to add the song to the database, and after adding redirect to the /all_songs route.
    errors = [v for v in form.errors.values()]
    if len(errors) > 0:
        flash("!!!! ERRORS IN FORM SUBMISSION - " + str(errors))
    return render_template('index.html',form=form)

@app.route('/names')
def all_names():
    q=Movie.query.all()
    num_movies=len(q)
    names = Movie.query.all()
    all_names=[(nam.title,nam.rating,str(nam.plot) +"...", Director.query.filter_by(director_id=nam.director_id).first()) for nam in names]

    return render_template('movie.html',names=all_names, num_movies=num_movies)



@app.route('/directors')
def all_directors():
    names= Director.query.all()
    return render_template('director.html',names=names)

class Usernameform(FlaskForm):
    username = StringField("Please enter your username.")
    submit = SubmitField()
def get_or_create_user(username):
    # Query the director table and filter using artist_name
    # If director exists, return the director object
    # Else add a new director to the Director table
    use=User.query.filter_by(username=username).first()
    if use:
        return use
    else: 
        use2=User(username=username)
        db.session.add(use2)
        db.session.commit()
        print ("added user successfully")
        return use2
@app.route('/user_form', methods=['GET', 'POST'])
def user_upload():
    form = Usernameform()
    username=None
    if form.validate_on_submit(): 
        return redirect(url_for('users'))
    errors = [v for v in form.errors.values()]
    return render_template('user_form.html',form=form)

@app.route('/users',  methods=['GET', 'POST'])
def users():
    form = Usernameform()
    if request.method == 'GET':
        result = request.args
        user = result.get('username')
        q= get_or_create_user(user)
        users= User.query.all()
        return render_template('users.html',names=users)





## Code to run the application...
if __name__ == '__main__':
    manager.run()
    db.create_all() # Will create any defined models when you run the application
    app.run(use_reloader=True,debug=True) # The usual


# Put the code to do so here!
# NOTE: Make sure you include the code you need to initialize the database structure when you run the application!
