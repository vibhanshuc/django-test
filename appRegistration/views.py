import csv
from datetime import date, datetime, timedelta
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from instamojo_wrapper import Instamojo

from main.views import commonDisplay, activaPlans, deactivaPlans
from .forms import gymDetailsForm, gymPlansForm, \
    memberActivatePlanForm, memberDetailsForm, staffDetailsForm
from .models import gymDetails, memberDetails, gymPlans, staffDetails


# Create your views here.
@login_required
def dashboard(request):
    # Start: Ensure Gym is registered first
    User = get_user_model()
    gymRegistered = False
    allGymNumbers = gymDetails.objects.all().values('gymUser_id')
    for i in allGymNumbers:
        if i['gymUser_id'] == request.user.id:
            gymRegistered = True
    if not gymRegistered:
        return HttpResponseRedirect("/client/register/")
    # End
    last30Days = datetime.now() + timedelta(days=-30)
    gymObj = gymDetails.objects.filter(gymUser_id=request.user.id).values()
    for elements in gymObj:
        gymNumber = elements['gymNumber']
    totalNumberOfMembers = memberDetails.objects.filter(memberGymNumber_id=gymNumber).count()
    totalActiveMembers = memberDetails.objects.filter(memberGymNumber_id=gymNumber, memberStatus=1).count()
    newMembers = memberDetails.objects.filter(memberGymNumber_id=gymNumber,
                                              memberRegistrationDate__gte=datetime.now() - timedelta(
                                                  days=30)).count()
    maleCount = memberDetails.objects.filter(memberGender='M', memberGymNumber_id=gymNumber).count()
    femaleCount = memberDetails.objects.filter(memberGender='F', memberGymNumber_id=gymNumber).count()
    total_Subscriptions = memberDetails.objects.filter(memberPlanActivationDate__gte=last30Days,
                                                       memberGymNumber_id=gymNumber).values()
    totalCollection = 0
    for items in total_Subscriptions:
        obj = gymPlans.objects.filter(planName=items['memberPlan'], planGymNumber_id=gymNumber).values()
        for i in obj:
            price = i['planPrice']
            totalCollection = totalCollection + price

    # Start: Today's Stats calculation
    totalActiveStaff = staffDetails.objects.filter(staffGymNumber_id=gymNumber, staffStatus=1).count()
    today_newMembers = memberDetails.objects.filter(memberRegistrationDate__gte=(date.today()),
                                                    memberGymNumber_id=gymNumber, ).count()
    today_maleCount = memberDetails.objects.filter(memberRegistrationDate__gte=(date.today()), memberGender='M',
                                                   memberGymNumber_id=gymNumber).count()
    today_femaleCount = memberDetails.objects.filter(memberRegistrationDate__gte=(date.today()), memberGender='F',
                                                     memberGymNumber_id=gymNumber).count()
    today_Subscriptions = memberDetails.objects.filter(memberPlanActivationDate__gte=(date.today()),
                                                       memberGymNumber_id=gymNumber).values()
    todaysCollection = 0
    for items in today_Subscriptions:
        obj = gymPlans.objects.filter(planName=items['memberPlan'], planGymNumber_id=gymNumber).values()
        for i in obj:
            price = i['planPrice']
            todaysCollection = todaysCollection + price

    last30daysExpired = memberDetails.objects.filter(memberPlandExpiryDate__range=(last30Days, datetime.now()),
                                                     memberGymNumber_id=gymNumber).values().order_by(
        'memberPlandExpiryDate').reverse()
    expired_as_dict = []
    for names in last30daysExpired:
        # memberNames.append(names['memberName'])
        # memberContactNumber.append(names['memberContactNumber'])
        my_dict = {
            'memberNames': names['memberName'],
            'memberContactNumber': names['memberContactNumber'],
            'memberEmail': names['memberEmail'],
            'memberPlan': names['memberPlan'],
            'memberPlanActivationDate': names['memberPlanActivationDate'],
            'memberPlandExpiryDate': names['memberPlandExpiryDate']
        }
        expired_as_dict.append(my_dict)
    common = commonDisplay(request)
    context = {
        'totalNumberOfMembers': totalNumberOfMembers,
        'totalActiveMembers': totalActiveMembers,
        'newMembers': newMembers,
        'maleCount': maleCount, 'femaleCount': femaleCount,
        'totalActiveStaff': totalActiveStaff,
        'today_newMembers': today_newMembers,
        'today_maleCount': today_maleCount,
        'today_femaleCount': today_femaleCount,
        'todaysCollection': todaysCollection,
        'totalCollection': totalCollection,
        'expired_as_dict': expired_as_dict
    }
    finalContext = {**common, **context}  # append the dictionaries
    return render(request, 'dashboard.html', context=finalContext)


@login_required
def clientRegistration(request):
    form = gymDetailsForm(request.POST or None)
    emptyDB = True
    x = gymDetails.objects.all().values('gymNumber')
    for getLatestGymNum in x:
        emptyDB = False
        latestGymNum = getLatestGymNum

    if request.POST:
        form = gymDetailsForm(request.POST, request.FILES)
        if form.is_valid():
            save_it = form.save(commit=False)
            save_it.gymRegistrationDate = datetime.now()
            save_it.gymUser_id = request.user.id
            if emptyDB:
                save_it.gymNumber = 1
            else:
                save_it.gymNumber = int(latestGymNum['gymNumber']) + 1
            try:
                form.save()
                messages.success(request, 'SUCCESS! Business Successfully Registered', extra_tags='success')
                return HttpResponseRedirect("/")
            except:
                messages.error(request, 'ERROR! Your have already registered a business in our system',
                               extra_tags='warning')
            return HttpResponseRedirect("/client/register/")
    common = commonDisplay(request)
    context = {'form': form}
    finalContext = {**common, **context}  # append the dictionaries
    return render(request, 'registerClient.html', context=finalContext)


