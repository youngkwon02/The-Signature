import shutil
from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render
from django.core.exceptions import ImproperlyConfigured
from .models import preservedResult
from .models import preservedWatermark
from PIL import Image
import os
import json
import sys
import re
import io
import base64
import random

sys.path.insert(
    1, '/home/ubuntu/src/TheSignature-Web/signMaker/new_model/')
import run

secret_file = os.path.realpath('./secrets.json')

with open(secret_file) as f:
    secrets = json.loads(f.read())


def get_secret(key, secrets=secrets):
    try:
        return secrets[key]
    except KeyError:
        error_msg = "Set the {} environment variable".format(key)
        raise ImproperlyConfigured(error_msg)


def session_existence(request):
    if 'user_email' not in request.session:
        return False
    else:
        return True


def drawingPage(request):
    if session_existence(request):
        rows = preservedResult.objects.filter(
            owner_email=request.session['user_email'], is_removed="F", is_rep="T").values()
        if len(rows) > 0:
            return render(request, 'signMaker/drawing.html', {'alpha_path': rows[0]['alpha_path']})
        else:
            return render(request, 'signMaker/drawing.html')
    else:
        return redirect('login')


def mainPage(request):
    if session_existence(request):
        return render(request, 'signMaker/selectOption.html')
    else:
        return redirect('login')


def getNumberOfWatermark(request):
    if session_existence(request):
        rows = preservedWatermark.objects.filter(
            owner_email=request.session['user_email']).values()
        return len(rows)
    else:
        return redirect('login')


def watermarkPage(request):
    if session_existence(request):
        rows = preservedResult.objects.filter(
            owner_email=request.session['user_email'], is_removed="F", is_rep="T").values()
        if len(rows) > 0:
            return render(request, 'signMaker/watermark.html', {'alpha_path': rows[0]['alpha_path']})
        else:
            return render(request, 'signMaker/watermark.html')
    else:
        return redirect('login')


def watermarkUpload(request):
    if session_existence(request):
        if request.method == 'POST':
            if request.POST.get('savedImg'):
                preservedDir = './signMaker/preservedWatermark/'
                if os.path.isdir(preservedDir)==False:
                    os.mkdir(preservedDir)
                image_path = 'signMaker/preservedWatermark/' + request.session['user_email'] + str(getNumberOfWatermark(request)+1) + '.png'
                savedImg = request.POST.get('savedImg', '')
                imgstr = re.search(r'base64,(.*)', savedImg).group(1)
                output = open(image_path, 'wb')
                output.write(base64.b64decode(imgstr))
                output.close()
                
                form = preservedWatermark()
                form.owner_email = request.session["user_email"]
                form.result_path = image_path
                form.save()
            return redirect('watermark')
        else:
            return render(request, 'signMaker/watermark.html')
    else:
        return redirect('login')
    

def passOptions(request):
    if not session_existence(request):
        return redirect('login')
    email = request.session['user_email']
    user_name = request.GET['name']
    option = request.GET['options']
    is_cap = request.GET['isCapital']
    color = request.GET['color']
    data = {
        "email": request.session['user_email'],
        "name": user_name,
        "option": option,
        "color": color,
        "isCap": is_cap
    }
    num = random.sample([1, 5, 6, 8, 12, 17, 18, 20, 21], 3)
    run.make_result(data, '01', num[0])
    run.make_result(data, '02', num[1])
    run.make_result(data, '03', num[2])
    
    return render(request, 'signMaker/signCreate.html', data)
    

def preserveResult(request):
    if not session_existence(request):
        return redirect('login')
    rows = preservedResult.objects.filter(
        owner_email=request.session['user_email'],
        is_removed="F")
    file_seq = str(len(preservedResult.objects.filter(owner_email=request.session['user_email'])) + 1)
    path = ""

    preservedDir = './signMaker/preservedResult/'
    if os.path.isdir(preservedDir)==False:
        os.mkdir(preservedDir)
    alphaPreservedDir = './signMaker/alphaPreservedResult/'
    if os.path.isdir(alphaPreservedDir)==False:
        os.mkdir(alphaPreservedDir)

    if len(rows) == 0:
        path += shutil.copy("./signMaker/static/ml_result/" + request.session['user_email'] + "/" +
                            request.GET['file_name'], "./signMaker/preservedResult/" + request.session['user_email'] + file_seq + ".png")
        path += shutil.copy("./signMaker/static/alpha_result/" + request.session['user_email'] + "/" +
                            request.GET['file_name'], "./signMaker/alphaPreservedResult/" + request.session['user_email'] + file_seq + ".png")        
        preservedResult.objects.create(owner_email=request.session['user_email'],
                                       result_path="../../signMaker/preservedResult/" + request.session['user_email'] + file_seq + ".png",
                                       alpha_path="../../signMaker/alphaPreservedResult/" + request.session['user_email'] + file_seq + ".png",
                                       is_removed="F", is_rep="T")
    elif len(rows) < 5:
        path += shutil.copy("./signMaker/static/ml_result/" + request.session['user_email'] + "/" +
                            request.GET['file_name'], "./signMaker/preservedResult/" + request.session['user_email'] + file_seq + ".png")
        path += shutil.copy("./signMaker/static/alpha_result/" + request.session['user_email'] + "/" +
                            request.GET['file_name'], "./signMaker/alphaPreservedResult/" + request.session['user_email'] + file_seq + ".png")        
        preservedResult.objects.create(owner_email=request.session['user_email'],
                                       result_path="../../signMaker/preservedResult/" + request.session['user_email'] + file_seq + ".png",
                                       alpha_path="../../signMaker/alphaPreservedResult/" + request.session['user_email'] + file_seq + ".png",
                                       is_removed="F", is_rep="F")
    return render(request, 'signMaker/signCreate.html', {"email": request.session['user_email']})


def is_storable(request):
    if not session_existence(request):
        return redirect('login')
    rows = preservedResult.objects.filter(
        owner_email=request.session['user_email'],
        is_removed="F")
    if len(rows) < 5:
        return HttpResponse('True')
    else:
        return HttpResponse('False')


def set_rep_signature(request):
    if not session_existence(request):
        return redirect('login')
    target_src = request.GET['target_src']
    preservedResult.objects.filter(owner_email=request.session['user_email']).update(is_rep='F')
    preservedResult.objects.filter(owner_email=request.session['user_email'], result_path=target_src).update(is_rep='T')
    return HttpResponse('True')


def delete_preserved_result(request):
    if not session_existence(request):
        return redirect('login')
    target_src = request.GET['target_src']
    rows = preservedResult.objects.filter(owner_email=request.session['user_email'], result_path=target_src)
    if len(rows) < 1 :
        return HttpResponse('False')
    preservedResult.objects.filter(owner_email=request.session['user_email'], result_path=target_src).update(is_removed='T')
    return HttpResponse('True')