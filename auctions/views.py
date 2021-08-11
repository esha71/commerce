from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.forms import ModelForm, Field
from django import forms
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
import urllib.parse as urlparse
from urllib.parse import parse_qs
from django.forms import modelform_factory
from django.db import transaction
from django.views.decorators.http import require_POST

from commerce import settings
from .models import User, Listing, Category, Watchlist, Bids, Comments

html_pages = {
    "listing_view": "listings/view.html",
    "message_view": "listings/message.html",
}

def index(request):
    # return render(request, "auctions/index.html")
    return HttpResponseRedirect(reverse('active_listing'))


def active_listings(request):
    # listingObjects =listings.objects.filter(status="A")
    return render(request, "listings/index.html", {
        "heading": "Active Listings",
        "listings": listings_by_status(request, "A")
    })


def listings_by_status(request, status):
    if status:
        listingObjects = Listing.objects.filter(status=status)
        return listingObjects


class ListingForm(ModelForm):
    class Meta:
        model = Listing
        fields = ['name', 'description', 'starting_bid_price', 'category', 'image_url']

class CommentsForm(ModelForm):
    listing_id = forms.CharField(widget=forms.HiddenInput(), required=False)
    created_by = forms.CharField(widget=forms.HiddenInput(), disabled=True, required=False  )
    description = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Please write your comments'}))

    class Meta:
        model = Comments
        fields = ['description', ]




class BidForm(ModelForm):
    listing_id = forms.CharField(widget = forms.HiddenInput(), required = False)
    listing_on_watchlist = forms.BooleanField(widget = forms.HiddenInput(), required = False)
    bid_price = forms.DecimalField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Your bid price'}))
    # listing = forms.ChoiceField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Bids
        fields = ('bid_price',)

    def is_new_high_bid_price(self): #_bid_price
        data = self.cleaned_data.get("bid_price")
        listing = self.instance.listing
        new_high_bid = False
        if listing.last_high_bid:
            if data <= listing.last_high_bid.bid_price:
                self._errors['bid_price'] = self.error_class(['bid price less than last bid price'])
                # raise forms.ValidationError('bid price less than last bid price')
            else:
                new_high_bid = True
        else:
            if data < listing.starting_bid_price:
                self._errors['bid_price'] = self.error_class(['bid price less than starting price'])
               # raise forms.ValidationError('bid price less than starting price')
            else:
                new_high_bid = True
        return new_high_bid


@login_required(login_url='login')
def new_listing(request):
    if request.method == 'POST':
        # save the page_name and description
        form = ListingForm(request.POST or None)
        if form.is_valid():
            print(form.cleaned_data)
            form.instance.modified_by = User.objects.get(username=request.user)
            listingobj = form.save()
            url_for_page = reverse('view_listing', args=[listingobj.id])
            return HttpResponseRedirect(url_for_page)
        else:
            pass
    else:
        form = ListingForm(auto_id=True)
    return render(request, "listings/form.html", {
        "form": form
    })


def view_listing(request, listing_id):
    try:
        listing_obj = Listing.objects.get(id=listing_id)
        listingOnUserWatchList = None
        if request.user.is_authenticated:
            try:
                Watchlist.objects.get(listing__id=listing_id, user=request.user)
                listingOnUserWatchList = True
            except Watchlist.DoesNotExist:
                listingOnUserWatchList = False

        return render_detail_listing(request, listingOnUserWatchList, listing_obj)
    except Listing.DoesNotExist:
            return render(request, html_pages['message_view'], {
                "message": f"your requested listing '{listing_id}' was not found",
            })
    except Exception as e:
        return render(request, html_pages['message_view'], {"message": e.__str__()})


def render_detail_listing(request, listingOnUserWatchList, listing_obj, bid_form=None, comment_form=None):
    if bid_form is None:
        bid_form = BidForm(initial={"listing_id": listing_obj.id, 'listing_on_watchlist': listingOnUserWatchList})
    if comment_form is None:
        comment_form = CommentsForm(initial={"listing_id": listing_obj.id, 'created_by': request.user.username})
    return render(request, html_pages['listing_view'], {
        "listingOnUserWatchList": listingOnUserWatchList,
        "listing_obj": listing_obj,
        "bid_form": bid_form,
        "comment_form": comment_form,
    })

def edit_listing(request, listing_id):
    pass


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            url = request.META.get('HTTP_REFERER')
            parsed = urlparse.urlparse(url)
            parsed_q = parse_qs(parsed.query)
            if parsed_q.__contains__('next'):
                next_url = parsed_q['next']
                if next_url:
                    return HttpResponseRedirect(next_url[0])

            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


