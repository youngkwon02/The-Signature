from django.db import models

class UserInfo(models.Model):
    user_seq = models.AutoField(primary_key=True)
    user_email = models.EmailField(max_length=254, verbose_name="user_email", blank=False)
    first_name_kr = models.CharField(max_length=16, verbose_name="first_name_kr")
    last_name_kr = models.CharField(max_length=32, verbose_name="last_name_kr")
    first_name_en = models.CharField(max_length=32, verbose_name="first_name_en")
    last_name_en = models.CharField(max_length=32, verbose_name="last_name_en")
    user_password = models.CharField(max_length=512, verbose_name="user_passwd")
    register_dttm = models.DateField(auto_now_add=True, verbose_name="Register_date")
    is_active = models.BooleanField(default=False)
    
    def __str__(self):
        return self.user_email
