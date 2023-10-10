import re
from flask import Flask,render_template,request,url_for,session,redirect
from flask_mysqldb import MySQL
import MySQLdb.cursors
from mapbox import Maps,Geocoder, StaticStyle
from mapbox.services.base import Service
from mapbox.services.static import Static
from flask import Flask, render_template, request, url_for, redirect, flash
from flask_mysqldb import MySQL
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import csv
from datetime import datetime
import os
from werkzeug.utils import secure_filename

app=Flask(__name__)

app.secret_key="password"

mysql=MySQL(app)
app.config["MYSQL_HOST"]="127.0.0.1"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]="password"
app.config["MYSQL_DB"]="project"

bool=True


@app.route('/')
def home():
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('index.html', username=session['username'],userid=session["id"],bool=bool)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


@app.route('/admin')
def adminhome():
    if 'loggedin2' in session:
        # User is loggedin show them the home page
        return render_template('admin.html', username=session['username'],userid=session["id"],bool=bool)
    # User is not loggedin redirect to login page
    return redirect(url_for('admin_login'))


@app.route('/register', methods=['POST','GET'])
def register():
    print("akashregister")
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
                # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute('INSERT INTO accounts VALUES (NULL,%s, %s, %s,NULL)', (username, password, email,))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        query="SELECT * FROM accounts WHERE username = %s AND password = %s AND adm = null"
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            global bool 
            bool = False
            return redirect(url_for('home'))
            
        else:
            print("no user '%s' ",username)
            msg = 'Incorrect username/password!'

    return render_template('login.html', msg=msg)



@app.route('/admin_login',methods=['GET','POST'])
def admin_login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username1 = request.form['username']
        password1 = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM accounts WHERE username = %s AND password = %s AND adm = 'yes'", (username1, password1))
        print(username1,password1)
        global account2
        account2 = cursor.fetchone()
        print(account2)
        if account2:
            session['loggedin2'] = True
            session['id'] = account2['id']
            session['username'] = account2['username']
            global bool
            bool = True
            return redirect(url_for('adminhome'))
        else:
            msg = 'Incorrect username/password!'
    return render_template('admin_login.html', msg=msg)


@app.route('/logout')
def logout():
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   return redirect(url_for('login'))


#service notification
def notify():
    date = datetime.today().strftime('%Y-%m-%d')
    f = open('static/bought_cars.csv','r', newline='')
    csv_r = csv.reader(f)
    for rec in csv_r:
        if rec[0] == 'Car_ID':
            continue
        if rec[2] == date:
            notif = Mail(from_email='rahulsiv2108@gmail.com',
                         to_emails=rec[3],
                         subject='Time to take your car to the service centre',
                         html_content= "<p>Hi! It's been 6 months since you have had your car checked. Ensure that you take your car to the nearest showroom for better performance! Happy driving!</p>"
                        )
            sg_key = "#" #supposed to have the sendgrid api key
            try:
                mail = SendGridAPIClient(sg_key)
                mail.send(notif)
            except Exception as e:
                print(e)
    f.close()

#home route
@app.route('/buyers', methods = ['GET', 'POST'])
def buyer():
    notify()
    if request.method == 'POST':
        car = request.form
        carType = car['search']
        cursor = mysql.connection.cursor()
        cursor.execute('select car_id, Car_brand_name, car_model_name from seller_tb where car_type= % s;', (carType,))
        data = cursor.fetchall()
        return render_template('buyer.html', data=data,bool=bool)
    cursor = mysql.connection.cursor()
    cursor.execute('select car_id, Car_brand_name, car_model_name from Seller_tb;')
    data = cursor.fetchall()
    return render_template('buyer.html', data=data,bool=bool)

#more info route
@app.route('/buyers/more')
def info():
    file = open('info.txt', 'r')
    text = file.readlines()
    file.close()
    return render_template('info.html', text=text,bool=bool)

#car route
@app.route('/buyers/<car_id>')
def car(car_id):
    cursor = mysql.connection.cursor()
    cursor.execute('select * from seller_tb where car_id= % s;', (car_id,))
    info = cursor.fetchall()
    return render_template('car.html', info=info,bool=bool)

