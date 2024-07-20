from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField()
    carrera = forms.CharField(max_length=100)
    nivel = forms.CharField(max_length=100, required=False)  # Add a field for level