@login_required
def memberRegistration(request):
    # Start: Ensure Gym is registered first
    User = get_user_model()
    userId = User.id
    gymRegistered = False
    allGymNumbers = gymDetails.objects.all().values('gymUser_id')
    for i in allGymNumbers:
        if i['gymUser_id'] == request.user.id:
            gymRegistered = True
    if not gymRegistered:
        return HttpResponseRedirect("/client/register/")
    # End
    form = memberDetailsForm(request.POST or None)
    emptyDB = True
    x = memberDetails.objects.all().values('memberNumber')
    gymObj = gymDetails.objects.filter(gymUser_id=request.user.id).values()
    for elements in gymObj:
        gymNumber = elements['gymNumber']
    latestMemberNum = 0
    for getMemberGymNum in x:
        print('getMemberGymNum is:', getMemberGymNum)
        emptyDB = False
        latestMemberNum = latestMemberNum + 1

    if request.POST:
        form = memberDetailsForm(request.POST)
        # print ('inside post')
        try:
            print(request.POST['selectedPlanName'])
        except:
            messages.error(request,
                           'ERROR! Please select a Plan. If no plans are displayed, please register a plan first.')
            return HttpResponseRedirect("/member/register/")
        # print (request.POST['memberContactNumber'])

        if form.is_valid():
            checkAlreadyRegistered = memberDetails.objects.filter(memberGymNumber_id=gymNumber,
                                                                  memberContactNumber=request.POST[
                                                                      'memberContactNumber'])
            if checkAlreadyRegistered:
                print('Already registered')
                messages.success(request, 'ERROR: Member Already registered')
                return HttpResponseRedirect("/member/register/")
            # for i in checkAlreadyRegistered:
            # 	print (i['memberContactNumber'])
            # 	if int(i['memberContactNumber']) == int(request.POST['memberContactNumber']):
            # 		print ('Already registered')
            # 		messages.success(request,'ERROR: Member Already registered')
            # 		return HttpResponseRedirect("/member/register/")
            print('inside form')
            save_it = form.save(commit=False)
            save_it.memberRegistrationDate = datetime.now()
            save_it.memberGymNumber_id = gymNumber
            save_it.memberPlanActivationDate = datetime.now()
            save_it.memberPlan = request.POST['selectedPlanName']
            Plans = gymPlans.objects.filter(planGymNumber_id=gymNumber,
                                            planName=request.POST['selectedPlanName']).values()
            print('****')
            print(Plans)
            for i in Plans:
                expiryDuration = i['planDuration']
            save_it.memberPlandExpiryDate = datetime.now() + timedelta(days=expiryDuration)
            if emptyDB:
                save_it.memberNumber = 1
            else:
                print('---')
                print(latestMemberNum)
                save_it.memberNumber = latestMemberNum + 1
            form.save()
            messages.success(request, 'Member Registration Successful!')
            return HttpResponseRedirect("/member/register/")
    common = commonDisplay(request)
    activePlans = activaPlans(request)
    context = {'form': form}
    finalContext = {**common, **context, **activePlans}  # append the dictionaries
    return render(request, 'registerMembers.html', context=finalContext)


@login_required
def staffRegistration(request):
    # Start: Ensure Gym is registered first
    User = get_user_model()
    userId = User.id
    gymRegistered = False
    allGymNumbers = gymDetails.objects.all().values('gymUser_id')
    for i in allGymNumbers:
        print('---------')
        print(i['gymUser_id'])
        print(request.user.id)
        if i['gymUser_id'] == request.user.id:
            gymRegistered = True
    if not gymRegistered:
        return HttpResponseRedirect("/client/register/")
    # End
    form = staffDetailsForm(request.POST or None)
    emptyDB = True
    x = staffDetails.objects.all().values('staffNumber')
    gymObj = gymDetails.objects.filter(gymUser_id=request.user.id).values()
    for elements in gymObj:
        gymNumber = elements['gymNumber']
    latestMemberNum = 0
    for getMemberGymNum in x:
        print('getMemberGymNum is:', getMemberGymNum)
        emptyDB = False
        latestMemberNum = latestMemberNum + 1

    if request.POST:
        form = staffDetailsForm(request.POST)
        print('inside post')
        if form.is_valid():
            print('inside form')
            save_it = form.save(commit=False)
            save_it.staffRegistrationDate = datetime.now()
            save_it.staffGymNumber_id = gymNumber
            if emptyDB:
                save_it.staffNumber = 1
            else:
                print('---')
                print(latestMemberNum)
                save_it.staffNumber = latestMemberNum + 1
            form.save()
            messages.success(request, 'Staff Registration Successful')
            return HttpResponseRedirect("/staff/register/")
    common = commonDisplay(request)
    context = {'form': form}
    finalContext = {**common, **context}  # append the dictionaries
    return render(request, 'registerStaffs.html', context=finalContext)


