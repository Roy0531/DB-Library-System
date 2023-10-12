from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import URL


def init_db(app: Flask) -> SQLAlchemy:
    import models
    db = SQLAlchemy(model_class=models.Base)
    app.config["SQLALCHEMY_DATABASE_URI"] = URL.create(
        drivername="postgresql",
        username="postgres",
        password="postgres",
        host="localhost",
        port=5432,
        database="postgres"
    )
    db.init_app(app)
    return db
