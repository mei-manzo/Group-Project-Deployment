from django.db import models
import re
import bcrypt
from decimal import Decimal
import datetime


EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
NAME_REGEX = re.compile(r'^[a-zA-Z]+$')
PRICE_REGEX = re.compile(r'^[0-9]+\.[0-9]+$')
NUM_REGEX = re.compile(r'^[0-9]+$')


class UserManager(models.Manager):
    def basic_validator(self, postData):
        errors = {}

        email = postData['email']
        if len(postData['first-name']) <2:
            errors["first_name"]="First name should be at least 2 characters"
        if len(postData['last-name']) <2:
            errors["last_name"]="Last name should be at least 2 characters"
        if not EMAIL_REGEX.match(postData['email']):             
            errors['email'] = ("Invalid email address!")
        if len(User.objects.filter(email=email)) >= 1:
            errors["email"]="Email is already in use"
        if len(postData['password']) < 8:
            errors["password"]="Password must be at least 8 characters"
        if postData['password'] != postData['confirm-password']:
            errors["password"]="Passwords do not match"
        return errors
        
    def login_validator(self, postData):
        errors = {}

        existing_user = User.objects.filter(email=postData['email'])
        if len(postData['email']) == 0:
            errors['email'] = "Must enter an email"
        elif len(existing_user) == 0: 
            errors['email'] = "Email is not registered"
        elif len(postData['password']) < 8:
            errors['password'] = "Must enter a password 8 characters or longer"
        elif bcrypt.checkpw(postData['password'].encode(), existing_user[0].password.encode()) != True:
            errors['password'] = "Email and password do not match"
        return errors

    def edit_profile_validator(self, postData):
        errors = {}

        if len(postData['first_name']) < 2 or not NAME_REGEX.match(postData['first_name']):
            errors['first_name'] = "Please enter a valid first name"
        if len(postData['last_name']) < 2 or not NAME_REGEX.match(postData['last_name']):
            errors['last_name'] = "Please enter a valid last name"
        if len(postData['email']) < 2 or not EMAIL_REGEX.match(postData['email']):
            errors["email"] = "Please enter a valid email"
        user = self.get(id=postData['user_id'])
        if user.email != postData['email']:
            email_in_db = self.filter(email = postData['email'])
            if email_in_db:
                errors['email'] = "This email is already registered to another user"
        return errors


class SubscriptionManager(models.Manager): #validates subscription data
    def add_subscription_validator(self, postData):
        errors = {}
        
        if len(postData['account']) <2:
            errors["account"] = "Subscription account should be at least 2 characters."

        logged_user = User.objects.get(id=postData['user_id'])
        user_subscriptions = Subscription.objects.filter(user=logged_user)
        if postData['company_id'] != "-1" and len(postData['company_name']) > 0:
            errors["company"] = "Please do not select a company from the dropdown and enter your own."
        elif postData['company_id'] == "-1" and len(postData['company_name']) < 1:
            errors["company"] = "Please either select a company from the dropdown or enter your own."
        else:
            if postData['company_id'] == "-1":
                if len(postData['company_name']) < 2:
                    errors["company"] = "A company name should be longer than 2 characters."
                admin_company_exists = Company.objects.filter(company_name=postData['company_name'].capitalize()).filter(entered_by_admin=True)
                if admin_company_exists:
                    errors["company"] = "Company Already Exists Please Select From Dropdown"                
                for subscription in user_subscriptions:
                    if subscription.company.company_name == postData['company_name'] and subscription.account == postData['account']:
                        errors["company"] = "You have already entered this account"
            else:
                company_to_check = Company.objects.get(id=postData['company_id'])
                for subscription in user_subscriptions:
                    if subscription.company == company_to_check and subscription.account == postData['account']:
                        errors["company"] = "You have already entered this account"

        if len(postData['level']) <2:
            errors["level"] = "Subscription level should be at least 2 characters."
        if len(postData['monthly_rate']) < 1:
            errors["monthly_rate"] = "Must enter a monthly rate"
        if not PRICE_REGEX.match(postData['monthly_rate']):             
            errors['monthly_rate'] = "Invalid monetary value!"

        if len(postData['start_date']) < 1:
            errors["start_date"] = "Please select a valid start date." 
        if postData['start_date'] >= str(datetime.date.today()):
            errors['start_date'] = "Please enter a date prior to today's date"
        nums = postData['start_date'].split("-")
        within_twenty = int(nums[0])+20
        nums[0] = str(within_twenty)
        new_date = "-".join(nums)
        date_plus_twenty = datetime.datetime.strptime(new_date, '%Y-%m-%d')
        if date_plus_twenty < datetime.datetime.now():
            errors["start_date"] = "The start date must be within the last 20 years."

        if postData['duration'] == "-1":
            errors["duration"] = "Please select a duration."
        return errors

    def edit_subscription_validator(self, postData):
        errors = {}
        
        if len(postData['account']) <2:
            errors["account"] = "Subscription account should be at least 2 characters."

        logged_user = User.objects.get(id=postData['user_id'])
        if postData['company_id'] != "-1" and len(postData['company_name']) > 0:
            errors["company"] = "Please do not select a company from the dropdown and enter a your own."
        elif postData['company_id'] == "-1" and len(postData['company_name']) < 1:
            errors["company"] = "Please either select a company from the dropdown or enter a your own."
        else:
            if postData['company_id'] == "-1":
                if len(postData['company_name']) < 2:
                    errors["company"] = "A company name should be longer than 2 characters."
                admin_company_exists = Company.objects.filter(company_name=postData['company_name'].capitalize()).filter(entered_by_admin=True)
                if admin_company_exists:
                    errors["company"] = "Company Already Exists Please Select From Dropdown" 
                subscription_exists = Subscription.objects.filter(user=logged_user).filter(company__company_name=postData['company_name']).filter(account=postData['account']).exclude(id=postData['subscription_id'])
                if subscription_exists:
                    errors["company"] = "You have already entered this account previously"
            else:
                company_to_check = Company.objects.get(id=postData['company_id'])
                subscription_exists = Subscription.objects.filter(user=logged_user).filter(company=company_to_check).filter(account=postData['account']).exclude(id=postData['subscription_id'])
                if subscription_exists:
                    errors["company"] = "You have already entered this account previously"

        if len(postData['level']) <2:
            errors["level"] = "Subscription level should be at least 2 characters."
        if len(postData['monthly_rate']) < 1:
            errors["monthly_rate"] = "Must enter a monthly rate"
        if not PRICE_REGEX.match(postData['monthly_rate']):             
            errors['monthly_rate'] = "Invalid monetary value!"

        if len(postData['start_date']) < 1:
            errors["start_date"] = "Please select a valid start date." 
        if postData['start_date'] >= str(datetime.date.today()):
            errors['start_date'] = "Please enter a date prior to today's date"
        nums = postData['start_date'].split("-")
        within_twenty = int(nums[0])+20
        nums[0] = str(within_twenty)
        new_date = "-".join(nums)
        date_plus_twenty = datetime.datetime.strptime(new_date, '%Y-%m-%d')
        if date_plus_twenty < datetime.datetime.now():
            errors["start_date"] = "The start date must be within the last 20 years."

        if postData['duration'] == "-1":
            errors["duration"] = "Please select a duration."
        return errors


