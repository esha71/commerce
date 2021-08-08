# import listview as listview
from django.urls import path

from . import views
from django.views import generic

from .models import Listing, Category

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("listings/active/", views.active_listings, name="active_listing"),
    # path("listings/active/", generic.ListView.as_view(
    #     model=listings,
    #     paginate_by="10",
    #     queryset=listings.objects.filter(status="A"),
    #     context_object_name="listings",
    #     template_name="listings/index.html"
    # ), name="active_listing"),
    path("newlisting", views.new_listing, name="new_listing"),
    path("listing/<int:listing_id>/", views.view_listing, name="view_listing"),
    path("listing/<int:listing_id>/edit", views.edit_listing, name="edit_listing"),
    path("listing/<int:listing_id>/close-bid/", views.close_listing, name="close_listing"),


    path("categories/", generic.ListView.as_view(
        model=Category,
        paginate_by="10",
        queryset=Category.objects.all(),
        context_object_name="categories",
        template_name="category/index.html"
    ), name="categories"),
    path("category/<int:category_id>/", views.view_category, name="view_category"),

    path("watchlist/", views.view_watchlist, name="view_watchlist"),
    path("watchlist/add", views.add_watchlist, name="add_watchlist"),
    path("watchlist/remove", views.remove_watchlist, name="remove_watchlist"),

    path("submit_bid", views.submit_bid, name="submit_bid"),
    path("post_comment", views.post_comment, name="post_comment"),

]
