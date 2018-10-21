from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model
from django.core.files.images import get_image_dimensions
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, force_bytes

from .tokens import account_activation_token


class CustomUserCreationForm(UserCreationForm):
    image = forms.FileField(label='image', required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'profile_input', 'required': True})
        self.fields['email'].widget.attrs.update({'class': 'profile_input', 'required': True})
        self.fields['password1'].widget.attrs.update({'class': 'profile_input', 'required': True})
        self.fields['password2'].widget.attrs.update({'class': 'profile_input', 'required': True})

    class Meta:
        model = get_user_model()
        fields = ('username', 'password1', 'password2', 'email', 'image')

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.image = self.cleaned_data.get('image')
        user.email = self.cleaned_data.get("email")

        if commit:
            user.is_active = False
            user.save()

            date = user.date_joined.replace(microsecond=0)

            subject = u'[%s] : Subscription' % settings.SITE_NAME

            mail = render_to_string('registration/account_activation_email.html',
                                    {'title': subject,
                                     'username': user.username,
                                     'site': settings.SITE_NAME,
                                     'user_id': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
                                     'token': account_activation_token.make_token(user)})

            msg = EmailMessage(subject, mail, '%(site)s <%(email)s>' % {
                'site': settings.SITE_NAME, 'email': settings.DEFAULT_FROM_EMAIL
            }, [user.email])

            msg.content_subtype = "html"
            msg.send()

        return user

    def clean_image(self):
        image = self.cleaned_data['image']

        if not image:
            return

        try:
            w, h = get_image_dimensions(image)

            # validate dimensions
            max_width = max_height = 1000
            if w > max_width or h > max_height:
                raise forms.ValidationError(
                    u'Please use an image that is '
                    '%s x %s pixels or smaller.' % (max_width, max_height))

            # validate content type
            main, sub = image.content_type.split('/')
            if not (main == 'image' and sub in ['jpeg', 'pjpeg', 'gif', 'png']):
                raise forms.ValidationError(u'Please use a JPEG, '
                                            'GIF or PNG image.')

            # validate file size
            if len(image) > (120 * 1024):
                raise forms.ValidationError(
                    u'Avatar file size may not exceed 20k.')

        except AttributeError:
            """
            Handles case when we are updating the user profile
            and do not supply a new avatar
            """
            pass

        return image


class CustomUserChangeForm(UserChangeForm):

    image = forms.FileField(label='image', required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'profile_input', 'required': True})
        self.fields['email'].widget.attrs.update({'class': 'profile_input', 'required': True})

    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'image')
        exclude = ('password',)

    def clean_password(self):
        return ""
