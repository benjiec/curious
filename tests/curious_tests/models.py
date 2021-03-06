"""
Testing models. Model idea stolen from Django documentation.
"""

from django.db import models


class Blog(models.Model):
  name = models.CharField(max_length=100)

  def __unicode__(self):
    return self.name

  @staticmethod
  def authors(instances, filters=None):
    q = Author.objects.filter(entry__blog_id__in=[x.id for x in instances])
    if filters:
      q = filters(q)
    r = []
    # this is very inefficient, since it requires separate N queries by Django
    # to fetch related Entry from N authors. so when not testing, don't do
    # this. instead you should just use two separate relationships, with two
    # queries, to go from Blog to Author.
    for author in q:
      for entry in author.entry_set.all():
        r.append((author, entry.blog_id))
    return r


class LivingThing(models.Model):
  class Meta:
    abstract = True

  alive = models.BooleanField(default=True)


class Person(LivingThing):
  gender = models.CharField(max_length=50)

  @property
  def example_property_field(self):
    return 'The owls are not what they seem'


class Author(models.Model):
  name = models.CharField(max_length=50)
  age = models.IntegerField(null=True)
  friends = models.ManyToManyField('self')

  person = models.OneToOneField(Person, null=True)

  def __unicode__(self):
    return self.name


class Entry(models.Model):
  blog = models.ForeignKey(Blog)
  headline = models.CharField(max_length=255)
  authors = models.ManyToManyField(Author)
  response_to = models.ForeignKey('self', null=True, related_name='responses')
  related_blog_id = models.PositiveIntegerField(null=True)

  def __unicode__(self):
    return self.headline


class Comment(models.Model):
  entry = models.ForeignKey(Entry)
  comment = models.CharField(max_length=50)

  def __unicode__(self):
    return self.comment
