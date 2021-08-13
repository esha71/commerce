from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from datetime import datetime


class User(AbstractUser):
    id = models.AutoField(primary_key=True)
    pass

class Base(models.Model):
    id = models.AutoField(primary_key=True)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='%(class)s_createdby',
                                   on_delete=models.DO_NOTHING)
    modified_on = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name='%(class)s_modifiedby',
                                   on_delete=models.DO_NOTHING)

    class Meta:
        abstract = True

    def to_string(self):
        return str(self.__class__) + ": " + str(self.__dict__)


    def get_all_fields(self):
        """Returns a list of all field names on the instance."""
        fields = []
        for f in self._meta.fields:

            fname = f.name
            # resolve picklists/choices, with get_xyz_display() function
            get_choice = 'get_' + fname + '_display'
            if hasattr(self, get_choice):
                value = getattr(self, get_choice)()
            else:
                try:
                    value = getattr(self, fname)
                except AttributeError:
                    value = None

            # only display fields with values and skip some fields entirely
            if f.editable and value and f.name not in ('modified_by', 'modified_on', ):
                fields.append(
                    {
                        'label': f.verbose_name,
                        'name': f.name,
                        'value': value,
                    }
                )
        return fields

    def save(self, *args, **kwargs):
        # self.slug = slugify(self.title)
        try:
            self.modified_on = datetime.now()
            if not self.id:
                self.created_on = self.modified_on
                self.created_by = self.modified_by
            super(Base, self).save(*args, **kwargs)
        except Exception as e:
            raise




class Category(Base):
    name = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.name



class Listing(Base):
    name = models.CharField(max_length=30,)
    last_high_bid = models.OneToOneField('Bids', related_name='%(class)s_current_high_bid', on_delete=models.DO_NOTHING,
                                         null=True, blank=True)
    starting_bid_price = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField()
    status = models.CharField(max_length=1,
                              choices=[("A", "Active"), ("C", "Closed"), ("D", "Discontinued")],
                              default="A", )
    category = models.ForeignKey(Category, related_name='%(class)s_category',
                                 on_delete=models.DO_NOTHING, )
    image_url = models.URLField("Image", blank=True, null=True)


class Bids(Base):
    listing = models.ForeignKey(Listing, related_name='%(class)s_listing',
                                on_delete=models.DO_NOTHING, )
    bid_price = models.DecimalField(max_digits=12, decimal_places=2)
    user = models.ForeignKey(User, related_name='%(class)s_user',
                                   on_delete=models.DO_NOTHING)

    def __str__(self):
        return self.bid_price.__str__()

    # def save(self, *args, **kwargs):
    #     super(Bids, self).save(*args, **kwargs)
    #     self.listing.last_high_bid = self


class Comments(Base):
    description = models.TextField()
    listing = models.ForeignKey(Listing, related_name='%(class)s_listing',
                                on_delete=models.DO_NOTHING, null=True)

    class Meta:
        ordering = ['created_on']

    def __str__(self):
        return 'Comment {} by {}'.format(self.description, self.created_by)


class Watchlist(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, related_name='%(class)s_user',
                             on_delete=models.DO_NOTHING)
    listing = models.ForeignKey(Listing, related_name='%(class)s_listing',
                                on_delete=models.DO_NOTHING, )

    class Meta:
        unique_together = [
            ["user", "listing"],
        ]

