"""
The flask application package.
"""

from configparser import ConfigParser
from flask import Flask,render_template,Config,session,request,abort
import base64
from functools import wraps
from flask import g,request,redirect,url_for
import itsdangerous


class LibConfig(Config):
    """
    LibServer inherits this Config class so that there is an interface to the underlying ConfigParser held by the config global handed arund from Flask.

    The purpopse here is to keep the configuration file a handle away. The admin panel completely ignores this and handles the configuration files directly.
    """
    tainted=False
    def __init__(self, *args, **kwargs):
        """
        LibConfig is essentially just a wrapper around
        a ConfigParser that reads the combined configuration
        files from the command line (typically).
        """
        self.localconf = ""
        self.baseconf = "" 
        self.parser = None
        self.tainted = False
        Config.__init__(self, *args, **kwargs)
    def get(self, section, option, default=None):
        """
        Get a configuration item from the loaded configuration
        files.

        If the section or configuration is not declared, the
        default value is returned. 
        """
        if self.parser.has_section(section) == False:
            return default
        if not self.parser.has_option(section,option):
            return default
        return self.parser.get(section, option)

    def getBool(self,section,option,default=True):
        """
        Gets a boolean value, with the default default being `True`
        """
        if not self.parser.has_section(section):
            return default
        elif not self.parser.has_option(section,option):
            return default
        else:
            return self.parser.getboolean(section,option)

    def load(self, baseconfig, localconfig):
        """
        Load a set of configuration files.
        """
        self.parser = ConfigParser()
        self.parser.read(baseconfig)
        self.parser.read(localconfig)

        self.localconf = localconfig
        self.baseconf = baseconfig

class LibFlask(Flask):
    """
    LibFlask is just a wrapper around the standard Flask class. It's used to hold the config_class type. 
    
    """
    config_class = LibConfig

    def __init__(self,*args, **kwargs):
        Flask.__init__(self, *args, **kwargs)


app = LibFlask(__name__)


def needs_authentication():
    """
    Decorator: Attach this to a route and it will require that the session has been
    previously authenticated.
    """
    def auth_chk_wrapper(f):
        # This is our decoratorated function wrapper
        @wraps(f)
        def deco(*args, **kwargs):
            # If the session does not yet have an authentication 
            if not is_authenticated():
                return redirect(sign_auth_path(request.full_path))
            else:
                return f(*args, **kwargs)
        return deco
    return auth_chk_wrapper

def is_authenticated():
    """Gets the authentication status of the current session"""
    return ('authenticated' in session) and session["authenticated"] == True

def sign_auth_path(next_path):
    """returns a URL-safe signed next_path"""
    # next_path must start with a /
    if not next_path.startswith('/'):
        abort(503)
    # sign the next_path
    notary = itsdangerous.URLSafeSerializer(app.secret_key)
    next_path_signed = notary.dumps(next_path)
    return url_for('authenticate', next=next_path_signed)

def unsign_auth_path(path_signed):
    """returns the path from a signed/sealed next_path"""
    notary = itsdangerous.URLSafeSerializer(app.secret_key)
    next_path_unsigned = notary.loads(path_signed)
    return next_path_unsigned

@app.route("/auth/",methods=["GET","POST"])
def authenticate():
    next = None
    if 'next' in request.args:
        next = request.args["next"]
    elif 'next' in request.form:
        next = request.form['next']
    if request.method == "POST":
        # Check if we're correct.
        passphrase = app.config.get("general","admin_key")
        # Check the request
        chkpass = request.form["password"]
        print("Comparing {0} == {1} ? ".format(passphrase,chkpass))
        if(passphrase == chkpass):
            print("Successful login!")
            session["authenticated"]=True
            # redirect off
            if next == None:
                print("No redirect specified. We're going home.")
                return redirect(url_for("home"))
            else:
                try:
                    return redirect(unsign_auth_path(next))
                except:
                    abort(500)
        else:
            session["authenticated"]=False
            return render_template("login.html",fail=True,next=next);
    else:
        # are we already authenticated?
        if is_authenticated():
            if next != None:
                try:
                    return redirect(unsign_auth_path(next))
                except:
                    return redirect(url_for('home'))
            return redirect(url_for("home"))
        else:
            return render_template("login.html",next=next)

@app.route("/auth/logout")
def logout():
    session["authenticated"] = False
    return redirect(url_for('home'))


@app.route('/')
def home():
    # There should be more things here. I'm not sure what to put here, but there needs to be more here.
    # Ideas are in TODO, but include a list of contents and the dixed they take up.
    # Collection lists would be nice too.
    return render_template('index.html',year=2017,title="Hello!")
