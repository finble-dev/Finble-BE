from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
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

class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, id, nickname, email, password, **extra_fields):
        if not id:
            raise ValueError('Users require an id field')
        if not nickname:
            raise ValueError('Users require a nickname field')
        if not email:
            raise ValueError('Users require an email field')
        email = self.normalize_email(email)
        user = self.model(id=id, nickname=nickname, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, id, nickname, email, password=None, **extra_fields):
        return self._create_user(id, nickname, email, password, **extra_fields)

    def create_superuser(self, id, nickname, email, password, **extra_fields):
        user = self.create_user(
            id=id,
            nickname=nickname,
            email=email,
            password=password,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, BaseModel):
    id = models.CharField(max_length=20, primary_key=True)
    nickname = models.CharField(max_length=20)
    email = models.EmailField(max_length=255, unique=True)

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin

    objects = UserManager()

    USERNAME_FIELD = 'id'
    REQUIRED_FIELDS = ['email', 'nickname', ]

    def __str__(self):
        return self.nickname