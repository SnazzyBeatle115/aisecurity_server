from django.shortcuts import render
from rest_framework import viewsets
from .models import Student, Transaction, StudentDateInOutStatus
from django.contrib.auth.models import User, Group
from .serializers import UserSerializer, GroupSerializer, StudentSerializer, TransactionSerializer, StudentDateInOutStatusSerializer
from django.contrib.auth import get_user_model
from datetime import datetime, timezone, date
from django.http import JsonResponse, HttpResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.forms.models import model_to_dict
import csv
from datetime import datetime, date
import os
import pytz as tz
from . import IN_MORNING_MODE

from django.shortcuts import render

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from django.core.files.storage import default_storage

from pyzbar.pyzbar import decode
import pymongo


from .workingAiClean import *
# from .barcodeScanner import *
from .dbname import *

import time, datetime, os


# Define global vars
package_id = 0
# print(int(datetime.datetime.fromtimestamp(time.time()).strftime('%M')))
prev_date = int(datetime.datetime.fromtimestamp(time.time()).strftime('%d')) - 1
current_img_dir = str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M'))
# Available times '%Y-%m-%d %H:%M:%S'

# * Load the database encodings
client = pymongo.MongoClient('mongodb://localhost:27017/')
table = client["kiosk"]
collection = table[db]

data = collection.find()

database = {}

for doc in data:
    database[doc['_id']] = doc

# database["Musk"] = getTestImage("api/Images/mrmusk3.jpg")
# database["David"] = getTestImage("api/Images/Unknown1.jpg")


"""
postImages(request) -> gets the post 
from the app on the kiosk and stores the images based on the time and date
format is "kiosk#/year-month-day_hour-min/packageid_sec_unix/" then it tries 
to run facial detection on the images
"""
@api_view(['POST'])
def postImages(request):    
    
    global package_id, prev_date, current_img_dir

    # * Attempt to store the images
    try:
        # * Get the images from the post
        data = request.data
        print("-----------------------------")
        print(request)
        print("data", data.keys(), type(data.keys()))
        print("items", str(list(data.items())))
        print("values", str(list(data.values())))
        print("image", str(next(data.items())).split("File: ")[1].split(" ")[0])

        print("has face?", "Face" in str(next(data.items())))
        print("has bar?", "Barcode" in str(next(data.items())))
        if "Barcode" in str(next(data.items())):
            for _ in range(4):
                print("BARCODE DETECTED")


        # * Block empty package
        if len(list(data.keys())) == 0:
            print("Empty Package")
            return Response("Empty Package")

        # * Block incoming package if it is too old
        if (int(list(data.keys())[0].split("-")[1]) + 7 < time.time()):
            print("Blocked", data.keys(), " Difference in times: ", time.time() - int(list(data.keys())[0].split("-")[1]))
            return Response("Blocked Package")

        # * Check if we need to update the current directory where we are storing images
        current_date = int(datetime.datetime.fromtimestamp(time.time()).strftime('%d'))
        if current_date > prev_date: 
            prev_date = current_date
            current_img_dir = str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H-%M'))
            new_path = os.getcwd() + "/api/Images/" + list(data.keys())[0].split("-")[0] + "/" + current_img_dir
            # * Create the new directory
            if not os.path.exists(new_path):
                os.mkdir(new_path)

        recieve_time = datetime.datetime.fromtimestamp(time.time()).strftime('%S')

        face_image_paths = []
        bar_image_paths = []
        
        uniqueID = 0
        # * Go through all image keys in dictionary
        for t in data.items():
            i, img = t
            imgName = str(img)
            print("DEBUG", imgName)

            # * Open new image file
            curr_time = str(round(time.time()))
            destination = f"api/Images/{i.split('-')[0]}/{current_img_dir}/{package_id}_{recieve_time}_{curr_time}_{imgName}_{uniqueID}.jpg"
            if "Barcode" in imgName:
                bar_image_paths.append(destination)
            else:
                face_image_paths.append(destination)
            
            with open(destination, "wb") as binary_file:
                # * Write image bytes to file
                binary_file.write(img.file.read())
            uniqueID += 1

        package_id += 1
        
        returnID = -1
        # * Barcode Detection
        if len(bar_image_paths) != 0:
            returnID = readMultipleBarcodes(bar_image_paths)
            print("Barcode ID: ", returnID)

        if returnID == -1 and len(face_image_paths) != 0:
            # * Face detection
            returnID = recognize_face(face_image_paths, database)
            print("Face ID: ", returnID)

        print("FINAL ID: ", returnID)
        with open('outs.txt', 'a') as f:
            f.write(f"{returnID} was detected at {str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H-%M-%S'))}\n")

        return Response(returnID[0])
        # return Response(f"{returnID}")
    except Exception as e:
        print(e)
        with open('errors.txt', 'a') as f:
            f.write(f"ERROR: {e}\n" +
                    f"Date: {str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H-%M-%S'))}\n")
            f.write(f"Request: {request}\n"+
                    f"Request Data: {request.data}\n"+
                    f"Request Items: {list(request.data.items())}\n\n")
        # * Return the exception if the code errors
        return Response(str(e))