@login_required
def clientPlans(request):
    # Start: Ensure Gym is registered first
    User = get_user_model()
    userId = User.id
    gymRegistered = False
    allGymNumbers = gymDetails.objects.all().values('gymUser_id')
    for i in allGymNumbers:
        print('---------')
        print(i['gymUser_id'])
        print(request.user.id)
        if i['gymUser_id'] == request.user.id:
            gymRegistered = True
    if not gymRegistered:
        return HttpResponseRedirect("/client/register/")
    # End
    common = commonDisplay(request)
    form = gymPlansForm(request.POST or None)
    if request.POST:
        if form.is_valid():
            save_it = form.save(commit=False)
            gymObj = gymDetails.objects.filter(gymUser_id=request.user.id).values()
            for elements in gymObj:
                gymNumber = elements['gymNumber']
                save_it.planGymNumber_id = gymNumber
            form.save()
            print('SAVED!!!!!!!!!')
            return HttpResponseRedirect("/client/plans/")
    common = commonDisplay(request)
    activePlans = activaPlans(request)
    context = {'form': form}
    deactivePlans = deactivaPlans(request)

    finalContext = {**common, **context, **activePlans, **deactivePlans}  # append the dictionaries
    return render(request, 'clientPlans.html', context=finalContext)


@login_required
def clientActivatePlan(request):
    # Start: Ensure Gym is registered first
    User = get_user_model()
    userId = User.id
    gymRegistered = False
    allGymNumbers = gymDetails.objects.all().values('gymUser_id')
    for i in allGymNumbers:
        if i['gymUser_id'] == request.user.id:
            gymRegistered = True
    if not gymRegistered:
        return HttpResponseRedirect("/client/register/")
    # End

    form = memberActivatePlanForm(request.POST or None)
    context = {'form': form, 'buttontext': 'Submit'}

    if form.is_valid():
        input = form.cleaned_data['Search']
        print(input)
        gymObj = gymDetails.objects.filter(gymUser_id=request.user.id).values()
        for i in gymObj:
            gymNumber = i['gymNumber']

        if 'selectedPlanName' in request.POST:
            print(request.POST['selectedPlanName'])
            gymObj = gymDetails.objects.filter(gymUser_id=request.user.id).values()
            for elements in gymObj:
                gymNumber = elements['gymNumber']
            Plans = gymPlans.objects.filter(planGymNumber_id=gymNumber,
                                            planName=request.POST['selectedPlanName']).values()
            print('****')
            print(Plans)
            for i in Plans:
                expiryDuration = i['planDuration']
                print('.............')
                print(expiryDuration)

            userData = memberDetails.objects.filter(memberContactNumber=input,
                                                    memberGymNumber_id=gymNumber).update(
                memberPlanActivationDate=datetime.now(),
                memberPlan=request.POST['selectedPlanName'],
                memberPlandExpiryDate=datetime.now() + timedelta(days=expiryDuration))
            messages.success(request, 'Updated successfully')
        member = memberDetails.objects.filter(memberContactNumber=input, memberGymNumber_id=gymNumber).values()
        if not member:
            messages.error(request, 'ERROR! Number not registered in system. Please check the entered number.')
        for i in member:
            name = i['memberName']
            memberEmail = i['memberEmail']
            registrationDate = i['memberRegistrationDate']
            status = i['memberStatus']
            memberId = i['memberGymNumber_id']
            activeMemberPlan = i['memberPlan']
            memberPlanActivationDate = i['memberPlanActivationDate']
            memberPlandExpiryDate = i['memberPlandExpiryDate']
            buttontext = 'Update'

            context = {'form': form, 'name': name, 'memberEmail': memberEmail, 'registrationDate': registrationDate,
                       'status': status, 'memberId': memberId, 'activeMemberPlan': activeMemberPlan,
                       'memberPlanActivationDate': memberPlanActivationDate,
                       'memberPlandExpiryDate': memberPlandExpiryDate, 'buttontext': buttontext}

    common = commonDisplay(request)
    activePlans = activaPlans(request)

    finalContext = {**common, **context, **activePlans}  # append the dictionaries
    return render(request, 'gymPlans.html', context=finalContext)


@login_required
def export_users_csv(request):
    # Start: Ensure Gym is registered first
    User = get_user_model()
    userId = User.id
    gymRegistered = False
    allGymNumbers = gymDetails.objects.all().values('gymUser_id')
    for i in allGymNumbers:
        if i['gymUser_id'] == request.user.id:
            gymRegistered = True
    if not gymRegistered:
        return HttpResponseRedirect("/client/register/")
    # End
    User = get_user_model()
    response = HttpResponse(content_type='text/csv')
    gymObj = gymDetails.objects.filter(gymUser_id=request.user.id).values()
    for elements in gymObj:
        gymNumber = elements['gymNumber']
    response['Content-Disposition'] = 'attachment; filename="users.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Father Name', 'Date Of Birth', 'Address 1', 'City 1', 'Pincode 1', 'Address 2', 'City 2',
                     'Pincode 2', 'Contact Number', 'Identification Mark', 'Height', 'Weight' 'Emergency Contact',
                     'Email', 'Registration Date', 'Member Number', 'Status', 'Gender', 'Subscription Plan',
                     'Last Plan Activation Date', 'Plan Expiry Date'])

    users = memberDetails.objects.filter(memberGymNumber_id=gymNumber).values_list('memberName',
                                                                                   'fatherName',
                                                                                   'dateOfBirth',
                                                                                   'memberAddress1',
                                                                                   'memberCity1',
                                                                                   'memberPincode1',
                                                                                   'memberAddress2',
                                                                                   'memberCity2',
                                                                                   'memberPincode2',
                                                                                   'memberContactNumber',
                                                                                   'identificationMark',
                                                                                   'memberHeight',
                                                                                   'memberWeight',
                                                                                   'memberEmergencyNumber',
                                                                                   'memberEmail',
                                                                                   'memberRegistrationDate',
                                                                                   'memberNumber',
                                                                                   'memberStatus',
                                                                                   'memberGender',
                                                                                   'memberPlan',
                                                                                   'memberPlanActivationDate',
                                                                                   'memberPlandExpiryDate')
    for user in users:
        writer.writerow(user)
    return response


