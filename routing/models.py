from django.db import models
from django.contrib.auth.models import (BaseUserManager,
                                        AbstractBaseUser,
                                        PermissionsMixin)
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    def _create_user(self, name, password, **extra_fields):
        user = self.model(name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, name, password=None, **extra_fields):
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(name=name, password=password, **extra_fields)

    def create_superuser(self, name, password, **extra_fields):
        extra_fields['is_active'] = True
        extra_fields['is_staff'] = True
        extra_fields['is_superuser'] = True
        return self._create_user(name=name, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):

    name = models.CharField(
        verbose_name=_("name"),
        unique=True,
        max_length=10
    )
    is_superuser = models.BooleanField(
        verbose_name=_("is_superuser"),
        default=False
    )
    is_staff = models.BooleanField(
        verbose_name=_('staff status'),
        default=False,
    )
    is_active = models.BooleanField(
        verbose_name=_('active'),
        default=True,
    )
    created_at = models.DateTimeField(
        verbose_name=_("created_at"),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        verbose_name=_("updated_at"),
        auto_now=True
    )

    objects = UserManager()

    USERNAME_FIELD = 'name'  # ログイン時、ユーザー名の代わりにaccount_idを使用
    REQUIRED_FIELDS = []  # スーパーユーザー作成時にemailも設定する

    def __str__(self):
        return self.name

# class Tag(models.Model):
#     name = models.CharField(max_length=100, unique=True)

#     def __str__(self):
#         return self.name

# スポットデータ
class Spot(models.Model):
    idx = models.AutoField(primary_key=True)  # 自動インクリメントの整数型インデックス
    name = models.CharField(max_length=256, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    hp = models.TextField()
    tags = models.TextField()

    def __str__(self):
        return self.name
    
# スポットデータ
class Node(models.Model):
    idx = models.AutoField(primary_key=True)  # 自動インクリメントの整数型インデックス
    node = models.BigIntegerField(unique=True)
    name = models.TextField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    tags = models.TextField()

    def __str__(self):
        return self.node

# ユーザが付与した新しいタグ
class AddedTag(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Userとの関係
    tag = models.TextField()  # Tag
    spot = models.ForeignKey(Spot, on_delete=models.CASCADE)  # Spotとの関係
    added_at = models.DateTimeField(auto_now_add=True)  # タグを追加した時間を記録

    def __str__(self):
        return f"{self.user.name} added {self.tag} to {self.spot.name} at {self.added_at}"
    
class Tag(models.Model):
    idx = models.AutoField(primary_key=True)  # 自動インクリメントの整数型インデックス
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Userとの関係
    tag = models.TextField()  # Tag

    def __str__(self):
        return f"{self.user.name if self.user else 'Unknown user'} added {self.tag}"

# 保存されているマップデータ
class Mapdata(models.Model):
    idx = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Userとの関係
    name = models.CharField(max_length=64)
    distance = models.BigIntegerField()
    time = models.BigIntegerField()
    start_spot = models.ForeignKey(Spot, on_delete=models.CASCADE, related_name='start_spot')  # Spotとの関係
    goal_spot = models.ForeignKey(Spot, on_delete=models.CASCADE, related_name='goal_spot')  # Spotとの関係
    via_spots = models.ManyToManyField(Spot, related_name='via_spots')  # Spotと
    aim_tags = models.TextField()  # 検索条件のタグ
    html = models.TextField(null=True, blank=True)  # マップデータのHTML文字列
    created_at = models.DateTimeField(auto_now_add=True)  # 作成日時
 

    def __str__(self):
        return f"{self.name} saved map as name:{self.name}"