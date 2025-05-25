# forms.py
from django import forms
from .models import MangoThreat, Location, MangoTree, SurveillanceRecord
from django.contrib.auth.models import User

class MangoThreatForm(forms.ModelForm):
    class Meta:
        model = MangoThreat
        fields = ['name', 'description', 'details', 'threat_type', 'risk_level', 'image']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter threat name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief description of the threat'
            }),
            'details': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Detailed information about the threat'
            }),
            'threat_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'risk_level': forms.Select(attrs={
                'class': 'form-control'
            }),
            'image': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Image filename (e.g., threat.png)'
            })
        }
        
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            # Check for duplicate names (excluding current instance if editing)
            threat_id = self.instance.id if self.instance else None
            if MangoThreat.objects.filter(name__iexact=name).exclude(id=threat_id).exists():
                raise forms.ValidationError("A threat with this name already exists.")
        return name


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['name', 'address', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Location name'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Full address'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Description of the location'
            })
        }


class MangoTreeForm(forms.ModelForm):
    class Meta:
        model = MangoTree
        fields = ['location', 'tree_id', 'age', 'variety']
        widgets = {
            'location': forms.Select(attrs={
                'class': 'form-control'
            }),
            'tree_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Unique tree identifier'
            }),
            'age': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Age in years',
                'min': 1
            }),
            'variety': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Mango variety'
            })
        }
        
    def clean_tree_id(self):
        tree_id = self.cleaned_data.get('tree_id')
        if tree_id:
            # Check for duplicate tree IDs (excluding current instance if editing)
            tree_pk = self.instance.pk if self.instance else None
            if MangoTree.objects.filter(tree_id=tree_id).exclude(pk=tree_pk).exists():
                raise forms.ValidationError("A tree with this ID already exists.")
        return tree_id


class SurveillanceRecordForm(forms.ModelForm):
    class Meta:
        model = SurveillanceRecord
        fields = ['location', 'date', 'notes']
        widgets = {
            'location': forms.Select(attrs={
                'class': 'form-control'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Surveillance notes and observations'
            })
        }


class ThreatSearchForm(forms.Form):
    query = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search threats...'
        })
    )
    
    category = forms.ChoiceField(
        choices=[('', 'All'), ('pest', 'Pests'), ('disease', 'Diseases')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    sort = forms.ChoiceField(
        choices=[
            ('name_asc', 'Name (A-Z)'),
            ('name_desc', 'Name (Z-A)'),
            ('created_desc', 'Newest First'),
            ('created_asc', 'Oldest First')
        ],
        required=False,
        initial='name_asc',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    contact_number = forms.CharField(max_length=15, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            Grower.objects.create(
                user=user,
                contact_number=self.cleaned_data.get('contact_number')
            )
        return user