@login_required
def export_monthly_report(request):
    gymRegistered = False
    allGymNumbers = gymDetails.objects.all().values('gymUser_id')
    for i in allGymNumbers:
        if i['gymUser_id'] == request.user.id:
            gymRegistered = True
    if not gymRegistered:
        return HttpResponseRedirect("/client/register/")
    currentMonthStarting = datetime.today().replace(day=1)
    gymObj = gymDetails.objects.filter(gymUser_id=request.user.id).values()
    for elements in gymObj:
        gymNumber = elements['gymNumber']
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Father Name', 'Date Of Birth', 'Address 1', 'City 1', 'Pincode 1', 'Address 2', 'City 2',
                     'Pincode 2', 'Contact Number', 'Identification Mark', 'Height', 'Weight' 'Emergency Contact',
                     'Email', 'Registration Date', 'Member Number', 'Status', 'Gender', 'Subscription Plan',
                     'Last Plan Activation Date', 'Plan Expiry Date'])

    users = memberDetails.objects.filter(memberPlanActivationDate__gte=currentMonthStarting,
                                         memberGymNumber_id=gymNumber).values_list('memberName',
                                                                                   'fatherName',
                                                                                   'dateOfBirth',
                                                                                   'memberAddress1',
                                                                                   'memberCity1',
                                                                                   'memberPincode1',
                                                                                   'memberAddress2',
                                                                                   'memberCity2',
                                                                                   'memberPincode2',
                                                                                   'memberContactNumber',
                                                                                   'identificationMark',
                                                                                   'memberHeight',
                                                                                   'memberWeight',
                                                                                   'memberEmergencyNumber',
                                                                                   'memberEmail',
                                                                                   'memberRegistrationDate',
                                                                                   'memberNumber',
                                                                                   'memberStatus',
                                                                                   'memberGender',
                                                                                   'memberPlan',
                                                                                   'memberPlanActivationDate',
                                                                                   'memberPlandExpiryDate')
    for user in users:
        writer.writerow(user)

    return response


@login_required
def current_month_income(request):
    # Start: Ensure Gym is registered first
    User = get_user_model()
    userId = User.id
    gymRegistered = False
    allGymNumbers = gymDetails.objects.all().values('gymUser_id')
    for i in allGymNumbers:
        if i['gymUser_id'] == request.user.id:
            gymRegistered = True
    if not gymRegistered:
        return HttpResponseRedirect("/client/register/")
    # End
    User = get_user_model()
    currentMonthStarting = datetime.today().replace(day=1)
    gymObj = gymDetails.objects.filter(gymUser_id=request.user.id).values()
    for elements in gymObj:
        gymNumber = elements['gymNumber']
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Contact Number', 'Email', 'Registration Date', 'Member Number',
                     'Subscription Plan', 'Last Plan Activation Date', 'Plan Expiry Date'])

    users = memberDetails.objects.filter(memberPlanActivationDate__gte=(currentMonthStarting),
                                         memberGymNumber_id=gymNumber).values_list('memberName', \
                                                                                   'memberContactNumber', 'memberEmail',
                                                                                   'memberRegistrationDate', \
                                                                                   'memberNumber', 'memberPlan',
                                                                                   'memberPlanActivationDate',
                                                                                   'memberPlandExpiryDate')
    for user in users:
        writer.writerow(user)

    thisMonth_Subscriptions = memberDetails.objects.filter(memberPlanActivationDate__gte=(currentMonthStarting),
                                                           memberGymNumber_id=gymNumber).values()
    thisMonthCollection = 0
    for items in thisMonth_Subscriptions:
        print(items['memberPlan'])
        obj = gymPlans.objects.filter(planName=items['memberPlan'], planGymNumber_id=gymNumber).values()
        for i in obj:
            price = i['planPrice']
            print(price)
            thisMonthCollection = thisMonthCollection + price
    writer.writerow(['', '', '', ' ', ' ',
                     'Total Income= ' + str(thisMonthCollection), '', ''])

    return response


@login_required
def last_month_income(request):
    # Start: Ensure Gym is registered first
    User = get_user_model()
    userId = User.id
    gymRegistered = False
    allGymNumbers = gymDetails.objects.all().values('gymUser_id')
    for i in allGymNumbers:
        if i['gymUser_id'] == request.user.id:
            gymRegistered = True
    if not gymRegistered:
        return HttpResponseRedirect("/client/register/")
    # End
    User = get_user_model()
    currentMonthStarting = datetime.today().replace(day=1)
    lastMonthSameday = datetime.now() + timedelta(days=-30)
    lastMonth = lastMonthSameday.replace(day=1)
    gymObj = gymDetails.objects.filter(gymUser_id=request.user.id).values()
    for elements in gymObj:
        gymNumber = elements['gymNumber']
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Contact Number', 'Email', 'Registration Date', 'Member Number',
                     'Subscription Plan', 'Last Plan Activation Date', 'Plan Expiry Date'])

    users = memberDetails.objects.filter(memberPlanActivationDate__gte=(lastMonth),
                                         memberPlanActivationDate__lte=(currentMonthStarting),
                                         memberGymNumber_id=gymNumber).values_list('memberName', \
                                                                                   'memberContactNumber', 'memberEmail',
                                                                                   'memberRegistrationDate', \
                                                                                   'memberNumber', 'memberPlan',
                                                                                   'memberPlanActivationDate',
                                                                                   'memberPlandExpiryDate')
    for user in users:
        writer.writerow(user)

    thisMonth_Subscriptions = memberDetails.objects.filter(memberPlanActivationDate__gte=(lastMonth),
                                                           memberPlanActivationDate__lte=(currentMonthStarting),
                                                           memberGymNumber_id=gymNumber).values()
    thisMonthCollection = 0
    for items in thisMonth_Subscriptions:
        print(items['memberPlan'])
        obj = gymPlans.objects.filter(planName=items['memberPlan'], planGymNumber_id=gymNumber).values()
        for i in obj:
            price = i['planPrice']
            print(price)
            thisMonthCollection = thisMonthCollection + price
    writer.writerow(['', '', '', ' ', ' ',
                     'Total Income= ' + str(thisMonthCollection), '', ''])
    return response


