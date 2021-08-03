from django.shortcuts import render, redirect
from django.contrib import messages
import bcrypt
from .models import *
from datetime import datetime, date
# from datetime import date
from django.core.paginator import Paginator
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import numpy as np
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter

# default_companies = ['Amazon', "Pandora", "Hulu", "Planet Fitness", "Sam's Club", "YouTube", "Masterclass",
# "Disney+",
# "P.volve",
# "Netflix",
# "Annie's Creative Studio",
# "Philo",
# "Scribd",
# "Apple News+",
# "Blinkist",
# "Wondium",
# "Kindle Unlimited",
# "Epic!",
# "Amazon Music Unlimited",
# "Goddess Provisions Moon Wisdom"]

def index(request):
    return render(request, "index.html")


def check_registration(request):
    if request.method == "POST":
        # errors handling
        errors = User.objects.basic_validator(request.POST)
        if len(errors) > 0:
            for error in errors.values():
                messages.error(request, error)
        else:
            hashed_pw = bcrypt.hashpw(request.POST['password'].encode(), bcrypt.gensalt()).decode()
            new_user = User.objects.create(
                first_name = request.POST['first-name'], 
                last_name = request.POST['last-name'], 
                email = request.POST['email'], 
                password = hashed_pw)
            request.session['user_id'] = new_user.id
            return redirect('/subscriptions/sd/1')
    return redirect('/')


def check_login(request):
    if request.method == "POST":
        # errors handling
        errors = User.objects.login_validator(request.POST)
        if len(errors) > 0:
            for error in errors.values():
                messages.error(request, error)
        else:
            this_user = User.objects.get(email=request.POST['email'])
            request.session['user_id'] = this_user.id
            return redirect('/subscriptions/sd/1')
    return redirect ("/")


def logout(request):
    request.session.flush()
    return redirect('/')


def subscriptions(request, order_by, page_num):
    if 'user_id' in request.session:
        logged_user = User.objects.get(id=request.session['user_id'])
        
        # order_by selected column
        if order_by == "cn":
            order_by_field = "company__company_name" 
        elif order_by == "_cn":
            order_by_field = "-company__company_name" 
        elif order_by == "ac":
            order_by_field = "account"
        elif order_by == "_ac":
            order_by_field = "-account"
        elif order_by == "st":
            order_by_field = "level"
        elif order_by == "_st":
            order_by_field = "-level"
        elif order_by == "mr":
            order_by_field = "monthly_rate"
        elif order_by == "_mr":
            order_by_field = "-monthly_rate"
        elif order_by == "rb":
            order_by_field = "renew_by_date"
        elif order_by == "_rb":
            order_by_field = "-renew_by_date"
        elif order_by == "_sd":
            order_by_field = "-start_date"
        else:
            order_by_field = "start_date"
        
        my_subscriptions = Subscription.objects.filter(user = logged_user).order_by(order_by_field)
        
        # pagination driver
        p = Paginator(my_subscriptions, 10)
        page = p.page(page_num)
        num_of_pages = "a" * p.num_pages
        
        context = {
            'logged_user': logged_user,
            'my_subscriptions': page,
            'num_of_pages': num_of_pages,
            'order_by': order_by,
            'near_due_subscriptions': Subscription.objects.filter(user=logged_user).order_by("renew_by_date")[:6],
        }
        return render(request, 'subscription.html', context)    
    return redirect('/')


def get_graph():
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    graph = base64.b64encode(image_png)
    graph = graph.decode('utf-8')
    buffer.close()
    return graph

def get_plot(companies):
    list_graph =[]
    for company_name in companies:
        company_date_price = companies[company_name]
        x = company_date_price.keys()
        
        y = company_date_price.values()
        
        plt.switch_backend('AGG')
        plt.figure(figsize=(10,5))
        plt.title(company_name)
        ax = plt.gca()
        formatter = mdates.DateFormatter("%Y-%m-%d")
        ax.xaxis.set_major_formatter(formatter)
        locator = mdates.DayLocator()
        ax.xaxis.set_major_locator(locator)
        plt.plot(x,y,marker ='o',mfc='red',linestyle ='--')
        plt.xlabel('Dates')
        plt.ylabel('Prices')
        graph=get_graph()
        list_graph.append(graph)
    return list_graph

