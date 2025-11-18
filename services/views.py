from plotly.offline import plot
from plotly.graph_objs import Scatter
import os
from datetime import datetime
import json
from .backend.database.sqlclasses import dictpull, moving_average
from .backend.graphgeneration.createCustom import customGraph, makeTable
from django.template.defaulttags import csrf_token
from config import settings
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, logout
from django.contrib.auth import login as d_login # our login opage func is called login... thus overriding django login unless we rename
from django.core.mail import send_mail
from django.http import HttpResponse
import csv
# Create your views here.
# def store_data(request):
#     if request.method == 'POST':
#         # Retrieve form data
#         username = request.POST.get('username', '')
#         email = request.POST.get('email', '')
#         # Add more fields as needed

#         # Save data to a CSV file
#         with open('user_data.csv', 'a', newline='') as csvfile:
#             fieldnames = ['username', 'password', 'confirm password', 'email']  # Add more fields here
#             writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
#             writer.writerow({'username': username, 'email': email})  # Add more fields here

#         return HttpResponse('Data stored successfully')
#     else:
#         return HttpResponse('Invalid request method')

def favorites(request):
    favorites = []
    if request.user.is_authenticated:
        favorites = request.user.favorites.all()
    return render(request, 'HTML/favorites.html', {"favorites": favorites})

def contactus(request):
    return render(request,'HTML/contactus.html')
def register(request):
    return render(request, "HTML/register.html")
def login(request):
    return render(request, 'HTML/login.html')
def signup(request):

    if request.method == "POST":
        username = request.POST['username']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']

        # can't just call signup function because then we recurse
        # so redirect back to page manually
        if User.objects.filter(username=username):
            messages.error(request, "Username is taken. Please try another username")
            # return redirect('register/')
            return register(request)
        
        if len(username)>20:
            messages.error(request, "Username must be less than 20 charcters")
            return register(request)
        
        if pass1 != pass2:
            messages.error(request, "Pelase ensure both passwords match")
            return register(request)
        
        # TODO not sure why this is here, but we probably don't need to require this
        if not username.isalnum():
            messages.error(request, "Please only include letters and numbers")
            return register(request)
        
        myuser = User.objects.create_user(username=username, password=pass1)
        myuser.save()

        '''
        Email message from previous semesters
        As of Spring 25 we're not storing any email info but if that changes most of the code is here
        Just make sure to get email from user and save above
        '''
        # messages.success(request, "Your account has been succefully created. We have sent you a confirmation email, please confirm your email in order to activate your account")

        # #Welcome email

        # subject = "Welcome to HDR - Django Login!"
        # message = "Hello" + myuser.first_name + "!! \n" + "Welcome to HDR!! \n Thank you for visiting our website \n We habe also sent you a confirmation email, please comfirm email adress in order to activate your account. \n\n Thanking you \n HDR TEAM"
        # from_email = settings.EMAIL_HOST_USER
        # to_list = [myuser.email]
        # send_mail(subject, message, from_email, to_list, fail_silently = True)

        messages.success(request, "Your account has been created succesfully")
        return login(request)

    return register(request)

def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        pass1 = request.POST['pass1']
        
        user = authenticate(request, username=username, password=pass1)
        
        if user is None:
            messages.error(request, "We were unable to find an account with that username and password.")
            return login(request)
        
        d_login(request, user)
        uname = user.username

        messages.success(request, f"You're logged in! Hello {uname}")
        print(f"user {uname} logged in")
    
    # bring user to homepage after they've logged in
    return homepage(request)

def signout(request):
    logout(request)
    return homepage(request)

def about(request):
    return render(request, 'HTML/about.html')

def forecast(request):
    return render(request, 'HTML/forecast.html')

def homepage(request):
    return render(request, 'HTML/homepage.html')

def maptabs(request):
    return render(request, 'HTML/maptabs.html')
    
def tabs(request):
    return render(request, 'graphing/tabs.html')

def tabstest(request):
    return render(request, 'graphing/tabstest.html')

def test(request):
    return render(request, 'graphing/test.html')

def customgauge(request):
    return render(request, 'graphing/customgauge.html')

def customdam(request):
    return render(request, 'graphing/customdam.html')

def custommesonet(request):
    return render(request, 'graphing/custommesonet.html')

def interactiveMap(request):
    
    return render(request, 'HTML/interactiveMap.html')