def view_category(request, category_id):
    if category_id:
        category_listings = Listing.objects.filter(category__id=category_id, status="A")
        if category_listings:
            category_name = category_listings[0].category.name
            return render(request, "listings/index.html", {
                "heading": "Listings in " + category_name + " Category",
                "listings": category_listings,
            })
        else:
            return render(request, html_pages['message_view'], {
                "message": f"listings for Category '{category_id}' was not found",
            })
    else:
        return render(request, html_pages['message_view'], {"message": "No Category provided "})


@login_required(login_url='login')
def view_watchlist(request):
    userid = request.user.id.__str__()
    listing = Listing.objects.raw(
        '''select l.* from auctions_listing l inner join auctions_watchlist wl
        on l.id=wl.listing_id where wl.user_id=''' + userid
    )
    #     wl_listings = Watchlist.objects.select_related('listing').filter(user=request.user)
    #     listing = []
    #     for wl_listing in wl_listings:
    #         listing.append(wl_listing.listing)
    if listing:
        return render(request, "listings/index.html", {
            "heading": "Listings in your Watchlist",
            "listings": listing,
        })
    else:
        return render(request, html_pages['message_view'], {
            "message": "No listings in your watchlist",
        })


@login_required(login_url='login')
def add_watchlist(request):
    if request.method == "POST":
        listing_id = request.POST["id"]
        new_list_wl = Watchlist()
        new_list_wl.user = request.user
        new_list_wl.listing = Listing.objects.get(id=listing_id)

        try:
            new_list_wl.save()
            messages.add_message(request, messages.INFO, 'listing saved to your watchlist')
        except IntegrityError as e:
            messages.add_message(request, messages.WARNING, 'listing exist in your watchlist')
        return redirect(reverse('view_listing', args=[listing_id]))


@login_required(login_url='login')
def remove_watchlist(request):
    if request.method == "POST":
        listing_id = request.POST["id"]
        try:
            wl_listing_to_delete = Watchlist.objects.get(listing__id=listing_id, user=request.user)
            wl_listing_to_delete.delete()
            messages.add_message(request, messages.INFO, 'listing deleted from your watchlist')
        except Watchlist.DoesNotExist:
            messages.add_message(request, messages.INFO, 'listing not in your watchlist')
        return redirect(reverse('view_listing', args=[listing_id]))


@require_POST
@login_required(login_url='/auctions/login')
def submit_bid(request):

    bid = BidForm(request.POST or None)

    if bid.is_valid():
        bid.instance.user = request.user
        bid.instance.modified_by = request.user
        bid.instance.bid_price = bid.cleaned_data['bid_price']

        bid.instance.listing = Listing.objects.get(id=bid.cleaned_data['listing_id'])

        if bid.is_new_high_bid_price():
            with transaction.atomic():
                bid.save()
                bid.instance.listing.last_high_bid = bid.instance
                bid.instance.listing.save()
                messages.add_message(request, messages.INFO, 'bid saved successfully')
        else:
            return render_detail_listing(request, bid.cleaned_data['listing_on_watchlist'], bid.instance.listing, bid)

        return render_detail_listing(request, bid.cleaned_data['listing_on_watchlist'], bid.instance.listing)



@login_required(login_url='/auctions/login')
def close_listing(request, listing_id):
    try:
        listing_obj = Listing.objects.get(id=listing_id)
        listing_obj.status = "C"
        listing_obj.save()
        winner_announce = "No one bid. No winner!"
        if listing_obj.last_high_bid:
            if listing_obj.last_high_bid.user:
                winner_announce = f"{listing_obj.last_high_bid.user.username} is winner!"
        return render(request, html_pages['message_view'], {
            "message": f"your listing '{listing_id}:{listing_obj.name}' is closed. {winner_announce}",
        })
    except Exception as e:
        return render(request, html_pages['message_view'], {
            "message": f"your listing '{listing_id}:{listing_obj.name}' could not be closed due to server error",
        })


@require_POST
@login_required(login_url='/auctions/login')
def post_comment(request):
    comment = CommentsForm(request.POST or None)

    if comment.is_valid():
        comment.instance.modified_by = request.user
        comment.instance.description = comment.cleaned_data['description']
        listing_id = comment.cleaned_data['listing_id']

        comment.instance.listing = Listing.objects.get(id=listing_id)

        comment.save()
        messages.add_message(request, messages.INFO, 'comment saved!')
        return redirect(reverse('view_listing', args=[listing_id]))