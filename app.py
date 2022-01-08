#importing modules
from flask import Flask, render_template, request, url_for, redirect
from flask_mysqldb import MySQL
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import csv
import yaml
from datetime import datetime

#defining app
app = Flask(__name__)

#db config
db = yaml.load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']

#api keys file
api = yaml.load(open('api.yaml'))

mysql = MySQL(app)

#service notification
def notify():
    date = datetime.today().strftime('%Y-%m-%d')
    f = open('static/bought_cars.csv', 'r', newline='')
    csv_r = csv.reader(f)
    for rec in csv_r:
        if rec[0] == 'Car_ID':
            continue
        if rec[2] >= date:
            notif = Mail(from_email='rahulsiv2108@gmail.com',
                         to_emails=rec[3],
                         subject='Time to take your car to the service centre',
                         html_content= "<p>Hi! It's been 6 months since you have had your car checked. Ensure that you take your car to the nearest showroom for better performance! Happy driving!</p>"
                        )
            sg_key = api['sendgrid']
            try:
                mail = SendGridAPIClient(sg_key)
                mail.send(notif)
            except Exception as e:
                print(e)
    f.close()

#home route
@app.route('/', methods = ['GET', 'POST'])
def buyer():
    notify()
    if request.method == 'POST':
        car = request.form
        carType = car['search']
        cursor = mysql.connection.cursor()
        cursor.execute('select car_id, name from buyer where type= % s;', (carType,))
        data = cursor.fetchall()
        return render_template('buyer.html', data=data)
    cursor = mysql.connection.cursor()
    cursor.execute('select car_id, name from buyer;')
    data = cursor.fetchall()
    return render_template('buyer.html', data=data)

#more info route
@app.route('/more')
def info():
    file = open('info.txt', 'r')
    text = file.readlines()
    file.close()
    return render_template('info.html', text=text)

#car route
@app.route('/<car_id>')
def car(car_id):
    cursor = mysql.connection.cursor()
    cursor.execute('select * from buyer where car_id= % s;', (car_id,))
    info = cursor.fetchall()
    return render_template('car.html', info=info)

#automated e-mail route
@app.route('/<car_id>/mail')
def send(car_id):
    cursor = mysql.connection.cursor()
    cursor.execute('select seller_email from buyer where car_id= % s;', (car_id))
    data = cursor.fetchone()
    msg = Mail(
        from_email='rahulsiv2108@gmail.com',
        to_emails='sidsiv2007@gmail.com',
        subject='Seller contact info',
        html_content=f'<div>Seller contact info has been sent!</div><p>{data}</p>')
    sg_key = api['sendgrid']
    try:
        sg = SendGridAPIClient(sg_key)
        res = sg.send(msg)
    except Exception as e:
        print(e)
    return redirect(f'/{car_id}')

#test drive route
@app.route('/test-drive', methods= ['GET', 'POST']) 
def test_drive():
    cursor = mysql.connection.cursor()
    cur_date = datetime.today().strftime('%Y-%m-%d')
    cur_date_str = cur_date.replace('-', '')
    cursor.execute('select slot,car_id from testdrive')
    slots = cursor.fetchall()
    for i in slots:
        slot_date = str(i[0]).replace('-', '')
        if int(slot_date) < int(cur_date_str):
            cursor.execute('''update testdrive set slot = curdate() where car_id = % s;''', (i[1],))
            mysql.connection.commit()
    if request.method == 'POST':
        form = request.form
        name = form['name']
        cursor.execute('select * from testdrive where name = % s;', (name,))
        elements = cursor.fetchall()
        return render_template('test_drive.html', elements=elements)
    cursor.execute('select * from testdrive;')
    elements = cursor.fetchall()
    return render_template('test_drive.html', elements=elements)

#test drive this car route
@app.route('/test-drive/<car_id>')
def td_car(car_id):
    cursor = mysql.connection.cursor()
    cursor.execute('select * from testdrive t, buyer b where t.Car_ID = % s and t.Car_ID = b.Car_ID;', (car_id,))
    slot_data = cursor.fetchall()
    return render_template('tdcar.html', slot_data=slot_data)

#test drive confirmation
@app.route('/test-drive/<car_id>/book')
def confirm(car_id):
    cursor = mysql.connection.cursor()
    cursor.execute('select seller_email from buyer where Car_ID = % s;', (car_id,))
    email = cursor.fetchone()
    td_update = Mail(from_email='rahulsiv2108@gmail.com',
                     to_emails=email[0],
                     subject= 'Test drive slot update',
                     html_content= '<p>A prospective buyer has booked a slot to test drive your car.</p>'
                    )
    sg_key = api['sendgrid']
    try:
        sg = SendGridAPIClient(sg_key)
        sg.send(td_update)
    except Exception as e:
        print(e)
    return redirect(f'/test-drive/{car_id}')

#profile route
@app.route('/profile/<userid>')
def profile(userid):
    cursor = mysql.connection.cursor()
    cursor.execute('select * from accounts where id = % s;', (userid,))
    user = cursor.fetchone()
    return render_template('profile.html', user=user)

#delete profile route
@app.route('/profile/<userid>/delete')
def profile_delete(userid):
    cursor = mysql.connection.cursor()
    cursor.execute('delete from accounts where id = % s;', (userid,))
    mysql.connection.commit()
    return redirect('/')

#run the program
if __name__ == '__main__':
    app.run(debug=True)
 






