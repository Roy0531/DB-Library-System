# DB-Library-System
This is a Library System Programming Project. It involves creating a database host application that interfaces with a backend SQL database implementing a Library Management System.

# How to run the app
1. Install necesarry modules used in the app(requirements list TBA)
2. Make sure psotgres of some version has been installed on your compulter
3. Check if the postgres server is up and running in the background
4. Change the following lines for the correct working of the app

app.py, line 13, 158 - change the password 
```
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:[your password]@localhost:5432/library_db'

db_params = {
    'host': 'localhost',
    'database': 'postgres',
    'user': 'postgres',
    'password': 'your password',
    }
```

app.py, line 279, modify the comments

to create a db
```
if __name__ == '__main__':
    # app.run(debug=True)
    create_database()
    with app.app_context():
        db.create_all()
        insert_records()
        generate_sample_fines()
```

to run the app
```
if __name__ == '__main__':
    app.run(debug=True)
    # create_database()
    # with app.app_context():
    #     db.create_all()
    #     insert_records()
    #     generate_sample_fines()
```