def stats(request, subscription_id):
    if 'user_id' in request.session:
        logged_user = User.objects.get(id=request.session['user_id'])
        all_subscriptions = Subscription.objects.filter(user = logged_user)
        if len(all_subscriptions) < 1:
            context = {
                'all_subscriptions_count': len(all_subscriptions),
                'user' : logged_user,
            }
            return render(request, 'stats.html', context) 
        
        this_subscription = Subscription.objects.get(id=subscription_id)

        companies={}
        company_date_price = {}

        data_points = DataPoint.objects.filter(subscription= this_subscription).order_by("placed_at")
        
        for data in data_points:
            date = data.placed_at.date()
            price = data.monthly_rate
            print(date,price)
            company_date_price[date] = price
            
        companies[this_subscription.company.company_name] = company_date_price
        
        list_graph = get_plot(companies)
        context = {
            'all_subscriptions_count': len(all_subscriptions),
            'user' : logged_user,
            'list_graph':list_graph,
            'all_subscriptions': all_subscriptions,
        }
        return render(request, 'stats.html', context)    
    return redirect('/')


def user_account(request):
    if 'user_id' in request.session:
        logged_user = User.objects.get(id=request.session['user_id'])

        context = {
            'logged_user': logged_user,
            'user_subscriptions': Subscription.objects.filter(user=logged_user),
        }
        return render(request, "editUser.html", context)
    return redirect("/")  


def process_edit_user(request):
    if 'user_id' in request.session:
        if request.method == "POST":
            # errors handling
            errors = User.objects.edit_profile_validator(request.POST)
            if len(errors) > 0:
                for error in errors.values():
                    messages.error(request, error)
            else:
                logged_user = User.objects.get(id=request.session['user_id'])
                logged_user.first_name = request.POST['first_name']
                logged_user.last_name = request.POST['last_name']
                logged_user.email = request.POST['email']
                logged_user.save()
                messages.error(request, "Successfully updated profile")
        return redirect("/user_account")
    return redirect("/")


def add_subscription(request):
    if 'user_id' in request.session:
        logged_user = User.objects.get(id=request.session['user_id'])
        all_companies = Company.objects.filter(entered_by_admin=True).order_by("company_name")
        # todays_date = date.now(),

        context = {
            'logged_user': logged_user,
            'all_companies': all_companies,
            # 'todays_date': todays_date,
        }
        return render(request, "add_subscription.html", context)
    return redirect("/")  


def process_add_subscription(request):
    if 'user_id' in request.session:
        if request.method == "POST":
            # errors handling
            errors = Subscription.objects.add_subscription_validator(request.POST)
            if len(errors) > 0:
                for error in errors.values():
                    messages.error(request, error)
                return redirect("/add_subscription")
            else:
                logged_user = User.objects.get(id=request.session['user_id'])
                st_date = request.POST['start_date']
                sub_duration = request.POST['duration']

                # figure out time displacement
                # options ("Bi-annually", "Yearly")
                if sub_duration == "Bi-annually":
                    time_change = 2
                elif sub_duration == "Yearly":
                    time_change = 1

                s_date = st_date.split("-")
                add_time = int(s_date[0])+time_change
                s_date[0] = str(add_time)
                renew_date = "-".join(s_date)
                date_plus_time = datetime.strptime(renew_date, '%Y-%m-%d')        
            
                # gets or creates company to be subscribed to 
                if request.POST['company_id'] == "-1":
                    # if (request.POST['company_name']).capitalize() not in 
                    this_company = Company.objects.create(
                        company_name = (request.POST['company_name']).capitalize()
                    )
                else:
                    this_company = Company.objects.get(id= request.POST['company_id'])
                    
                # creates new subscription
                new_subscription = Subscription.objects.create(
                    user = logged_user,
                    company = this_company,
                    account = request.POST['account'],
                    level = request.POST['level'],
                    monthly_rate = Decimal(request.POST['monthly_rate']),
                    start_date = st_date,
                    renew_by_date = date_plus_time,
                    duration = sub_duration,
                )

                # sets initial datapoint for the subscription
                DataPoint.objects.create(
                    subscription = new_subscription,
                    monthly_rate = Decimal(request.POST['monthly_rate']),
                    placed_at = datetime.now(),
                )
                messages.error(request, "Subscription Successfully Added!")
                return redirect(f"/edit_subscription/{ new_subscription.id }")
        return redirect("/add_subscription")
    return redirect("/")  