@api_view(['POST'])
def postID(request):
    try:
        print("request:",request.data,request.data.items())
        studentID = request.data["studentID"]
        print("id:",studentID)
        # serializer = StudentIDSerializer(data={"accept":True})

        # if serializer.is_valid():
        #     serializer.save()
        hasSeniorPriv = True

        return Response({"accept":hasSeniorPriv})
    except Exception as e:
        print(e)
        # * Return the exception if the code errors
        return Response(str(e))


# idk if this is done right, just change it if it isn't
def IndexWebApp(request):
    return render(request, 'index.html')

# Create your views here


class UserViewSet(viewsets.ModelViewSet):
    queryset = get_user_model().objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class StudentDateInOutStatusViewSet(viewsets.ModelViewSet):
        queryset = StudentDateInOutStatus.objects.all()
        serializer_class = StudentDateInOutStatusSerializer


def getTransactionSet(request):
    queryset = Transaction.objects.all()
    kiosk_id = request.GET.get('kiosk_id', None)
    if kiosk_id is not None:
        queryset = queryset.filter(kiosk_id=kiosk_id)
    entered_id = request.GET.get('entered_id', None)
    if entered_id is not None:
        queryset = queryset.filter(entered_id=entered_id)
    from_datetime = request.GET.get('from_datetime', None)
    if from_datetime is not None:
        queryset = queryset.filter(timestamp__gte=from_datetime)
    to_datetime = request.GET.get('to_datetime', None)
    if to_datetime is not None:
        queryset = queryset.filter(timestamp__lte=to_datetime)
    student_id = request.GET.get('student_id', None)
    if student_id is not None:
        queryset = queryset.filter(student__student_id=student_id)
    student_name = request.GET.get('student_name', None)
    if student_name is not None:
        queryset = queryset.filter(student__name__contains=student_name)
    morning = request.GET.get('morning_mode', None)
    if morning is not None:
        queryset = queryset.filter(morning_mode=morning)
    flag = request.GET.get('flag', None)
    if flag is not None:
        queryset = queryset.filter(flag=flag)

    return queryset

def getStudentSet(request):
    queryset = Student.objects.all()
    name = request.GET.get('name', None)
    if name is not None:
        queryset = queryset.filter(name__contains=name)
    grade = request.GET.get('grade', None)
    if grade is not None:
        queryset = queryset.filter(grade=grade)
    student_id = request.GET.get('student_id', None)
    if student_id is not None:
        queryset = queryset.filter(student_id__contains=student_id)
    privilege_granted = request.GET.get('privilege_granted', None)
    if privilege_granted is not None:
        queryset = queryset.filter(privilege_granted=privilege_granted)
    return queryset


class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    queryset = Student.objects.all()

    def get_queryset(self):
        return getStudentSet(self.request)


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def get_queryset(self):
        return getTransactionSet(self.request)


