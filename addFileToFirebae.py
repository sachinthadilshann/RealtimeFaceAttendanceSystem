import firebase_admin
from firebase_admin import credentials, db

cred = credentials.Certificate("serviceAccountKey.json")

firebase_admin.initialize_app(cred, {
    'databaseURL':"https://faceattendancerealtime-38a87-default-rtdb.firebaseio.com/"
})

ref = db.reference('Employees Data')

data = {
    "20231009":
        {
            "name": "Sachintha Dishan",
            "major": "xyggffffffffg",
            "starting_year": 2022,
            "total_attendance": 1,
            "standing": "G",
            "year": 2,
            "last_attendance_time": "2023-10-09 12:12:12"
        },

    "123456":
        {
            "name": "Mark Sa",
            "major": "xyggffffffffg",
            "starting_year": 2020,
            "total_attendance": 7,
            "standing": "G",
            "year": 2,
            "last_attendance_time": "2023-10-09 12:12:12"
        }

}

for key, value in data.items():
    ref.child(key).set(value)

