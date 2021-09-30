#importing modules
from flask import Flask, render_template, request, url_for, redirect, flash
from flask_mysqldb import MySQL
import requests
from mapbox import Geocoder, StaticStyle, Maps
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
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
    cursor = mysql.connection.cursor()
    cursor.execute('select * from bought_cars')
    data = cursor.fetchall()
    for i in data:
        if str(i[2]) == date:
            notif = Mail(from_email='rahulsiv2108@gmail.com',
                         to_emails=i[3],
                         subject='Time to take your car to the service centre',
                         html_content= "<p>Hi! It's been 6 months since you have had your car checked. Ensure that you take your car to the nearest showroom for better performance! Happy driving!</p>"
                        )
            sg_key = api['sendgrid']
            try:
                mail = SendGridAPIClient(sg_key)
                mail.send(notif)
            except Exception as e:
                print(e)

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
    return render_template('buyer.html')

#car route
@app.route('/<car_id>')
def car(car_id):
    cursor = mysql.connection.cursor()
    cursor.execute('select * from buyer where car_id= % s;', (car_id,))
    info = cursor.fetchall()
    url = 'https://apis.solarialabs.com/shine/v1/vehicle-stats/specs'
    key =  api['shine']

    res = requests.get(url, 
        headers= {'Accept': 'application/json'},
        params= {'make': 'mazda', 'model': 'cx9', 'year': '2018', 'full-data': 'false', 'apikey': key}
    )
    specs = res.text
    return render_template('car.html', info=info, specs=specs)

    # res = requests.get('https://icanhazdadjoke.com/search', 
    #     headers= {'Accept': 'application/json'},
    #     params= {'term': 'car'}
    # )
    # data = res.json()
    # jokes = data["results"]
    # return render_template('car.html', info=info, jokes=jokes)

#automated e-mail route
@app.route('/mail')
def send():
    msg = Mail(
        from_email='rahulsiv2108@gmail.com',
        to_emails='sidsiv2007@gmail.com',
        subject='Your New Car',
        html_content='<p>Congratulations! You have successfully bought a car!</p>')
    sg_key = api['sendgrid']
    try:
        sg = SendGridAPIClient(sg_key)
        res = sg.send(msg)
    except Exception as e:
        print(e)
    return render_template('mail.html')

#location
@app.route('/location', methods=['GET', 'POST'])
def location():
    if request.method == 'POST':
        token = api['mapbox']
        loc = request.form
        city = loc['city']
        geocoder = Geocoder(access_token=token)
        service = StaticStyle(access_token=token)
        maps = Maps()
        response = maps.marker(marker_name="pin-s")
        res = geocoder.forward(city)
        geo = res.geojson()['features'][0]['center']
        lat = geo[1]
        lon = geo[0]
        res = service.image(username='mapbox', style_id='streets-v9', lon = lon, lat = lat, zoom = '12')
        file = open('static/map.png', 'wb') 
        file.write(res.content)
        file.write(response.content)

        return render_template('location.html')
    return render_template('location.html')

#test drive route
@app.route('/test-drive', methods= ['GET', 'POST']) 
def test_drive():
    if request.method == 'POST':
        form = request.form
        name = form['name']
        cursor = mysql.connection.cursor()
        cursor.execute('select * from testdrive where name = % s;', (name,))
        elements = cursor.fetchall()
        return render_template('test_drive.html', elements=elements)
    return render_template('test_drive.html')

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
    cursor.execute('update testdrive set Slot = Slot + 0000/00/01 where Car_ID = % s;', (car_id,))
    mysql.connection.commit()
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
    return redirect('/test-drive')
    flash('Booking Confirmed!')

#run the program
if __name__ == '__main__':
    app.run(debug=True)
    