def edit_subscription(request, subscription_id):
    if 'user_id' in request.session:
        logged_user = User.objects.get(id=request.session['user_id'])
        subscription_to_edit = Subscription.objects.get(id=subscription_id)
        if subscription_to_edit.user == logged_user:  
            all_companies = Company.objects.filter(entered_by_admin=True).order_by("company_name")   
            context = {
                'logged_user': logged_user,
                'subscription_to_edit': subscription_to_edit,
                'all_companies': all_companies,
            }
            return render(request, "editSubscription.html", context)
        return redirect("/subscriptions/sd/1")
    return redirect("/")


def process_edit_subscription(request, subscription_id):
    if 'user_id' in request.session:
        if request.method == "POST":
            # errors handling
            errors = Subscription.objects.edit_subscription_validator(request.POST)
            if len(errors) > 0:
                for error in errors.values():
                    messages.error(request, error)
            else:
                logged_user = User.objects.get(id=request.session['user_id'])
                subscription_to_edit = Subscription.objects.get(id=request.POST['subscription_id'])
                if subscription_to_edit.user == logged_user:    

                    if request.POST['company_id'] == "-1":
                        if subscription_to_edit.company.entered_by_admin:
                            this_company = Company.objects.create(
                            company_name = request.POST['company_name']
                            )
                            subscription_to_edit.company = this_company
                        else:
                            if subscription_to_edit.company.company_name != request.POST['company_name']:
                                company_to_delete_id = subscription_to_edit.company.id
                                company_to_delete = Company.objects.get(id=company_to_delete_id)
                                this_company = Company.objects.create(
                                    company_name = request.POST['company_name']
                                )
                                subscription_to_edit.company = this_company
                                company_to_delete.delete()
                    else:
                        if subscription_to_edit.company.entered_by_admin:
                            this_company = Company.objects.get(id= request.POST['company_id'])
                            subscription_to_edit.company = this_company
                        else:
                            company_to_delete_id = subscription_to_edit.company.id
                            company_to_delete = Company.objects.get(id=company_to_delete_id)
                            this_company = Company.objects.get(id= request.POST['company_id'])
                            subscription_to_edit.company = this_company
                            company_to_delete.delete()

                    subscription_to_edit.level = request.POST['level']

                    if subscription_to_edit.monthly_rate != Decimal(request.POST['monthly_rate']):
                        price_change = Decimal(request.POST['monthly_rate']) - subscription_to_edit.monthly_rate
                        DataPoint.objects.create(
                            subscription = subscription_to_edit,
                            monthly_rate = Decimal(request.POST['monthly_rate']),
                            price_change = price_change,
                            placed_at = datetime.now(),
                        )
                        subscription_to_edit.monthly_rate = Decimal(request.POST['monthly_rate'])

                    st_date = request.POST['start_date']
                    sub_duration = request.POST['duration']

                    # figure out time displacement
                    # options ("Bi-annually", "Yearly")
                    if sub_duration == "Bi-annually":
                        time_change = 2
                    elif sub_duration == "Yearly":
                        time_change = 1

                    s_date = st_date.split("-")

                    if sub_duration == "Bi-annually" or sub_duration == "Yearly":
                        add_time = int(s_date[0])+time_change
                        s_date[0] = str(add_time)
                        renew_date = "-".join(s_date)
                        date_plus_time = datetime.strptime(renew_date, '%Y-%m-%d')    

                    subscription_to_edit.account = request.POST['account']
                    subscription_to_edit.start_date = st_date
                    subscription_to_edit.duration = sub_duration
                    subscription_to_edit.renew_by_date = date_plus_time

                    subscription_to_edit.save()
        return redirect(f"/edit_subscription/{ subscription_id }")            
    return redirect("/")


def delete_subscription(request):
    if 'user_id' in request.session:
        if request.method == "POST":
            logged_user = User.objects.get(id=request.session['user_id'])
            subscription_to_delete = Subscription.objects.get(id=request.POST['subscription_id'])
            if subscription_to_delete.user == logged_user:     
                subscription_to_delete.delete()
                messages.error(request, "Subscription Successfully Deleted!")
        return redirect("/subscriptions/sd/1")
    return redirect("/")


def select_sub_to_view(request):
    if 'user_id' in request.session:
        if request.method == "POST":
            subscription_id = request.POST['subscription_id']
    return redirect(f"/stats/{ subscription_id }")
