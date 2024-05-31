from django.db import models


class Account(models.Model):
    Username = models.CharField(max_length=10, primary_key=True)
    Password = models.CharField(max_length=10)
    Wins = models.IntegerField()
    Loses = models.IntegerField()
    Draws = models.IntegerField()
    Points = models.IntegerField()
    Color = models.CharField(max_length=6)
    Bandate = models.CharField(max_length=11)
    class Meta:
        managed = False
        db_table = 'Accounts'
    
    