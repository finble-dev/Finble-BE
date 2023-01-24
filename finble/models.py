from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.timezone import now


# Create your models here.
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, default=None)

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = now
        self.save(update_fields=['deleted_at'])

class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=30)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

class Stock(models.Model):
    symbol = models.CharField(primary_key=True, max_length=10)
    market = models.CharField(max_length=20)
    name = models.CharField(max_length=50)
    sector = models.CharField(max_length=20)

    def to_string(self):
        return '{}'.format(self.symbol)


class Price(models.Model):
    symbol = models.ForeignKey(Stock, on_delete=models.CASCADE)
    date = models.DateField(default=None)
    close = models.FloatField()


class Kospi(models.Model):
    date = models.DateField(default=None)
    index = models.FloatField()


class Recommend(models.Model):
    symbol = models.OneToOneField(Stock, on_delete=models.CASCADE, primary_key=True)
    name = models.CharField(max_length=50)
    description = models.TextField()


class ExchangeRate(models.Model):
    date = models.DateField(default=None)
    rate = models.FloatField(null=True)


class Portfolio(BaseModel):
    symbol = models.ForeignKey(Stock, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    average_price = models.FloatField()
    quantity = models.FloatField(default=0)


class TestPortfolio(BaseModel):
    symbol = models.ForeignKey(Stock, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ratio = models.FloatField(null=True, default=None)
    is_from_portfolio = models.BooleanField(default=True)


class Contact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    contact = models.CharField(max_length=50)
