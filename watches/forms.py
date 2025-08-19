from django import forms
from .models import PriceWatch
from .url_parser import vinted_parser
import json


class PriceWatchForm(forms.ModelForm):
    # URL input field for easy form filling
    vinted_url = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Paste Vinted catalog URL here (e.g., https://www.vinted.be/catalog?search_text=barbour...)',
            'id': 'vinted-url-input'
        }),
        help_text="Paste a Vinted catalog URL to automatically fill the form fields below"
    )
    # Individual fields for better UX
    search_text = forms.CharField(
        max_length=200, 
        required=False, 
        help_text="Search query (e.g., 'barbour bedale')"
    )
    catalog_ids = forms.CharField(
        max_length=50, 
        required=False, 
        help_text="Category IDs (comma separated)"
    )
    price_to = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False,
        help_text="Maximum price"
    )
    brand_ids = forms.CharField(
        max_length=50, 
        required=False, 
        help_text="Brand IDs (comma separated)"
    )
    status_ids = forms.CharField(
        max_length=50, 
        required=False, 
        help_text="Condition IDs: 6=As new with tag, 1=As new, 2=Very good, 3=Good, 4=Heavily used"
    )
    size_ids = forms.CharField(
        max_length=50, 
        required=False, 
        help_text="Size IDs (comma separated)"
    )
    color_ids = forms.CharField(
        max_length=50, 
        required=False, 
        help_text="Color IDs (comma separated)"
    )
    
    class Meta:
        model = PriceWatch
        fields = ['name', 'std_dev_threshold', 'absolute_price_threshold', 'blacklist_words', 'highlight_words']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'e.g., Barbour Bedale Watch'
            }),
            'std_dev_threshold': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'step': '0.1',
                'min': '0.1'
            }),
            'absolute_price_threshold': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'step': '0.01',
                'min': '0'
            }),
            'blacklist_words': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'rows': 2,
                'placeholder': 'fake, replica, copy, defect'
            }),
            'highlight_words': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'rows': 2,
                'placeholder': 'vintage, rare, limited, deadstock'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If editing existing instance, populate individual fields from search_parameters
        if self.instance and self.instance.pk and self.instance.search_parameters:
            params = self.instance.search_parameters
            self.fields['search_text'].initial = params.get('search_text', '')
            self.fields['catalog_ids'].initial = ','.join(map(str, params.get('catalog_ids', [])))
            self.fields['price_to'].initial = params.get('price_to')
            self.fields['brand_ids'].initial = ','.join(map(str, params.get('brand_ids', [])))
            self.fields['status_ids'].initial = ','.join(map(str, params.get('status_ids', [])))
            self.fields['size_ids'].initial = ','.join(map(str, params.get('size_ids', [])))
            self.fields['color_ids'].initial = ','.join(map(str, params.get('color_ids', [])))
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Build search_parameters from individual fields
        search_parameters = {}
        
        if cleaned_data.get('search_text'):
            search_parameters['search_text'] = cleaned_data['search_text']
        
        if cleaned_data.get('catalog_ids'):
            try:
                catalog_ids = [int(x.strip()) for x in cleaned_data['catalog_ids'].split(',') if x.strip()]
                if catalog_ids:
                    search_parameters['catalog_ids'] = catalog_ids
            except ValueError:
                self.add_error('catalog_ids', 'Please enter valid numeric IDs separated by commas')
        
        if cleaned_data.get('price_to'):
            search_parameters['price_to'] = float(cleaned_data['price_to'])
        
        if cleaned_data.get('brand_ids'):
            try:
                brand_ids = [int(x.strip()) for x in cleaned_data['brand_ids'].split(',') if x.strip()]
                if brand_ids:
                    search_parameters['brand_ids'] = brand_ids
            except ValueError:
                self.add_error('brand_ids', 'Please enter valid numeric IDs separated by commas')
        
        if cleaned_data.get('status_ids'):
            try:
                status_ids = [int(x.strip()) for x in cleaned_data['status_ids'].split(',') if x.strip()]
                if status_ids:
                    search_parameters['status_ids'] = status_ids
            except ValueError:
                self.add_error('status_ids', 'Please enter valid numeric IDs separated by commas')
        
        if cleaned_data.get('size_ids'):
            try:
                size_ids = [int(x.strip()) for x in cleaned_data['size_ids'].split(',') if x.strip()]
                if size_ids:
                    search_parameters['size_ids'] = size_ids
            except ValueError:
                self.add_error('size_ids', 'Please enter valid numeric IDs separated by commas')
        
        if cleaned_data.get('color_ids'):
            try:
                color_ids = [int(x.strip()) for x in cleaned_data['color_ids'].split(',') if x.strip()]
                if color_ids:
                    search_parameters['color_ids'] = color_ids
            except ValueError:
                self.add_error('color_ids', 'Please enter valid numeric IDs separated by commas')
        
        # Add default parameters
        search_parameters.update({
            'per_page': 96,
            'currency': 'EUR',
            'order': 'newest_first'
        })
        
        cleaned_data['search_parameters'] = search_parameters
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.search_parameters = self.cleaned_data['search_parameters']
        if commit:
            instance.save()
        return instance