#automated e-mail route
@app.route('/buyers/<car_id>/mail')
def send(car_id):
    cursor = mysql.connection.cursor()
    cursor.execute('select seller_email from seller_tb where car_id= % s;', (car_id))
    data = cursor.fetchone()
    cursor.execute('select email from accounts where id = % s ;', (session["id"],))
    email = cursor.fetchone()[0]
    msg = Mail(
        from_email='rahulsiv2108@gmail.com',
        to_emails=email,
        subject='Seller contact info',
        html_content=f'<div>Seller contact info has been sent!</div><p>{data}</p>')
    sg_key = "#" #supposed to contain the sendgrid api key
    try:
        sg = SendGridAPIClient(sg_key)
        res = sg.send(msg)
    except Exception as e:
        print(e)
    return redirect(f'/buyers/{car_id}')

#test drive route
@app.route('/buyers/test-drive', methods= ['GET', 'POST']) 
def test_drive():
    cursor = mysql.connection.cursor()
    cur_date = datetime.today().strftime('%Y-%m-%d')
    cur_date_str = cur_date.replace('-', '')
    cursor.execute('select date,car_id from testdrive')
    slots = cursor.fetchall()
    for i in slots:
        slot_date = str(i[0]).replace('-', '')
        if int(slot_date) < int(cur_date_str):
            cursor.execute('''update testdrive set date = curdate() where car_id = % s;''', (i[1],))
            mysql.connection.commit()
    if request.method == 'POST':
        form = request.form
        name = form['name']
        cursor.execute('select * from testdrive where name = % s;', (name,))
        elements = cursor.fetchall()
        return render_template('test_drive.html', elements=elements,bool=bool)
    cursor.execute('select * from testdrive;')
    elements = cursor.fetchall()
    return render_template('test_drive.html', elements=elements,bool=bool)

#test drive this car route
@app.route('/buyers/test-drive/<car_id>')
def td_car(car_id):
    cursor = mysql.connection.cursor()
    cursor.execute('select * from testdrive t,seller_tb b where t.Car_ID = % s and t.Car_ID = b.Car_ID;', (car_id,))
    slot_data = cursor.fetchall()
    return render_template('tdcar.html', slot_data=slot_data,bool=bool)

#test drive confirmation
@app.route('/buyers/test-drive/<car_id>/book')
def confirm(car_id):
    cursor = mysql.connection.cursor()
    cursor.execute('select seller_email from seller_tb where Car_ID = % s;', (car_id,))
    email = cursor.fetchone()
    td_update = Mail(from_email='rahulsiv2108@gmail.com',
                     to_emails=email[0],
                     subject= 'Test drive slot update',
                     html_content= '<p>A prospective buyer has booked a slot to test drive your car.</p>'
                    )
    sg_key = "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"
    try:
        sg = SendGridAPIClient(sg_key)
        sg.send(td_update)
    except Exception as e:
        print(e)
    return redirect(f'/test-drive/{car_id}')

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg']
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1] in ALLOWED_EXTENSIONS

@app.route('/register_car',methods=["GET","POST"])
def getval():
    if request.method =="POST":
        SN=request.form["SN"]
        CMN = request.form['CMN']
        CBN = request.form['CBN']
        SE=request.form["email"]
        TD=request.form["TD"]
        CT=request.form["CT"]
        PR=request.form["PR"]
        date = datetime.today().strftime('%Y-%m-%d')
        cur=mysql.connection.cursor()
        cur.execute("INSERT INTO seller_tb(Seller_Name,Car_Model_Name,Car_Brand_Name ,Seller_email ,test_drive ,Car_type ,Price_range,id) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",(SN,CMN,CBN,SE,TD,CT,PR,session['id']))
        mysql.connection.commit()
        cur.execute("select test_drive,car_id from seller_tb where seller_name= %s;",(SN,))
        datatd=cur.fetchone()[0]
        id=1
        if datatd=="yes":
            cur.execute("INSERT INTO testdrive values(%s,%s,%s)",(id,date,SN))
            mysql.connection.commit()
        cur.close()
        # file = request.files['file']
        # if file and ALLOWED_EXTENSIONS(file.filename):
        #     filename = secure_filename(file.filename)
        #     filepath=os.path.join(UPLOAD_FOLDER, filename)
        #     file.save(filepath)
    return render_template("regis_car.html",bool=bool)