@login_required
def total_income(request):
    # Start: Ensure Gym is registered first
    User = get_user_model()
    userId = User.id
    gymRegistered = False
    allGymNumbers = gymDetails.objects.all().values('gymUser_id')
    for i in allGymNumbers:
        if i['gymUser_id'] == request.user.id:
            gymRegistered = True
    if not gymRegistered:
        return HttpResponseRedirect("/client/register/")
    # End
    User = get_user_model()
    gymObj = gymDetails.objects.filter(gymUser_id=request.user.id).values()
    for elements in gymObj:
        gymNumber = elements['gymNumber']
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Contact Number', 'Email', 'Registration Date', 'Member Number',
                     'Subscription Plan', 'Last Plan Activation Date', 'Plan Expiry Date'])

    users = memberDetails.objects.filter(memberGymNumber_id=gymNumber).values_list('memberName', \
                                                                                   'memberContactNumber', 'memberEmail',
                                                                                   'memberRegistrationDate', \
                                                                                   'memberNumber', 'memberPlan',
                                                                                   'memberPlanActivationDate',
                                                                                   'memberPlandExpiryDate')
    for user in users:
        writer.writerow(user)

    thisMonth_Subscriptions = memberDetails.objects.filter(memberGymNumber_id=gymNumber).values()
    thisMonthCollection = 0
    for items in thisMonth_Subscriptions:
        print(items['memberPlan'])
        obj = gymPlans.objects.filter(planName=items['memberPlan'], planGymNumber_id=gymNumber).values()
        for i in obj:
            price = i['planPrice']
            print(price)
            thisMonthCollection = thisMonthCollection + price
    writer.writerow(['', '', '', ' ', ' ',
                     'Total Income= ' + str(thisMonthCollection), '', ''])
    return response


@login_required
def usersearch(request):
    # Start: Ensure Gym is registered first
    User = get_user_model()
    userId = User.id
    gymRegistered = False
    allGymNumbers = gymDetails.objects.all().values('gymUser_id')
    for i in allGymNumbers:
        if i['gymUser_id'] == request.user.id:
            gymRegistered = True
    if not gymRegistered:
        return HttpResponseRedirect("/client/register/")
    # End

    last30Days = datetime.now() + timedelta(days=-30)
    print('last30days is:', last30Days)
    gymObj = gymDetails.objects.filter(gymUser_id=request.user.id).values()
    for elements in gymObj:
        gymNumber = elements['gymNumber']
    totalNumberOfMembers = memberDetails.objects.filter(memberGymNumber_id=gymNumber).count()
    totalActiveMembers = memberDetails.objects.filter(memberGymNumber_id=gymNumber, memberStatus=1).count()
    newMembers = memberDetails.objects.filter(memberGymNumber_id=gymNumber,
                                              memberRegistrationDate__gte=datetime.now() - timedelta(
                                                  days=30)).count()
    maleCount = memberDetails.objects.filter(memberGender='M', memberGymNumber_id=gymNumber).count()
    femaleCount = memberDetails.objects.filter(memberGender='F', memberGymNumber_id=gymNumber).count()

    form = memberActivatePlanForm(request.POST or None)
    context = {'form': form, 'totalNumberOfMembers': totalNumberOfMembers, 'totalActiveMembers': totalActiveMembers,
               'maleCount': maleCount, 'femaleCount': femaleCount, 'newMembers': newMembers}

    if form.is_valid():
        input = form.cleaned_data['Search']
        print(input)
        gymObj = gymDetails.objects.filter(gymUser_id=request.user.id).values()
        for i in gymObj:
            gymNumber = i['gymNumber']
        try:
            member = memberDetails.objects.filter(memberContactNumber=input, memberGymNumber_id=gymNumber).values()
            if not member:
                messages.error(request, 'ERROR! Number not registered in system. Please check the entered number.')
            for i in member:
                name = i['memberName']
                memberEmail = i['memberEmail']
                memberAddress = i['memberAddress']
                memberCity = i['memberCity']
                memberPincode = i['memberPincode']
                memberContactNumber = i['memberContactNumber']
                memberEmergencyNumber = i['memberEmergencyNumber']
                registrationDate = i['memberRegistrationDate']
                status = i['memberStatus']
                memberId = i['memberNumber']
                memberGender = i['memberGender']
                activeMemberPlan = i['memberPlan']
                memberPlanActivationDate = i['memberPlanActivationDate']
                memberPlandExpiryDate = i['memberPlandExpiryDate']
                buttontext = 'Update'

                context = {'form': form, 'name': name, 'memberEmail': memberEmail, 'registrationDate': registrationDate,
                           'status': status, 'memberId': memberId, 'activeMemberPlan': activeMemberPlan,
                           'memberPlanActivationDate': memberPlanActivationDate,
                           'memberAddress': memberAddress, 'memberCity': memberCity, 'memberPincode': memberPincode,
                           'memberContactNumber': memberContactNumber,
                           'memberEmergencyNumber': memberEmergencyNumber, 'memberGender': memberGender,
                           'memberPlandExpiryDate': memberPlandExpiryDate, 'buttontext': buttontext,
                           'totalNumberOfMembers': totalNumberOfMembers, 'totalActiveMembers': totalActiveMembers,
                           'maleCount': maleCount, 'femaleCount': femaleCount, 'newMembers': newMembers}
        except:
            messages.error(request,
                           'ERROR! Please enter valid contact number only. You have entered invalid charactered.')

    common = commonDisplay(request)
    activePlans = activaPlans(request)

    finalContext = {**common, **context, **activePlans}  # append the dictionaries
    return render(request, 'searchUser.html', context=finalContext)


