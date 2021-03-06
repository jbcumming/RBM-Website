import os
import json
import shutil
import tasks
import numpy as np
from PIL import Image as pil
from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.conf import settings
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib import messages
from rbm_website.apps.rbm.forms import DBNForm
from rbm_website.apps.rbm.forms import SearchForm
from rbm_website.apps.rbm.models import DBNModel
from rbm_website.libs.image_lib import image_processor as imgpr
from rbm_website.libs.decorators import message_login_required

# Generic view for a list of DBNs
class DBNListView(ListView):
    model = DBNModel

    @method_decorator(message_login_required)
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DBNListView, self).dispatch(*args, **kwargs)

# Generic view for the profile of a DBN
class DBNDetailView(DetailView):
    model = DBNModel

    def get_context_data(self, **kwargs):
        context = super(DBNDetailView, self).get_context_data(**kwargs)
        context['topology'] = self.object.get_topology()

        # Gets the base images if trained
        if self.object.trained:
            class_path = settings.MEDIA_ROOT + str(self.object.id)
            base_path = class_path + '/base_images'
            (images, labels) = imgpr.retrieve_images_base64(base_path)
            dictionary = dict(zip(labels, images))
            context['image_data'] = dictionary

        return context

    # Checks to make sure that only those allowed can access the DBN
    @method_decorator(message_login_required)
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        dbn = self.get_object()
        if (dbn.private and (self.request.user != dbn.creator)):
            messages.add_message(self.request, messages.ERROR, 'That DBN is private and you are not the owner!')
            url = reverse('index')
            return redirect(url)
        else:
            return super(DBNDetailView, self).dispatch(*args, **kwargs)

# Gets a list of DBNs
# By default, returns the 10 most recent DBNs
# Otherwise allows the user to search and sort DBNs
# Provides the base image or a default image if not trained
@message_login_required
@login_required
def dbn_list(request):
    if request.method == 'GET':
        form = SearchForm()
        recent_dbns = DBNModel.objects.filter(private=False).order_by('-created')[:10]
        dbn_images = []
        for dbn in recent_dbns:
            if dbn.trained:
                class_path = settings.MEDIA_ROOT + str(dbn.id)
                image_path = class_path + '/base_images/' + dbn.label_values[0] + '.png'
                image = imgpr.retrieve_image_base64(image_path)
                dbn_images.append(image)
            else:
                dbn_images.append('notTrained')
        dbn_info = zip(recent_dbns, dbn_images)
        return render(request, 'rbm/dbnmodel_list.html', {'dbns': dbn_info, 'searchForm' : form})
    elif request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            criteria = form.cleaned_data['criteria']
            order = form.cleaned_data['order_by']
            trained_only = form.cleaned_data['trained']
            terms = criteria.split()
            result_dbns = []
            dbn_images = []

            for t in terms:
                if trained_only:
                    termResults = DBNModel.objects.filter(name__icontains=t).filter(private=False).filter(trained=True)
                else:
                    termResults = DBNModel.objects.filter(name__icontains=t).filter(private=False)
                for tResult in termResults:
                    if (not tResult in result_dbns):
                        result_dbns.append(tResult)

                creatorResults = User.objects.filter(username__icontains=t)
                for cResult in creatorResults:
                    if trained_only:
                        cDbns = cResult.dbns.filter(private=False).filter(trained=True)
                    else:
                        cDbns = cResult.dbns.filter(private=False)
                    for dbn in cDbns:
                        if (not dbn in result_dbns):
                           result_dbns.append(dbn)

                if t.isdigit():
                    searchID = int(t)
                    if trained_only:
                        idResults = DBNModel.objects.filter(id__exact=searchID).filter(private=False).filter(trained=True)
                    else:
                        idResults = DBNModel.objects.filter(id__exact=searchID).filter(private=False)
                    for iResult in idResults:
                        if (not iResult in result_dbns):
                            result_dbns.append(iResult)

            if order == "nameasc":
                result_dbns.sort(key=lambda x: x.name, reverse=True)
            elif order == "namedesc":
                result_dbns.sort(key=lambda x: x.name)
            elif order == "timeasc":
                result_dbns.sort(key=lambda x: x.created)
            elif order == "timedesc":
                result_dbns.sort(key=lambda x: x.created, reverse=True)

            for dbn in result_dbns:
                if dbn.trained:
                    class_path = settings.MEDIA_ROOT + str(dbn.id)
                    image_path = class_path + '/base_images/' + dbn.label_values[0] + '.png'
                    image = imgpr.retrieve_image_base64(image_path)
                    dbn_images.append(image)
                else:
                    dbn_images.append('notTrained')

            dbn_info = zip(result_dbns, dbn_images)
            return render(request, 'rbm/dbnmodel_list.html', {'dbns': dbn_info, 'searchForm' : form})
        else:
            return render(request, 'rbm/dbnmodel_list.html', {'searchForm' : form})
    else:
        return render(request, 'rbm/dbnmodel_list.html', {})

# Deletes a DBN from the database
# Checks to make sure only the creator can delete the DBN
@message_login_required
@login_required
def delete(request, dbn_id):
    if request.method == 'GET':
        dbn = get_object_or_404(DBNModel , pk=dbn_id)

        if dbn.creator == request.user:
            dbn.delete()
            messages.add_message(request, messages.INFO, 'Your DBN was successfully deleted!')
            url = reverse('home')
            return redirect(url)
        else:
            messages.add_message(request, messages.INFO, 'You do not have permission to delete this DBN!')
            url = reverse('view', kwargs={'pk': dbn.id})
            return redirect(url)
    else:
        url = reverse('home')
        return redirect(url)

