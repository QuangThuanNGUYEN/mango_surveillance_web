from django.db import models

class MangoThreat(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    image = models.CharField(max_length=100) 
    details = models.TextField()  

    def __str__(self):
        return self.name