from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse
from django.shortcuts import render, render_to_response, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect


def logmein(request, _next=None):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect(
                    request.GET.get("next") or request.META.get("HTTP_REFERER")
                )
            else:
                pass
                return HttpResponse("Account Locked")
        else:
            pass
            return HttpResponse("Account Invalid")
    return render(request, "nhdb/login.html")


project_filters = ["act", "ben", "inv", "place", "pcode"]


def logmeout(request):
    logout(request)
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))