@login_required
def staffsearch(request):
    # Start: Ensure Gym is registered first
    User = get_user_model()
    userId = User.id
    gymRegistered = False
    allGymNumbers = gymDetails.objects.all().values('gymUser_id')
    for i in allGymNumbers:
        if i['gymUser_id'] == request.user.id:
            gymRegistered = True
    if not gymRegistered:
        return HttpResponseRedirect("/client/register/")
    # End

    last30Days = datetime.now() + timedelta(days=-30)
    print('last30days is:', last30Days)
    gymObj = gymDetails.objects.filter(gymUser_id=request.user.id).values()
    for elements in gymObj:
        gymNumber = elements['gymNumber']
    totalNumberOfstaffs = staffDetails.objects.filter(staffGymNumber_id=gymNumber).count()
    totalActivestaffs = staffDetails.objects.filter(staffGymNumber_id=gymNumber, staffStatus=1).count()
    newstaffs = staffDetails.objects.filter(staffGymNumber_id=gymNumber,
                                            staffRegistrationDate__gte=datetime.now() - timedelta(
                                                days=30)).count()
    maleCount = staffDetails.objects.filter(staffGender='M', staffGymNumber_id=gymNumber).count()
    femaleCount = staffDetails.objects.filter(staffGender='F', staffGymNumber_id=gymNumber).count()

    form = memberActivatePlanForm(request.POST or None)
    context = {'form': form, 'totalNumberOfstaffs': totalNumberOfstaffs, 'totalActivestaffs': totalActivestaffs,
               'maleCount': maleCount, 'femaleCount': femaleCount, 'newstaffs': newstaffs}

    if form.is_valid():
        input = form.cleaned_data['Search']
        print(input)
        gymObj = gymDetails.objects.filter(gymUser_id=request.user.id).values()
        for i in gymObj:
            gymNumber = i['gymNumber']
        try:
            staff = staffDetails.objects.filter(staffContactNumber=input, staffGymNumber_id=gymNumber).values()
            if not staff:
                messages.error(request, 'ERROR! Number not registered in system. Please check the entered number.')
            for i in staff:
                name = i['staffName']
                staffEmail = i['staffEmail']
                staffAddress = i['staffAddress']
                staffCity = i['staffCity']
                staffPincode = i['staffPincode']
                staffContactNumber = i['staffContactNumber']
                staffEmergencyNumber = i['staffEmergencyNumber']
                registrationDate = i['staffRegistrationDate']
                status = i['staffStatus']
                staffId = i['staffNumber']
                staffGender = i['staffGender']

                context = {'form': form, 'name': name, 'staffEmail': staffEmail, 'registrationDate': registrationDate,
                           'status': status, 'staffId': staffId,
                           'staffAddress': staffAddress, 'staffCity': staffCity, 'staffPincode': staffPincode,
                           'staffContactNumber': staffContactNumber,
                           'staffEmergencyNumber': staffEmergencyNumber, 'staffGender': staffGender,
                           'totalNumberOfstaffs': totalNumberOfstaffs, 'totalActivestaffs': totalActivestaffs,
                           'maleCount': maleCount, 'femaleCount': femaleCount, 'newstaffs': newstaffs}
        except:
            messages.error(request,
                           'ERROR! Please enter valid contact number only. You have entered invalid charactered.')

    common = commonDisplay(request)
    activePlans = activaPlans(request)

    finalContext = {**common, **context, **activePlans}  # append the dictionaries
    return render(request, 'staffSearch.html', context=finalContext)