def downloadStudent(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="student_download.csv"'
    writer = csv.writer(response)
    writer.writerow(['name', 'student_id', 'grade', 'privilege_granted', 'pathToImage'])
    for student in getStudentSet(request):
        writer.writerow([
            student.name,
            student.student_id,
            student.grade,
            student.privilege_granted,
            student.pathToImage,
        ])
    return response


def downloadTransaction(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transaction_download.csv"'
    writer = csv.writer(response)
    writer.writerow(['internal_id', 'entered_id', 'student_name', 'student_id', 'date', 'time', 'morning', 'entering', 'flagged'])
    for transaction in getTransactionSet(request):
        writer.writerow([
            transaction.pk,
            transaction.entered_id,
            transaction.student.name if transaction.student is not None else "N/A",
            transaction.student.student_id if transaction.student is not None else "N/A",
            transaction.timestamp.astimezone(tz.timezone("America/New_York")).strftime("%x"),
            transaction.timestamp.astimezone(tz.timezone("America/New_York")).strftime("%X"),
            transaction.morning_mode,
            transaction.entering,
            transaction.flag,
        ])
    return response


def kioskLogin(request):
    entered_id = request.GET.get('id', "")
    kiosk = request.GET.get('kiosk', "")

    if kiosk == "" or entered_id == "":
        return HttpResponse(status=400)


    search_student = Student.objects.all().filter(student_id=entered_id)
    search_student = None if len(search_student) == 0 else search_student[0]

    # search_student = Student.objects.all().filter(student_id=entered_id)
    # search_student = str(search_student[0]).split(",")
    # grade = int(search_student[1])
    # search_student = None if len(search_student) == 0 else search_student[0]
    automorningmode = datetime.now().hour == 11 and datetime.now().minute > 45
    gen_morning = IN_MORNING_MODE or automorningmode

    autoflag = False
    if search_student is not None:
        autoflag = search_student.privilege_granted == 0 and gen_morning == False

    movement = False
    if search_student is not None:
        if not gen_morning:
            movement = search_student.toggleIn(date.today())
        else:
            movement = True

    trans_id = Transaction.objects.create(kiosk_id=kiosk, student=search_student, entered_id=entered_id, timestamp=datetime.now(tz=timezone.utc), morning_mode=gen_morning, flag=autoflag, entering=movement).id


    async_to_sync(get_channel_layer().group_send)("security", {'type': 'message', 'message': {
        "id": trans_id,
        'kiosk_id': kiosk,
        'student': search_student.clean() if search_student is not None else None,
        'entered_id': entered_id,
        'timestamp': str(datetime.now(tz=timezone.utc)),
        'morning_mode': gen_morning,
        'flag': autoflag,
        'entering': movement,
    }})

    if search_student is not None:
        accepted = True if gen_morning else search_student.privilege_granted
        checkLateStudent(search_student.name, search_student.student_id, True if gen_morning else search_student.privilege_granted, movement, int(search_student.grade))
        return JsonResponse(data={"name": search_student.name,
                                  "accept": True if gen_morning else search_student.privilege_granted,
                                  "seniorPriv": True if gen_morning else search_student.privilege_granted,
                                  "id": search_student.student_id,
                                  "in": movement,
                                  }
                            )

    return JsonResponse(data={"name": "Invalid ID", "accept": False, "id": 00000, "seniorPriv": 0, "in": 0})

def checkLateStudent(studentName, studentId, seniorPriv, movement, grade):

    # Get all the datetime stuff 
    curtime = datetime.now()
    curday = str(date.today())
    curhour = curtime.hour - 4

    # Since the datetime timezone is 4 hours ahead, we have to check if its the next day in datetime and account for that in this if statement
    nextday = True if curhour < 0 else False
    if nextday:
        curhour += 24
        curday = curday.split("-")
        curday[2] = str(int(curday[2])-1)
        curday = "-".join(curday)
    curmin = curtime.minute
    cursecond = curtime.second
    morning = True if curhour <= 12 else False

    #Make this true if you want to test out the csv appending system
    testing = False

    # This is where the csv gets created and/or edited if the time is between 8:00 - 8:15 (inclusive)
    if ((curhour == 8 and curmin <= 30 and curmin >= 0 and morning) or testing):
        filename = curday + ".csv"
        csvexists = True if not os.path.exists("gdrive/Late Students/"+filename) else False
        f = open("gdrive/Late Students/" + filename, "a")
        if csvexists:
            csv.writer(f).writerow(["Name", "ID", "Time", "Senior Privilege", "Movement", "Grade"])
        csv.writer(f).writerow([studentName, studentId, (str(curhour) if morning else str(curhour-12)) + ":" + ("0" if curmin < 10 else "" ) + str(curmin) + (" AM" if morning else " PM"), str(seniorPriv), "Incoming" if movement else "Outgoing", grade])
        f.close()

        #This runs terminal commands to push the changes made to drive
        os.chdir("gdrive")
        os.system("drive push & y")
        os.chdir("..")

def revertStudent(request):
    def fix(val, current):
        return val[1] if val is not None else current

    student_primary_key = int(request.GET.get('id', None))
    revision_revert = int(request.GET.get('revert', None))
    s = Student.objects.all().get(pk=student_primary_key)
    num_entries =  len(Student.objects.all().get(pk=student_primary_key).history.all())
    if num_entries > revision_revert:
        for i in range(revision_revert+1):
            n = Student.objects.all().get(pk=student_primary_key).history.all()[::-1][i].changes_display_dict
            s.name = fix(n.get("name", None), s.name)
            s.student_id = fix(n.get("student id", None), s.student_id)
            s.grade = fix(n.get("grade", None), s.grade)
            s.privilege_granted = fix(n.get("privilege granted", None), s.privilege_granted)
            s.pathToImage = fix(n.get("pathToImage", None), s.pathToImage)
    s.save()
    return JsonResponse(data={})


def getStrikes(request):
    data = []
    for student in getStudentSet(request):
        d = {}
        d['student'] = student.clean()
        d['strikes'] = []
        d['num_strikes'] = 0
        d['num_unresolved_strikes'] = 0
        for state in student.end_states.all():
            if state.in_school == False:
                d['strikes'].append(model_to_dict(state))
                d['num_strikes'] += 1
                if not state.resolved:
                    d['num_unresolved_strikes'] += 1
        if d['num_strikes'] != 0:
            data.append(d)
    return JsonResponse(data=data, safe=False)


def getMorningMode(request):
    return JsonResponse(data={"status": IN_MORNING_MODE})


def setMorningMode(request):
    global IN_MORNING_MODE
    setTo = True if int(request.GET.get("status", "None")) == 1 else False
    IN_MORNING_MODE = setTo
    return getMorningMode(request)

