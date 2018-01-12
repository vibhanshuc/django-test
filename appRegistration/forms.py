from appRegistration.models import gymDetails, memberDetails, gymPlans, staffDetails
from django import forms


class gymDetailsForm(forms.ModelForm):
    class Meta:
        model = gymDetails
        fields = '__all__'
        exclude = ['gymRegistrationDate', 'gymNumber', 'gymUser']


class memberDetailsForm(forms.ModelForm):
    class Meta:
        model = memberDetails
        fields = '__all__'
        exclude = ['memberStatus', 'memberNumber', 'memberRegistrationDate', 'memberGymNumber',
                   'memberPlanActivationDate', 'memberPlandExpiryDate', 'memberPlan']


class gymPlansForm(forms.ModelForm):
    class Meta:
        model = gymPlans
        fields = '__all__'
        exclude = ['planGymNumber']


class memberActivatePlanForm(forms.Form):
    Search = forms.CharField(required=True)


class staffDetailsForm(forms.ModelForm):
    class Meta:
        model = staffDetails
        fields = '__all__'
        exclude = ['staffNumber', 'staffRegistrationDate', 'staffGymNumber']
