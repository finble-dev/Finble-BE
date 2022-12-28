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

 # google 로그인
class User(BaseModel):
    name = models.CharField(max_length=20)

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
    name = models.CharField(max_length=20)
    description = models.TextField


class Exchange_Rate(models.Model):
    date = models.DateField(default=None)
    rate = models.FloatField()

class Portfolio(BaseModel):
    symbol = models.ForeignKey(Stock, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    average_price = models.FloatField()
    quantity = models.IntegerField(default=1)


class Test_Portfolio(BaseModel):
    symbol = models.ForeignKey(Stock, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    seed_money = models.FloatField()
    ratio = models.IntegerField()

class Contact(models.Model):
    contact = models.CharField(max_length=50)