@login_required
def edituser(request):
    # Start: Ensure Gym is registered first
    User = get_user_model()
    userId = User.id
    gymRegistered = False
    found = False
    my_record = None
    title = 'Member Search'
    buttontext = 'Search'
    allGymNumbers = gymDetails.objects.all().values('gymUser_id')
    for i in allGymNumbers:
        if i['gymUser_id'] == request.user.id:
            gymRegistered = True
    if not gymRegistered:
        return HttpResponseRedirect("/client/register/")
    # End
    # Member stats
    last30Days = datetime.now() + timedelta(days=-30)
    print('last30days is:', last30Days)
    gymObj = gymDetails.objects.filter(gymUser_id=request.user.id).values()
    for elements in gymObj:
        gymNumber = elements['gymNumber']
    totalNumberOfMembers = memberDetails.objects.filter(memberGymNumber_id=gymNumber).count()
    totalActiveMembers = memberDetails.objects.filter(memberGymNumber_id=gymNumber, memberStatus=1).count()
    newMembers = memberDetails.objects.filter(memberGymNumber_id=gymNumber,
                                              memberRegistrationDate__gte=datetime.now() - timedelta(
                                                  days=30)).count()
    maleCount = memberDetails.objects.filter(memberGender='M', memberGymNumber_id=gymNumber).count()
    femaleCount = memberDetails.objects.filter(memberGender='F', memberGymNumber_id=gymNumber).count()

    # End
    gymObj = gymDetails.objects.filter(gymUser_id=request.user.id).values()
    for elements in gymObj:
        gymNumber = elements['gymNumber']
    print(request.POST)
    form = memberActivatePlanForm(request.POST or None)
    if 'deleteuser' in request.POST:
        input = request.POST['memberContactNumber']
        my_record = memberDetails.objects.get(memberContactNumber=input, memberGymNumber_id=gymNumber)
        form = memberDetailsForm(request.POST, instance=my_record)
        if form.is_valid():
            print('deleting user')
            form.fields['memberContactNumber'].widget.attrs['readonly'] = True
            print('input is:', input)
            memberDetails.objects.filter(memberContactNumber=input, memberGymNumber_id=gymNumber).delete()
            messages.success(request, 'Member DELETED successfully.')
    elif 'Search' in request.POST:
        print('???????????')
        form = memberActivatePlanForm(request.POST or None)
        if form.is_valid():
            input = form.cleaned_data['Search']
            print(input)
            try:
                my_record = memberDetails.objects.get(memberContactNumber=input, memberGymNumber_id=gymNumber)
                form = memberDetailsForm(instance=my_record)
                form.fields['memberContactNumber'].widget.attrs['readonly'] = True
                title = 'Edit or Delete Member'
                buttontext = 'Update'
            except:
                messages.error(request, 'ERROR! Member not found.')
    elif 'memberName' in request.POST:
        try:
            input = request.POST['memberContactNumber']

            my_record = memberDetails.objects.get(memberContactNumber=input, memberGymNumber_id=gymNumber)
            form = memberDetailsForm(request.POST, instance=my_record)
            if form.is_valid():
                save_it = form.save(commit=False)
                form.save()
                form.fields['memberContactNumber'].widget.attrs['readonly'] = True
                messages.success(request, 'Member details updated successfully.')
                title = 'Edit or Delete Member'

        except:
            messages.error(request, 'ERROR! Member contact number cannot be edited.')
            title = 'Member Search'

    context = {'form': form, 'title': title, 'buttontext': buttontext, 'totalNumberOfMembers': totalNumberOfMembers,
               'totalActiveMembers': totalActiveMembers,
               'maleCount': maleCount, 'femaleCount': femaleCount, 'newMembers': newMembers}
    common = commonDisplay(request)
    activePlans = activaPlans(request)

    finalContext = {**common, **context, **activePlans}  # append the dictionaries
    return render(request, 'edituser.html', context=finalContext)


@login_required
def clientEdit(request):
    my_record = gymDetails.objects.get(gymUser_id=request.user.id)
    form = gymDetailsForm(instance=my_record)
    if request.POST:
        print('inside')
        form = gymDetailsForm(request.POST, request.FILES, instance=my_record)
        save_it = form.save(commit=False)
        form.save()
        messages.success(request, 'Business details updated successfully.')
    common = commonDisplay(request)
    context = {'form': form}
    finalContext = {**common, **context}  # append the dictionaries
    return render(request, 'clientEdit.html', context=finalContext)


@login_required
def deactivePlan(request):
    # Start: Ensure Gym is registered first
    User = get_user_model()
    userId = User.id
    gymRegistered = False
    found = False
    my_record = None
    title = 'Plan Search'
    buttontext = 'Search'
    allGymNumbers = gymDetails.objects.all().values('gymUser_id')
    for i in allGymNumbers:
        if i['gymUser_id'] == request.user.id:
            gymRegistered = True
    if not gymRegistered:
        return HttpResponseRedirect("/client/register/")
    # End

    gymObj = gymDetails.objects.filter(gymUser_id=request.user.id).values()
    for elements in gymObj:
        gymNumber = elements['gymNumber']
    print(request.POST)
    form = memberActivatePlanForm(request.POST or None)
    if 'Search' in request.POST:
        print('???????????')
        print('yes')

        form = memberActivatePlanForm(request.POST or None)
        if form.is_valid():
            print('inside form')
            input = form.cleaned_data['Search']
            try:
                my_record = gymPlans.objects.get(planName__iexact=input, planGymNumber_id=gymNumber)
                form = gymPlansForm(instance=my_record)
                form.fields['planName'].widget.attrs['readonly'] = True
                form.fields['planDuration'].widget.attrs['readonly'] = True
                form.fields['planPrice'].widget.attrs['readonly'] = True
                form.fields['planDescription'].widget.attrs['readonly'] = True
                title = 'Deactivate Plan'
                buttontext = 'Deactivate Plan'
            except:
                messages.error(request, 'ERROR! Plan not found. Please check the plan name entered.')
    elif 'deactivate' in request.POST:
        try:
            input = request.POST['planName']

            my_record = gymPlans.objects.get(planName__iexact=input, planGymNumber_id=gymNumber)
            form = gymPlansForm(request.POST, instance=my_record)
            if form.is_valid():
                save_it = form.save(commit=False)
                form.save()
                form.fields['planName'].widget.attrs['readonly'] = True
                form.fields['planDuration'].widget.attrs['readonly'] = True
                form.fields['planPrice'].widget.attrs['readonly'] = True
                form.fields['planDescription'].widget.attrs['readonly'] = True
                messages.success(request, 'Plan updated successfully.')
                title = 'Deactivate Plan'
                buttontext = 'Deactivate Plan'
        except:
            messages.error(request, 'ERROR! Plan Name/Title cannot be edited. Please create a new plan.')
            title = 'Member Search'

    context = {'form': form, 'title': title, 'buttontext': buttontext}
    common = commonDisplay(request)
    activePlans = activaPlans(request)
    deactivePlans = deactivaPlans(request)

    finalContext = {**common, **context, **activePlans, **deactivePlans}  # append the dictionaries
    return render(request, 'deactivatePlan.html', context=finalContext)