@app.route('/registered_cars')
def alloffers():
    cur=mysql.connection.cursor()
    query="SELECT car_id,Seller_Name,Car_Model_Name,Car_Brand_Name ,Seller_email ,test_drive ,Car_type ,Price_range FROM seller_tb WHERE id=%s"
    cur.execute(query,(session["id"],))
    l=[]
    while True:
        data=cur.fetchone()
        if data == None:
            break
        else:
            l=l+[data]
    cur.close()
    h=["seller number","seller Name","Car Model Name","Car Brand","Seller email","test drive","car type","price"]
    return render_template("registered_cars.html",l=l,h=h,bool=bool)

@app.route('/searchcar',methods=["GET","POST"])
def getvalue():
    a=[]
    h=[]
    if request.method =="POST":
        LRT= request.form['LRT']
        RCT= request.form['RCT']
        RCB= request.form['RCB']
        RPR= request.form["RPR"]
        query=''' Select * from seller_tb Where 1=1'''
        if LRT !='none':
            query=query + " and Lease_renewal_time='" +  LRT +"'"
        if RCT !='none':
            query=query + " and Car_type='" +  RCT +"'"
        if RCB !='none':
            query=query+ " and Car_Brand_Name='" + RCB +"'"
        if RPR !='none':
            query=query+ " and Price_range=" + RPR +""
        cur=mysql.connection.cursor()
        cur.execute(query)
        while True:
            data=cur.fetchone()
            if data == None :
                break
            else:
                a=a+[data]
        cur.close()
        h=["car number","Car Model Name","Car Brand Name","test drive","car type","price range","action"]
    return render_template("searchplace.html",h=h,searchval=a,bool=bool)

@app.route('/lease_car_details/<car_number>')
def lease_car_details(car_number):
    cur=mysql.connection.cursor()
    query="SELECT Seller_Name,Car_Model_Name,Car_Brand_Name ,Seller_email ,test_drive ,Car_type ,Price_range FROM seller_tb where car_id='"+car_number+"'"
    cur.execute(query)
    l=[]
    while True:
        data=cur.fetchone()
        if data == None:
            break
        else:
            l=l+[data]
    cur.close() 
    return render_template("lease_car_details.html",l=l,car_number=car_number,bool=bool)


@app.route('/lease_car',methods=["GET","POST"])
def lease():
    cur=mysql.connection.cursor()
    if request.method =="POST":
        car_number=request.form["car_number"]
        status=request.form["status"]
        email=request.form["email"]
        TD=request.form["TD"]
        N=request.form["N"]
        LRP=request.form["LRP"]
        cur=mysql.connection.cursor()
        if status=="no":
            query="UPDATE rental_table SET status = '"+status +"' WHERE car_number = 'none' and E='none' and LPR='none' and TD='none' and N='none'"
        else:
            query="UPDATE rental_table SET status = '"+status +"' WHERE car_number = '" + car_number +"' and E='"+ email +"' LPR='"+ LRP +"' TD='"+ TD +"' N='"+ N +"'"
        cur.execute(query)
        mysql.connection.commit()
        cur.close()
    return render_template("lease_car.html",bool=bool)

@app.route('/update/<car_num>',methods=["GET","POST"])
def update(car_num):
    cur=mysql.connection.cursor()
    if request.method =="POST":
        CN=car_num
        SN=request.form["SN"]
        CMN = request.form['CMN']
        CBN = request.form['CBN']
        SE=request.form["email"]
        TD=request.form["TD"]
        CT=request.form["CT"]
        PR=request.form["PR"]
        cur=mysql.connection.cursor()
        query="UPDATE seller_tb SET Seller_Name=%s,Car_Model_Name=%s,Car_Brand_Name=%s,Seller_email=%s,test_drive=%s,Car_type=%s,Price_range=%s WHERE car_id=%s ;"
        t=(SN,CMN,CBN,SE,TD,CT,PR,CN)
        cur.execute(query,t)
        mysql.connection.commit()
        cur.close()    
    return render_template("update.html",bool=bool)


@app.route('/profile/<userid>')
def profile(userid):
    cursor = mysql.connection.cursor()
    cursor.execute('select * from accounts where id = % s;', (userid,))
    user = cursor.fetchone()
    return render_template('profile.html', user=user,bool=bool)

#delete profile route
@app.route('/profile/<userid>/delete')
def profile_delete(userid):
    cursor = mysql.connection.cursor()
    cursor.execute('delete from accounts where id = % s;', (userid,))
    mysql.connection.commit()

    return redirect('/register')

if __name__=="__main__":
    app.run(debug=True)
