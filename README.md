# DB-Library-System
This is a Library System Programming Project. It involves creating a database host application that interfaces with a backend SQL database implementing a Library Management System.

# How to run the app
1. Install necessary modules used in the app(listed in requirements.txt)
2. Make sure postgres of some version has been installed on your computer
3. Check if the postgres server is up and running in the background
4. Change the following lines to correctly set up the app

.env file, line 1 - change the password to yours
```
DATABASE_PASSWORD=your postgres password
```

.env file, line 2 - set DO_SETUP to true to have the program intialize the database
```
DO_SETUP=true
```

5. run the following command, this will generate a database named "library_db" and populate the database with the sample data given by the professor
```
python app.py
```

6. Change the following lines to run the app
.env file, line 2 - set DO_SETUP to true to initialize the database
```
DO_SETUP=false
```

7. Run the same command as step 5
