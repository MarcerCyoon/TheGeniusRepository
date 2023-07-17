from django.db import models
from django.urls import reverse

# Create your models here.
class Match(models.Model):
    name = models.CharField(max_length=200)
    designer = models.ForeignKey('Designer', on_delete=models.SET_NULL, null=True)
    summary = models.TextField(max_length=2000, help_text="Enter a quick summary of the Match here.")
    rules = models.TextField(max_length=30000, help_text='Enter the rules of the Match here.')
    ORGs = models.ManyToManyField('ORG', verbose_name="ORGs", help_text="Choose all ORGs this Match has appeared in.")
    tags = models.ManyToManyField('Tag', help_text='Choose tags for this match.')

    MATCH_TYPE = (
        ('DM', 'Death Match'),
        ('MM', 'Main Match')
    )

    match_type = models.CharField(max_length=2, choices=MATCH_TYPE, blank=True)
    min_players = models.IntegerField(help_text="Minimum number of players needed to play this match.")
    max_players= models.IntegerField(help_text="Maximum number of players that can play this match. Leave empty if num_players is not a range.", null=True, blank=True)

    class Meta:
        ordering = ['-match_type', 'name'] # reverse match_type order so MMs > DMs
        verbose_name = 'Match'
        verbose_name_plural = 'Matches'

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        """Returns the URL to access a detail record for this book."""
        return reverse('match-detail', args=[str(self.id)])
    
    def display_ORGs(self):
        """
        Create a string for all ORGs this Match has appeared in.
        Necessary for MatchAdmin list display.
        """
        return ', '.join(org.name for org in self.ORGs.all()[:5])
    
    display_ORGs.short_description = 'ORGs'

    def display_tags(self):
        """
        Create a string for the tags of this Match.
        Necessary for MatchAdmin list display.
        """
        return ', '.join(tag.name for tag in self.tags.all()[:5])
    
    display_tags.short_description = 'Tags'


class Designer(models.Model):
    name = models.CharField(max_length=100)
    desc = models.CharField(max_length=500)

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse("designer-detail", args=[str(self.id)])
    

class ORG(models.Model):
    name = models.CharField(max_length=200)
    size = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    main_host = models.ForeignKey('Designer', on_delete=models.SET_NULL, null=True)
    description = models.CharField(max_length=200, help_text="A short description of this ORG.")
    twists = models.TextField(max_length=1000, help_text="List out all relevant twists of this ORG.")

    class Meta:
        ordering = ['start_date']
        verbose_name = 'ORG'
        verbose_name_plural = 'ORGs'

    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=200, help_text='Enter a tag (e.g. \'social deduction\' or \'bidding game\')')

    def __str__(self):
        return self.name
