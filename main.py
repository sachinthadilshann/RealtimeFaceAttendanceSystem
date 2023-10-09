import os
import pickle
from datetime import datetime
import cvzone
import face_recognition
import numpy as np
import cv2 as cv
import firebase_admin
from firebase_admin import credentials, db, storage

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://faceattendancerealtime-38a87-default-rtdb.firebaseio.com/",
    'storageBucket': "faceattendancerealtime-38a87.appspot.com"
})

bucket = storage.bucket()

cap = cv.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

imgBackground = cv.imread('Resources/background.png')

# Importing the mode images into a list
folderModePath = 'Resources/Modes'
modePathList = os.listdir(folderModePath)
imgModeList = []
for path in modePathList:
    imgModeList.append(cv.imread(os.path.join(folderModePath, path)))

print("Loading Encode File ...")
file = open('EncodeFile.p', 'rb')
encodeListKnownWithIds = pickle.load(file)
file.close()
encodeListKnown, studentIds = encodeListKnownWithIds

modeType = 0
counter = 0
id = -1
imgStudent = None  # Initialize as None

while True:
    success, img = cap.read()

    imgS = cv.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv.cvtColor(imgS, cv.COLOR_BGR2RGB)

    faceCurFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

    imgBackground[162:162 + 480, 55:55 + 640] = img
    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

    if faceCurFrame:
        for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)

            matchIndex = np.argmin(faceDis)

            if matches[matchIndex]:
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
                imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)
                id = studentIds[matchIndex]

                if counter == 0:
                    cvzone.putTextRect(imgBackground, "Loading", (275, 400))
                    cv.imshow("Face Attendance", imgBackground)
                    cv.waitKey(1)
                    counter = 1
                    modeType = 1

        if counter != 0:

            if counter == 1:
                Info = db.reference(f'Employees/{id}').get()
                if Info is not None:
                    print(Info)

                    blob = bucket.get_blob(f'Images/{id}.png')
                    if blob is not None:
                        array = np.frombuffer(blob.download_as_string(), np.uint8)
                        imgStudent = cv.imdecode(array, cv.COLOR_BGRA2BGR)
                    else:
                        print(f"Image for ID {id} not found in storage.")

                    if 'last_attendance_time' in Info:
                        datetimeObject = datetime.strptime(Info['last_attendance_time'], "%Y-%m-%d %H:%M:%S")
                        secondsElapsed = (datetime.now() - datetimeObject).total_seconds()
                        print(secondsElapsed)

                        if secondsElapsed > 30:
                            ref = db.reference(f'Employees/{id}')
                            Info['total_attendance'] += 1
                            ref.child('total_attendance').set(Info['total_attendance'])
                            ref.child('last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        else:
                            modeType = 3
                            counter = 0
                            imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]
                    else:
                        print(f"'last_attendance_time' not found in Info for ID {id}")
                else:
                    print(f"Employee data not found for ID {id}")

            if modeType != 2:

                if 10 < counter < 20:
                    modeType = 2

                imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

                if counter <= 10:
                    cv.putText(imgBackground, str(Info['total_attendance']), (861, 125),
                                cv.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
                    cv.putText(imgBackground, str(Info['major']), (1006, 550),
                                cv.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                    cv.putText(imgBackground, str(id), (1006, 493),
                                cv.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                    cv.putText(imgBackground, str(Info['standing']), (910, 625),
                                cv.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                    cv.putText(imgBackground, str(Info['year']), (1025, 625),
                                cv.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                    cv.putText(imgBackground, str(Info['starting_year']), (1125, 625),
                                cv.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)

                    (w, h), _ = cv.getTextSize(Info['name'], cv.FONT_HERSHEY_COMPLEX, 1, 1)
                    offset = (414 - w) // 2
                    cv.putText(imgBackground, str(Info['name']), (808 + offset, 445),
                                cv.FONT_HERSHEY_COMPLEX, 1, (50, 50, 50), 1)

                    if imgStudent is not None:
                        imgBackground[175:175 + 216, 909:909 + 216] = imgStudent

                counter += 1

                if counter >= 20:
                    counter = 0
                    modeType = 0
                    Info = None  # Reset Info to None
                    imgStudent = None
                    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]
    else:
        modeType = 0
        counter = 0

    cv.imshow("Face Attendance", imgBackground)
    cv.waitKey(1)
