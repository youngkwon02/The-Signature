from django.db import models

class preservedResult(models.Model):
    result_seq = models.AutoField(primary_key=True)
    owner_email = models.EmailField(max_length=254, verbose_name="user_email", blank=False)
    owner_last_name_kr = models.CharField(max_length=32, verbose_name="last_name_kr")
    result_path = models.TextField(default=None)
    alpha_path = models.TextField(default=None)
    preserve_dttm = models.DateTimeField(auto_now_add=True, verbose_name="preserve_date")
    is_removed = models.TextField(default="F")
    is_rep = models.TextField(default="F")
    
    def __str__(self):
        return self.alpha_path

class preservedWatermark(models.Model):
    seq = models.AutoField(primary_key=True)
    owner_email = models.EmailField(max_length=254, verbose_name="user_email", blank=False)
    owner_last_name_kr = models.CharField(max_length=32, verbose_name="last_name_kr")
    result_path = models.TextField(default=None)
    upload_date = models.DateTimeField(auto_now_add=True, verbose_name="watermark_result_upload_date")

    def __str__(self):
        return self.image