class User(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    password = models.CharField(max_length=255)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add = True)
    objects = UserManager()


class Company(models.Model): #one-to-many with photos, subscriptions
    company_name = models.CharField(max_length=255)
    entered_by_admin = models.BooleanField(default=False)
    url = models.TextField(null=True, blank=True)#made text field in case urls are very long
    # to call in templates use:
    # <img src="{% static 'img/'|add:company.img_src %}" alt="{{ company.img_alt }}">
    image_src = models.TextField(default="no_img_available.jpg", null=True, blank=True)#made text field in case img urls are very long
    image_alt = models.CharField(default="no image available",max_length=255, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add = True)


class Subscription(models.Model): #company's / user's subscriptions
    user = models.ForeignKey(
        User, 
        related_name = "subscriptions", 
        on_delete = models.CASCADE
    )
    company = models.ForeignKey(
        Company, 
        related_name = "company_subscriptions", 
        on_delete = models.CASCADE
    )
    account = models.CharField(max_length = 255) #for different accounts from same company
    level = models.CharField(max_length = 255) # for premium, basic, first tier etc
    monthly_rate = models.DecimalField(decimal_places=2, max_digits=9)
    start_date = models.DateField()#can be selected from a clickable calender to deal with formatting
    renew_by_date = models.DateField(null=True, blank=True)
    duration = models.CharField(max_length = 255) #can select from dropdown? auto-renew, 12-month, etc
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add = True)
    objects = SubscriptionManager()#use to validate subscription data


class DataPoint(models.Model):  #connect to subscription (can show one, or all)
    subscription = models.ForeignKey(
        Subscription,
        related_name = "subscription_datapoints",
        on_delete=models.CASCADE,
    )
    monthly_rate = models.DecimalField(decimal_places=2, max_digits=9)
    price_change = models.DecimalField(default = 0.00, decimal_places=2, max_digits=9)
    placed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add = True)



class MessageManager(models.Manager):
    def msg_validator(self, postData):
        errors = {}

        if len(postData['msg_content']) < 8:
                errors['message'] = "Please enter a valid message"
        return errors


class Message(models.Model):
    msg_poster = models.ForeignKey(
        User, 
        related_name = "messages", 
        on_delete = models.CASCADE
    )
    msg_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = MessageManager()


class Comment(models.Model):
    cmt_poster = models.ForeignKey(
        User, 
        related_name = "comments", 
        on_delete = models.CASCADE
    )
    cmt_message = models.ForeignKey(
        Message, 
        related_name = "comments", 
        on_delete = models.CASCADE
    )
    cmt_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


