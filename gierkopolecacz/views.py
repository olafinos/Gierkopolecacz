from django.core.mail import EmailMessage
from django.contrib import messages
from django.contrib.auth import logout, get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from gierkopolecacz.forms import UserRegistrationForm
from gierkopolecacz.tokens import account_activation_token


def signup(request):
    """
    View which allows to create account. When account is created is not active. To be in such state user needs to activate
    account by using email sent to them.
    """
    if request.user.is_authenticated:
        return redirect("/")

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            activate_email(request, user, form.cleaned_data.get('email'))
            return redirect('/polecacz/')
        else:
            for error in list(form.errors.values()):
                print(request, error)
    else:
        form = UserRegistrationForm()
    return render(
        request=request,
        template_name="./registration/signup.html",
        context={"form": form}
        )


def activate_email(request, user, to_email):
    """
    Sends email with token needed to activate account.
    """
    mail_subject = 'Aktywuj swoje konto.'
    message = render_to_string('./email_conf/activate_account.html', {
        'user': user.username,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http'
    })
    email = EmailMessage(mail_subject, message, to=[to_email])
    if email.send():
        messages.success(request, f'<b>{user}</b>, proszę sprawdź swoją skrzynkę odbiorczą dla adresu <b>{to_email}</b> i kliknij w \
            otrzymany link aktywacyjny aby potwierdzić oraz ukończyć rejestracje. <b>Uwaga:</b> Sprawdź swój spam.')
    else:
        messages.error(request, 'Wystąpił problem z wysyłaniem mailu z linkiem aktywacyjnym. '
                                'Proszę sprawdź, czy prawidłowo został wpisany adres e-mail.')


def activate(request, uidb64, token):
    """
    Allows to activate user account by using their id and token
    """
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()

        messages.success(request, 'Dziękujemy za aktywację konta. Możesz teraz się do niego zalogować.')
        return redirect('login')
    else:
        messages.error(request, 'Link aktywacyjny jest niepoprawny!')

    return redirect('homepage')


def logout_view(request):
    logout(request)
    return redirect('polecacz/')
