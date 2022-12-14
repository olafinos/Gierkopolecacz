from smtplib import SMTPAuthenticationError

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.contrib import messages
from django.contrib.auth import logout, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpRequest
from django.views import generic
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from gierkopolecacz.forms import UserRegistrationForm
from gierkopolecacz.tokens import account_activation_token


class SignupView(generic.View):

    def post(self, request: HttpRequest):
        """
        View which allows to create account. When account is created is not active. To be in such state user needs to
        activate account by using email sent to them
        :param request: Incoming HttpRequest with all data
        """
        if request.user.is_authenticated:
            return redirect("/")
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            send_activation_email(request, user, form.cleaned_data.get("email"))
            return redirect("/polecacz/")
        else:
            return render(
                request=request,
                template_name="./registration/signup.html",
                context={"form": form},
                )

    def get(self, request: HttpRequest):
        form = UserRegistrationForm()
        return render(
            request=request,
            template_name="./registration/signup.html",
            context={"form": form},
        )


def send_activation_email(request: HttpRequest, user: User, to_email: str):
    """
    Sends email with token needed to activate account
    :param request: Incoming HttpRequest with all data
    :param user: User object
    :param to_email: Email address
    """
    mail_subject = "Aktywuj swoje konto."
    message = render_to_string(
        "./email_conf/activate_account.html",
        {
            "user": user.username,
            "domain": get_current_site(request).domain,
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": account_activation_token.make_token(user),
            "protocol": "https" if request.is_secure() else "http",
        },
    )
    try:
        _send_email(mail_subject, message, request, to_email, user)
    except SMTPAuthenticationError:
        messages.error(
            request,
            "Wyst??pi?? problem z wysy??aniem mailu z linkiem aktywacyjnym. "
            "W celu weryfikacji skontaktuj si?? z administratorem",
        )


def _send_email(
    mail_subject: str, message: str, request: HttpRequest, to_email: str, user: User
):
    """
    Sends email with activation link
    :param mail_subject: Mail subject
    :param message: Mail message
    :param request: Incoming HttpRequest with all data
    :param to_email: Email address
    :param user: User object
    """
    email = EmailMessage(mail_subject, message, to=[to_email])
    if email.send():
        messages.success(
            request,
            f"<b>{user}</b>, prosz?? sprawd?? swoj?? skrzynk?? odbiorcz?? dla adresu <b>{to_email}</b> i kliknij w \
                otrzymany link aktywacyjny aby potwierdzi?? oraz uko??czy?? rejestracje. <b>Uwaga:</b> Sprawd?? sw??j spam.",
        )
    else:
        messages.error(
            request,
            "Wyst??pi?? problem z wysy??aniem mailu z linkiem aktywacyjnym. "
            "Prosz?? sprawd??, czy prawid??owo zosta?? wpisany adres e-mail.",
        )


class ActivateView(generic.View):

    def get(self, request: HttpRequest, uidb64: bytes, token: str):
        """
        Allows to activate user account by using their id and token
        :param request: Incoming HttpRequest with all data
        :param uidb64: User id decoded to base64 bytes object
        :param token: Validation token
        """
        User = get_user_model()
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and account_activation_token.check_token(user, token):
            user.is_active = True
            user.save()

            messages.success(
                request,
                "Dzi??kujemy za aktywacj?? konta. Mo??esz teraz si?? do niego zalogowa??.",
            )
            return redirect("login")
        else:
            messages.error(request, "Link aktywacyjny jest niepoprawny!")

        return redirect("polecacz/")


class LogoutView(LoginRequiredMixin, generic.View):
    def get(self, request: HttpRequest):
        """
        Allows user to logout
        :param request: Incoming HttpRequest with all data
        """
        logout(request)
        return redirect("polecacz/")
