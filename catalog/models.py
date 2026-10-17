from django.db import models
from django.db.models import Index
from django.urls import reverse

# Create your models here.
class Ruleset(models.Model):
    alias = models.CharField(max_length=200, blank=True, null=True, help_text="Write the alias for this game for this specific Ruleset, if it had one.")
    ORG = models.ForeignKey('ORG', on_delete=models.SET_NULL, null=True, help_text="Choose the ORG this version of the Ruleset has appeared in.")
    episode = models.CharField(max_length=100, help_text="Details about the episode in which this Ruleset was played (such as 'MM7', 'Episode 6', 'DM6')")
    rules = models.TextField(max_length=50000, help_text='Enter the rules for the Ruleset here.')
    tags = models.ManyToManyField('Tag', help_text='Choose tags for this Ruleset.', blank=True)
    player_count = models.PositiveIntegerField(help_text="Number of players needed to play this match with this Ruleset.")
    ordering = models.IntegerField(help_text="Helper integer used to give rulesets of the same match a proper order. If there is a tie in order, the ruleset that was created first takes default precedence.", default=0)

    match = models.ForeignKey('Match', on_delete=models.SET_NULL, null=True, related_name="rulesets")

    class Meta:
        verbose_name = 'Ruleset'
        verbose_name_plural = 'Rulesets'

    def __str__(self):
        if self.alias is not None:
            return self.alias + " (" + self.ORG.name + ")"
        else:
            return self.match.name + " (" + self.ORG.name + ")"

    def display_tags(self):
        """
        Create a string for the tags of this Ruleset.
        Necessary for RulesetAdmin list display.
        """
        return ', '.join(tag.name for tag in self.tags.all())
    
    display_tags.short_description = 'Tags'

class Match(models.Model):
    name = models.CharField(max_length=200)
    designers = models.ManyToManyField('Designer', verbose_name="Designer(s)")
    summary = models.TextField(max_length=2000, help_text="Enter a quick summary of the Match here.")

    MATCH_TYPE = (
        ('DM', 'Death Match'),
        ('MM', 'Main Match')
    )

    match_type = models.CharField(max_length=2, choices=MATCH_TYPE)

    see_also = models.ManyToManyField('Match', help_text="Note games that are inspired by or are similar to this game.", verbose_name="See Also", blank=True)
    awards = models.ManyToManyField('YearAward', help_text='Choose all awards this design has won.', blank=True)

    # TODO: maybe make a new field that is "Award Level" so that we can set 1st, 2nd, 3rd etc.? do it here instead of in Awards so I don't have to make
    # awards a m2m with like a trillion extra objects
    # wait fuck this doesn't work if something wins multiple awards I'm going to go scream into the void
    # probably just tie it to the award then :(

    class Meta:
        ordering = ['-match_type', 'name'] # reverse match_type order so MMs > DMs
        verbose_name = 'Match'
        verbose_name_plural = 'Matches'
        indexes = [
            Index(fields=['name', 'match_type'])
        ]

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        """Returns the URL to access a detail record for this match."""
        return reverse('match-detail', args=[str(self.pk)])
    
    def display_designers(self):
        """
        Create a string for all designers that designed this Match.
        Necessary for MatchAdmin list display.
        """
        return ', '.join(designer.name for designer in self.designers.all()[:3])

    display_designers.short_description = 'Designer(s)'
    
    def display_ORGs(self):
        """
        Create a string for all ORGs this Match has appeared in.
        Necessary for MatchAdmin list display.
        """
        return ', '.join(org.name for org in [rule.ORG for rule in self.rulesets.all()[:5]])
    
    display_ORGs.short_description = 'ORGs'

class Designer(models.Model):
    name = models.CharField(max_length=100)
    desc = models.CharField(max_length=500)

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse("designer-detail", args=[str(self.pk)])
    
    class Meta:
        ordering = ['name']
    
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
    
    def get_absolute_url(self):
        return reverse("org-detail", args=[str(self.pk)])

class Tag(models.Model):
    name = models.CharField(max_length=200, help_text='Enter a tag (e.g. \'social deduction\' or \'bidding\')')
    description = models.CharField(max_length=1000, help_text='Enter a description for the tag.', null=True, blank=True)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class YearAward(models.Model):
    award = models.ForeignKey("Award", on_delete=models.SET_NULL, null=True)
    # level = models.CharField(max_length=20)

    import datetime
    YEAR_CHOICES = []
    for r in range(2010, (datetime.datetime.now().year+1)):
        YEAR_CHOICES.append((r,r))

    year = models.IntegerField(choices=YEAR_CHOICES, default=datetime.datetime.now().year)

    def __str__(self):
        return self.award.name + " " + str(self.year)

    class Meta:
        ordering = ['year', 'award']

class Award(models.Model):
    name = models.CharField(max_length=200, help_text="Enter the name of this award (e.g. \'Most Fun MM\').")
    description = models.CharField(max_length=1000, help_text='Enter the description of this award.')
    priority = models.PositiveIntegerField(default=100, help_text="Priority value for awards ordering in view.")

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['priority']