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
	
def parse_strikethrough(value):
	lst = value.split("~~")

	if len(lst) > 2:
		string = ""
		for i in range(0, len(lst)):
			string += lst[i]

			if i != len(lst) - 1:
				if i % 2 == 0:
					string += "<s>"
				else:
					string += "</s>"
		
		return string
	else:
		return "~~".join(lst)

def parse_spoilers(value):
	lst = value.split("||")

	if len(lst) > 2:
		string = ""
		for i in range(0, len(lst)):
			string += lst[i]

			if i != len(lst) - 1:
				if i % 2 == 0:
					string += '<span class="spoiler">'
				else:
					string += "</span>"
					
		return string
	else:
		return "||".join(lst)

def parse_emojis(value):
	# this is up there as some of the worst and least Pythonic code I've written ;;
	# cut me some slack I tried so many things and came to the conclusion I just
	# had to manually for loop through strings :sob: I am stupid
	import copy
	emoji = False
	number = False
	start = -1
	number_start = -1
	end = -1
	original = copy.deepcopy(value)
	
	for i, chr in enumerate(original):
		if not emoji:
			if chr == ":" and i != 0:
				if original[i-1] == "<":
					# detected start of emoji
					emoji = True
					start = i-1
		else:
			if not number:
				if chr == ":":
					# detected start of number string in emoji that corresponds to emoji ID
					number = True
					number_start = i+1
			else:
				if chr == ">":
					# the emoji string has ended
					end = i
					numbers = original[number_start:end]

					def is_a_number(n):
						try:
							int(n)
						except:
							return False
						return True

					if is_a_number(numbers):
						# if the numbers actually form a string of integers, we have (probably) detected an emoji
						alt = original[start+1:number_start] # we want the alt to be in the form of :thonk: (surrounded by colons)
						to_be_replaced = original[start:end+1] # to_be_replaced is just the whole string
						link = f"https://cdn.discordapp.com/emojis/{numbers}.png?size=160"
						string = f'<img src="{link}" class="emoji" alt="{alt}"></img>'
						value = value.replace(to_be_replaced, string)
					
					emoji = False
					number = False
					start = -1
					number_start = -1
					end = -1

	return value

@register.filter(name='lookup')
def lookup(value, key):
    return value.get(key)

@register.filter
@stringfilter
def discordify(value):
	"""
	We are going to custom-implement underlines
	and strikethrough and spoiler text and even
	god damn emojis because I am insane.
	"""
	
	html = parse_underlines(value)
	html = parse_strikethrough(html)
	html = parse_spoilers(html)
	html = parse_emojis(html)

	return mark_safe(html)

@register.filter
@stringfilter
def org_name(value):
	value = value.replace(":", "").replace("'", "").replace("-", " ")
	value = [v for v in value.split(" ") if v != ""] # remove empty strings
	return "_".join(value).lower()