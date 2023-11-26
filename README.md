                                                                                                                                                                                                                                                                                                                                                           # DB-Library-System
This is a Library System Programming Project. It involves creating a database host application that interfaces with a backend SQL database implementing a Library Management System.

# How to run the app
1. Install necesarry modules used in the app(requirements list TBA)
2. Make sure postgres of some version has been installed on your compulter
3. Check if the postgres server is up and running in the background
4. Change the following lines for the correct working of the app

.env file, line 1 - change the password to yours
```
DATABASE_PASSWORD=your postgres password
```

app.py, line 279 - comments out 'app.run(debug=True)' as follows
```
if __name__ == '__main__':
    # app.run(debug=True)
    create_database()
    with app.app_context():
        db.create_all()
        insert_records()
        generate_sample_fines()
```

5. run the following command, this will generate a database called "library_db" and populate the dataabse with the sample data given by the prof
```
python app.py
```

6. Change the following lines to run the app
app.py, line 279 - comments out everything but 'app.run(debug=True)' as follows
```
if __name__ == '__main__':
    app.run(debug=True)
    # create_database()
    # with app.app_context():
    #     db.create_all()
    #     insert_records()
    #     generate_sample_fines()
```

7. Run the same command as step 5