def customgaugegraph(request):
    
    #Pulls most recently submitted data
    locationlist = request.POST.getlist('location')
    length = len(locationlist)

    data2see = request.POST['data2see']

    start_date = request.POST['start-date']

    end_date = request.POST['end-date']

    datalist = []
    sites = []
    index = 0
    while index < length:
        locations = locationlist[index]
        locations = locations.split()
        if locations[0] == "Little":
            locations[0] = "Little Eagle"
        sites.append(locations[0])
        times, data = dictpull(locations[0], data2see, start_date, end_date, "gauge")
        m = moving_average()
        m_t, m_d = m.one_day_ma(times,data)
        datalist.append(data)
        index += 1
        
    plot = customGraph(times, sites, datalist, data2see, 0)
    table = makeTable(datalist, 0)

    return render(request, "HTML/graphdisplay.html", context={'plot': plot, 'table': table})

def customdamgraph(request):

    locationlist = request.POST.getlist('dam')
    length = len(locationlist)
    data2see = request.POST['data2see']
    if "_" in data2see:
        data2see = data2see.split("_")
        data2see = data2see[0] + " " + data2see[1]

    start_date = request.POST['start-date']

    end_date = request.POST['end-date']

    folder_path = "./map/static/customdata/"

    datalist = []
    sites = []
    index = 0
    while index < length:
        sites.append(locationlist[index])
        times, data = dictpull(locationlist[index], data2see, start_date, end_date, "dam")
        datalist.append(data)
        index += 1
        
    plot = customGraph(times, sites, datalist, data2see, 0)
    table = makeTable(datalist, 0)

    return render(request, 'HTML/graphdisplay.html', context={'plot': plot, 'table': table})

def custommesonetgraph(request):

    locationlist = request.POST.getlist('mesonet')
    length = len(locationlist)
    data2see = request.POST['data2see']
    if "_" in data2see:
        data2see = data2see.split("_")
        data2see = data2see[0] + " " + data2see[1]

    start_date = request.POST['start-date']

    end_date = request.POST['end-date']

    datalist = []
    sites = []
    index = 0
    while index < length:
        sites.append(locationlist[index])
        times, data = dictpull(locationlist[index], data2see, start_date, end_date, "mesonet")
        datalist.append(data)
        index += 1
        
    plot = customGraph(times, sites, datalist, data2see, 0)
    table = makeTable(datalist, 0)

    return render(request, 'HTML/graphdisplay.html', context={'plot': plot, 'table': table})

def customcocograph(request):

    locationlist = request.POST.getlist('cocorahs')
    length = len(locationlist)
    data2see = request.POST['data2see']
    if "_" in data2see:
        data2see = data2see.split("_")
        data2see = data2see[0] + " " + data2see[1]

    start_date = request.POST['start-date']

    end_date = request.POST['end-date']

    datalist = []
    sites = []
    index = 0
    while index < length:
        sites.append(locationlist[index])
        times, data = dictpull(locationlist[index], data2see, start_date, end_date, "cocorahs")
        datalist.append(data)
        index += 1
        
    plot = customGraph(times, sites, datalist, data2see, 0)
    table = makeTable(datalist, 0)

    return render(request, 'HTML/graphdisplay.html', context={'plot': plot, 'table': table})

def customshadehillgraph(request):
    
    data2see = request.POST['data2see']
    if "_" in data2see:
        data2see = data2see.split("_")
        data2see = data2see[0] + " " + data2see[1]

    start_date = request.POST['start-date']
    end_date = request.POST['end-date']
    
    times, data = dictpull("Shadehill", data2see, start_date, end_date, "shadehill")

    plot = customGraph(times, ["Shadehill"], [data], data2see, 0)
    table = makeTable([data], 0)

    return render(request, 'HTML/graphdisplay.html', context={'plot': plot, 'table': table})

def customnoaagraph(request):

    locationlist = request.POST.getlist('noaa')
    length = len(locationlist)
    data2see = request.POST['data2see']
    if "_" in data2see:
        data2see = data2see.split("_")
        data2see = data2see[0] + " " + data2see[1]

    start_date = request.POST['start-date']

    end_date = request.POST['end-date']

    datalist = []
    sites = []
    index = 0
    while index < length:
        sites.append(locationlist[index])
        times, data = dictpull(locationlist[index], data2see, start_date, end_date, "noaa")
        datalist.append(data)
        index += 1
        
    plot = customGraph(times, sites, datalist, data2see, 0)
    table = makeTable(datalist, 0)

    return render(request, 'HTML/graphdisplay.html', context={'plot': plot, 'table': table})
