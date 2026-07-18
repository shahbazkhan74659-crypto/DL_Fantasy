from django import forms
from django.utils.text import slugify

from .models import Collection, Content, Subcategory

FIELD_ATTRS = {'class': 'auth-field'}
BODY_ATTRS = {'class': 'auth-field', 'rows': 20}
SELECT_ATTRS = {'class': 'auth-field'}


class GodValleyUploadForm(forms.ModelForm):
    class Meta:
        model = Content
        fields = ('chapter_number', 'title', 'body', 'cover_image')
        labels = {
            'chapter_number': 'Chapter Number', 'title': 'Chapter Title', 'body': 'Chapter Body',
            'cover_image': 'Cover Image',
        }
        widgets = {
            'chapter_number': forms.NumberInput(attrs=FIELD_ATTRS),
            'title': forms.TextInput(attrs=FIELD_ATTRS),
            'body': forms.Textarea(attrs=BODY_ATTRS),
            'cover_image': forms.FileInput(attrs=FIELD_ATTRS),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['chapter_number'].required = True


class SubcategoryUploadForm(forms.ModelForm):
    """Base for Fiction/Philosophy/Mythology upload forms — each locks `subcategory`'s queryset to
    its own `parent_category` and lets the admin type a brand-new one inline instead of needing
    Django admin first, so a new story/topic/tradition never needs a code change.
    """
    parent_category = None
    category_label = 'Category'
    title_label = 'Title'

    new_subcategory_name = forms.CharField(
        required=False, label='Or add a new category',
        widget=forms.TextInput(attrs={**FIELD_ATTRS, 'placeholder': 'Type a new category name…'}),
    )

    class Meta:
        model = Content
        fields = ('subcategory', 'title', 'body', 'cover_image')
        labels = {'cover_image': 'Cover Image'}
        widgets = {
            'subcategory': forms.Select(attrs=SELECT_ATTRS),
            'title': forms.TextInput(attrs=FIELD_ATTRS),
            'body': forms.Textarea(attrs=BODY_ATTRS),
            'cover_image': forms.FileInput(attrs=FIELD_ATTRS),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subcategory'].queryset = Subcategory.objects.filter(parent_category=self.parent_category)
        self.fields['subcategory'].required = False
        self.fields['subcategory'].label = self.category_label
        self.fields['title'].label = self.title_label

    def clean(self):
        cleaned_data = super().clean()
        new_name = cleaned_data.get('new_subcategory_name', '').strip()
        if new_name:
            subcategory, _ = Subcategory.objects.get_or_create(
                parent_category=self.parent_category,
                slug=slugify(new_name)[:100],
                defaults={'name': new_name},
            )
            cleaned_data['subcategory'] = subcategory
        elif not cleaned_data.get('subcategory'):
            self.add_error('subcategory', 'Select an existing category or type a new one.')
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.subcategory = self.cleaned_data['subcategory']
        if commit:
            instance.save()
        return instance


class FictionUploadForm(SubcategoryUploadForm):
    parent_category = Content.Category.FICTION
    category_label = 'Fiction Category'
    title_label = 'Chapter Name'

    class Meta(SubcategoryUploadForm.Meta):
        fields = ('subcategory', 'chapter_number', 'title', 'body', 'cover_image')
        widgets = {**SubcategoryUploadForm.Meta.widgets, 'chapter_number': forms.NumberInput(attrs=FIELD_ATTRS)}


class PhilosophyUploadForm(SubcategoryUploadForm):
    parent_category = Content.Category.PHILOSOPHY
    category_label = 'Philosophy Category'
    title_label = 'Philosophy Title'


class MythologyUploadForm(SubcategoryUploadForm):
    parent_category = Content.Category.MYTHOLOGY
    category_label = 'Mythology Category'
    title_label = 'Mythology Title'


class CollectionForm(forms.ModelForm):
    """Create/edit an author-curated anthology. Unlike the content upload forms (where
    _handle_upload sets is_published server-side), is_published is exposed deliberately: a
    collection is assembled across sessions, so draft-then-publish is a real workflow. The
    `items` picker is hand-rendered in the templates as checkboxes grouped by category —
    it still validates through this field.
    """
    items = forms.ModelMultipleChoiceField(
        queryset=Content.objects.filter(is_published=True),
        required=False,
    )

    class Meta:
        model = Collection
        fields = ('title', 'description', 'cover_image', 'is_published')
        labels = {
            'title': 'Collection Title', 'description': 'Description',
            'cover_image': 'Cover Image', 'is_published': 'Published',
        }
        widgets = {
            'title': forms.TextInput(attrs=FIELD_ATTRS),
            'description': forms.Textarea(attrs={'class': 'auth-field', 'rows': 4}),
            'cover_image': forms.FileInput(attrs=FIELD_ATTRS),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['items'].initial = self.instance.contents.all()