@login_required
def deactiveStaff(request):
    # Start: Ensure Gym is registered first
    User = get_user_model()
    userId = User.id
    gymRegistered = False
    found = False
    my_record = None
    title = 'Staff Search'
    buttontext = 'Search'
    allGymNumbers = gymDetails.objects.all().values('gymUser_id')
    for i in allGymNumbers:
        if i['gymUser_id'] == request.user.id:
            gymRegistered = True
    if not gymRegistered:
        return HttpResponseRedirect("/client/register/")
    # End

    gymObj = gymDetails.objects.filter(gymUser_id=request.user.id).values()
    for elements in gymObj:
        gymNumber = elements['gymNumber']
    form = memberActivatePlanForm(request.POST or None)
    if 'Search' in request.POST:
        print('???????????')
        print('yes')

        form = memberActivatePlanForm(request.POST or None)
        if form.is_valid():
            print('inside form')
            input = form.cleaned_data['Search']
            print(input)
            try:
                my_record = staffDetails.objects.get(staffContactNumber=input, staffGymNumber_id=gymNumber)
                form = staffDetailsForm(instance=my_record)
                form.fields['staffContactNumber'].widget.attrs['readonly'] = True

                title = 'Edit Staff Details'
                buttontext = "Update"
            except:
                messages.error(request, 'ERROR! Plan not found. Please check the plan name entered.')
    elif 'deactivate' in request.POST:
        try:
            input = request.POST['staffContactNumber']

            my_record = staffDetails.objects.get(staffContactNumber=input, staffGymNumber_id=gymNumber)
            form = staffDetailsForm(request.POST, instance=my_record)
            if form.is_valid():
                save_it = form.save(commit=False)
                form.fields['staffContactNumber'].widget.attrs['readonly'] = True
                form.save()
                # form.fields['planName'].widget.attrs['readonly'] = True
                # form.fields['planDuration'].widget.attrs['readonly'] = True
                # form.fields['planPrice'].widget.attrs['readonly'] = True
                # form.fields['planDescription'].widget.attrs['readonly'] = True
                messages.success(request, 'Staff updated successfully.')
                title = 'Edit Staff Details'
                buttontext = "Update"
        except:
            messages.error(request, 'ERROR! Plan Name/Title cannot be edited. Please create a new plan.')
            title = 'Staff Search'
            buttontext = "Search"

    context = {'form': form, 'title': title, 'buttontext': buttontext}
    common = commonDisplay(request)
    activePlans = activaPlans(request)
    deactivePlans = deactivaPlans(request)

    finalContext = {**common, **context, **activePlans, **deactivePlans}  # append the dictionaries
    return render(request, 'editStaff.html', context=finalContext)


def payment(request):
    api = Instamojo(api_key='',
                    auth_token='',
                    endpoint='https://test.instamojo.com/api/1.1/')

    # Create a new Payment Request
    response = api.payment_request_create(
        amount='3499',
        purpose='FIFA 164',
        send_email=True,
        email="foo@example.com",
        buyer_name='abhi',
        phone='9886330471',
        redirect_url="http://127.0.0.1:8000/sucess/",
    )
    # print the long URL of the payment request.
    print(response['payment_request']['longurl'])
    # print the unique ID(or payment request ID)
    print(response['payment_request']['id'])
    context = {}
    common = commonDisplay(request)
    activePlans = activaPlans(request)
    deactivePlans = deactivaPlans(request)

    finalContext = {**common, **context, **activePlans, **deactivePlans}  # append the dictionaries
    return HttpResponseRedirect(response['payment_request']['longurl'])


def billing(request):
    api = Instamojo(api_key='',
                    auth_token='',
                    endpoint='https://test.instamojo.com/api/1.1/')

    gymObj = gymDetails.objects.filter(gymUser_id=request.user.id).values()
    for elements in gymObj:
        gymNumber = elements['gymNumber']
        gymContactNum = elements['gymContactNumber']
        gymEmail = elements['gymEmail']
    userId = request.user.id
    print('UserID is:', userId)
    # Update status of users whose subscrition plans have expired
    totalActiveMembers = memberDetails.objects.filter(memberGymNumber_id=gymNumber, memberStatus=1).count()
    amountPerMember = 60
    billableAmount = totalActiveMembers * amountPerMember
    # End
    # Create a new Payment Request
    # response = api.payment_request_create(
    #     amount=billableAmount,
    #     purpose='Gym_' + str(gymNumber) + '_' + str(datetime.today()),
    #     send_email=True,
    #     email=gymEmail,
    #     buyer_name=user + '_id:' + str(userId),
    #     # phone=gymContactNum,
    #     redirect_url="http://127.0.0.1:8000/sucess/",
    # )

    # Create a new Payment Request
    # response = api.payment_request_create(
    #     amount=billableAmount,
    #     purpose='Gym_'+str(gymNumber)+str(datetime.date.today()),
    #     send_email=True,
    #     email=gymEmail,
    #     buyer_name=user+'_id:'+str(userId),
    #     phone=gymContactNum,
    #    	redirect_url="http://127.0.0.1:8000/sucess/",
    #     )
    # print the long URL of the payment request.
    context = {'totalActiveMembers': totalActiveMembers,
               'billableAmount': billableAmount,
               'amountPerMember': amountPerMember,
               'payment_link': ''}
    common = commonDisplay(request)
    activePlans = activaPlans(request)
    deactivePlans = deactivaPlans(request)

    finalContext = {**common, **context, **activePlans, **deactivePlans}  # append the dictionaries
    return render(request, 'billing.html', context=finalContext)
