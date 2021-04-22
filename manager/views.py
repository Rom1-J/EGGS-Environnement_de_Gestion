from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy

from .forms import *
from .models import *
from .urls import *

User = get_user_model()  # new User definitions


@login_required
def dashboard(request):
    user = request.user

    if request.method == "POST":
        database_name = request.POST.get('database')
        user.update_current_database(database_name)

    return render(request, "manager/dashboard.html", locals())


@login_required
def contact(request):
    send = False
    if request.method == 'POST':
        form = ContactForm(request.POST)

        if form.is_valid():
            subject = "Contact - " + form.cleaned_data.get('subject')
            user = User.objects.get(username=request.user.username)
            message = "Utilisateur : " + user.get_full_name() + " " + user.email + '\n\n' \
                      + form.cleaned_data.get('message')

            send_mail(subject=subject, message=message, from_email=None, recipient_list=['eggs.contacts@gmail.com'])
            send = True

    form = ContactForm()  # Réintialisation du formulaire

    return render(request, "manager/contact.html", locals())


@login_required
def add_database(request):
    user = request.user

    if request.method == 'POST':
        form = AddDbForm(request.POST, initial={'user': request.user})

        if form.is_valid():
            name = form.cleaned_data.get("name")
            type = form.cleaned_data.get("type")
            user = request.user

            db = DataBase()
            db.set(name=name, type=type)
            db.save()
            db.add_owner(user)
            user.update_current_database(db)

            return HttpResponseRedirect('/manager/dashboard/')
    else:
        form = AddDbForm(initial={'user': request.user})  # Réintialisation du formulaire

    return render(request, "manager/add_db.html", locals())


@login_required
def add_product(request):
    user = request.user
    current_database = user.current_database

    if user.is_current_owner() or user.is_current_editor():
        if request.method == 'POST':
            form = AddProductForm(request.POST, initial={'user': request.user})

            if form.is_valid():
                name = form.cleaned_data.get("name")
                quantity = form.cleaned_data.get("quantity")
                price = form.cleaned_data.get("price")

                product = Product()
                product.set(name=name, quantity=quantity, price=price)
                product.save()
                # Ajout du produit dans la base de donnée
                current_database.products.add(product)

                return HttpResponseRedirect('/manager/dashboard/')
        else:
            form = AddProductForm(initial={'user': request.user})

    else:
        return HttpResponseRedirect('/manager/dashboard/')

    return render(request, "manager/add_products.html", locals())


@login_required
def details_product(request, product_id):
    user = request.user
    product = get_object_or_404(Product, pk=product_id)

    if user.current_database is not None:
        if product not in user.current_database.products.all():
            return HttpResponseRedirect('/manager/display_products/')
    else:
        return HttpResponseRedirect('/manager/dashboard/')

    context = {
        'product': product,
        'user': user
    }
    return render(request, 'manager/details_product.html', context)


@login_required
def display_products(request):
    user = request.user
    if user.current_database is not None:
        products_list = user.current_database.products.all()
    else:
        products_list = []
    paginator = Paginator(products_list, 9)
    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        products = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        products = paginator.page(paginator.num_pages)
    context = {
        'products': products,
        'user': user,
        'paginate': True
    }
    return render(request, 'manager/display_products.html', context)


@login_required
def switch_current_db(request, database_name):
    user = request.user
    user.update_current_database(database_name)

    return render(request, 'manager/dashboard.html', locals())


@login_required
def my_databases(request):
    return render(request, 'manager/my_databases.html', locals())


@login_required
def update_product(request, product_id):
    user = request.user
    product = get_object_or_404(Product, pk=product_id)

    if user.is_current_owner() or user.is_current_editor():
        if product in user.current_database.products.all():
            if request.method == "POST":
                product_name = request.POST.get('name')
                product_quantity = request.POST.get('quantity')
                product_price = request.POST.get('price')
                product.set(name=product_name, price=product_price, quantity=product_quantity)
                product.save()
                return HttpResponseRedirect(reverse_lazy("manager:details_product", kwargs={'product_id': product_id}))
        else:
            return HttpResponseRedirect('/manager/dashboard/')
    else:
        return HttpResponseRedirect('/manager/dashboard/')

    return render(request, 'manager/update_product.html', locals())


@login_required
def compte(request):
    user = request.user

    return render(request, 'manager/compte.html', locals())


@login_required
def update_compte(request):
    user = request.user

    if request.method == "POST":
        user_firstname = request.POST.get('first_name')
        user_lastname = request.POST.get('last_name')
        user_email = request.POST.get('email')
        user.set(first_name=user_firstname, last_name=user_lastname, email=user_email)
        user.save()
        return HttpResponseRedirect('/manager/compte/')

    return render(request, 'manager/update_compte.html', locals())


@login_required
def update_password(request):
    user = request.user

    if request.method == 'POST':
        form = UpdatePasswordForm(request.POST, initial={'user': request.user})

        if form.is_valid():
            new_password2 = form.cleaned_data.get("new_password2")
            user.set_password(new_password2)
            user.save()

            current_site = get_current_site(request)
            subject = user.get_short_name() + " - Vous avez modifié votre mot de passe - "
            message = message = render_to_string('manager/update_password_email.html', {
                'user': user,
                'domain': current_site.domain,
                'protocol': 'http',
            })

            user.email_user(subject=subject, message=message)

            return HttpResponseRedirect('/manager/compte/')
    else:
        form = UpdatePasswordForm(initial={'user': request.user})  # Réintialisation du formulaire

    return render(request, 'manager/update_password.html', locals())
