from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

register = template.Library()

def parse_underlines(value):
	lst = value.split("__")

	if len(lst) > 2:
		string = ""
		for i in range(0, len(lst)):
			string += lst[i]

			if i != len(lst) - 1:
				if i % 2 == 0:
					string += "<u>"
				else:
					string += "</u>"
		
		return string
	else:
		return "__".join(lst)

def parse_spoilers(value):
	lst = value.split("||")

	if len(lst) > 2:
		string = ""
		for i in range(0, len(lst)):
			string += lst[i].strip()

			if i != len(lst) - 1:
				if i % 2 == 0:
					string += '<span class="spoiler">'
				else:
					string += "</span>"
					
		return string
	else:
		return "||".join(lst)
	
def parse_blockquote(value):
	if value.startswith(">"):
		value = value.replace(">", "").strip()
		value = "<blockquote>" + value + "</blockquote>"
	return value

# TODO: parse emojis properly and display them as small images
def parse_emojis(value):
	import re

	result = re.search('<:(.*)>', value)
	print(result.group(1))

	return value

@register.filter
@stringfilter
def discordify(value):
	"""
	We are going to custom-implement underlines
	and spoiler text because I am insane.
	"""
	
	html = parse_underlines(value)
	html = parse_spoilers(html)
	html = parse_blockquote(html)

	return mark_safe(html)