# Classifies an image using the DBN
# Flips the pixels if required
# Gets the image posted
# Classifies it and then returns the probability via a JSON
# Used as an AJAX request
# Otherwise just returns the classify page
def classify(request, dbn_id):
    if request.method == 'POST':
        dbn = get_object_or_404(DBNModel , pk=dbn_id)
        save_image("classifyImage", request.POST['image_data'], dbn)
        image_data = imgpr.convert_url_to_array(request.POST['image_data'], "classifyImage")

        if dbn.id in settings.FLIPPED_DBNS:
            iterator = np.vectorize(flip_pixels)
            image_data = iterator(image_data)

        probs = dbn.classify_image([image_data], 1)
        for i in range(1,10):
            probs = probs + dbn.classify_image([image_data], 1)

        probs = probs[0] / 10
        max_prob = probs.max()
        result = dbn.label_values[probs.argmax(axis=0)]

        os.remove(settings.MEDIA_ROOT + str(dbn.id) + '/base_images/classifyImage.png')

        json_data = json.dumps({
            "label_values": dbn.label_values,
            "probs":probs.tolist(),
            "max_prob":max_prob,
            "result":result
        })

        return HttpResponse(json_data, mimetype="application/json")
    else:
        if not request.user.is_authenticated():
            messages.add_message(request, messages.ERROR, "You must be logged in to access this content!")
            url = reverse('home', kwargs={})
            return redirect(url)
        else:
            dbn = get_object_or_404(DBNModel , pk=dbn_id)

            if dbn.training:
                messages.add_message(request, messages.ERROR, 'This DBN is currently being trained!' +
                    ' Please check back shortly to use it!')
                url = reverse('view', kwargs={'pk': dbn.id})
                return redirect(url)

            return render(request, 'rbm/classify.html', {'dbn': dbn})

# Flips a pixel
def flip_pixels(value):
    if value == 1:
        return 0
    else:
        return 1

# Trains the DBN
# Gets the images and labels posted
# Starts the celery task to train in the background
# Otherwise returns the training page to begin training
@message_login_required
@login_required
def train(request, dbn_id):
    if request.method == 'POST':
        dbn = get_object_or_404(DBNModel , pk=dbn_id)

        clean_image_directory(dbn.id)
        label_values = []

        for x in range(0, dbn.labels):
            save_image(request.POST['classImages[' + str(x) + '][image_name]'],
                request.POST['classImages[' + str(x) + '][image_data]'], dbn)
            label_values.append(request.POST['classImages[' + str(x) + '][image_name]'])


	pre_epoch = int(request.POST.get('pre_epoch'))
	train_epoch = int(request.POST.get('train_epoch'))
	train_loop = int(request.POST.get('train_loop'))
        tasks.train_dbn.delay(dbn, label_values, pre_epoch, train_epoch, train_loop)
        messages.add_message(request, messages.INFO, 'Congratulations! Your DBN is training.' +
            ' Please check back shortly to use it!')
        return redirect('/rbm/training/')
    else:
        dbn = get_object_or_404(DBNModel , pk=dbn_id)
        if dbn.trained:
            messages.add_message(request, messages.ERROR, 'This DBN has already been trained!' +
                ' Please create a new DBN to train on new data.')
            url = reverse('view', kwargs={'pk': dbn.id})
            return redirect(url)

        if dbn.training:
            messages.add_message(request, messages.ERROR, 'This DBN is currently being trained!' +
                ' Please check back shortly to use it!')
            url = reverse('view', kwargs={'pk': dbn.id})
            return redirect(url)

        return render(request, 'rbm/train.html', {'dbn': dbn})

# Cleans up the directory for training
def clean_image_directory(id):
    path = settings.MEDIA_ROOT + str(id)
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path + '/base_images')

# Saves a URL specified image to a directory
def save_image(image_id, image_data, dbn):
    image_data = imgpr.convert_url_to_image(image_data, image_id)
    image = pil.open(image_data).convert("L")
    image_path = settings.MEDIA_ROOT  + str(dbn.id) + '/base_images/' + image_id + '.png'
    image.save(image_path)

# A training page for after training begins
@message_login_required
@login_required
def training(request):
    if request.method == 'POST':
        return render(request, 'rbm/training.html', {})
    else:
        return render(request, 'rbm/training.html', {})

# Used to create a DBN
# Sets up the form with all the details
# Otherwise sorts out a completed form to create a DBN
@message_login_required
@login_required
def create(request):
    if request.method == 'POST':
        form = DBNForm(request.POST, layer=request.POST.get('layer_count'))

        if form.is_valid():
            height = form.cleaned_data['height']
            width = form.cleaned_data['width']
            visible = height*width
            labels = form.cleaned_data['labels']
            learning_rate = form.cleaned_data['learning_rate']
            description = form.cleaned_data['description']
            name = form.cleaned_data['name']
            private = form.cleaned_data['private']
            creator = request.user
            layer_count = form.cleaned_data['layer_count']

            topology = []
            topology.append(visible)
            for index in range(layer_count):
                topology.append(form.cleaned_data['layer_{index}'.format(index=index)])

            dbn = DBNModel.build_dbn(name, creator, description, height, width, topology, labels, private, learning_rate)
            dbn.save()
            messages.add_message(request, messages.INFO, 'Successfully created the DBN!')
            url = reverse('view', kwargs={'pk': dbn.id})
            return redirect(url)
    else:
        form = DBNForm()

    return render(request, 'rbm/create.html', { 'form' : form })
