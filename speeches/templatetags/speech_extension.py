# -*- coding: utf-8 -*-

from collections import defaultdict
from heapq import nlargest
from operator import itemgetter
from django import template
import re
from django.utils.html import strip_tags
import json
from unicodedata import normalize

register = template.Library()


@register.assignment_tag
def get_top_speakers(count=9):
    from speeches.models import Speech, Speaker
    from django.db.models import Count

    top_speakers_list = Speech.objects.values('speaker').annotate(count=Count('speaker')).order_by('speaker').order_by(
        '-count')[0:count]
    top_speakers = []
    for speaker in top_speakers_list:
        the_speaker = Speaker.objects.get(pk=speaker['speaker'])
        # setattr(the_speaker, 'count', speaker['count])
        the_speaker.count = speaker['count']
        top_speakers.append(the_speaker)
    return top_speakers


@register.assignment_tag
def get_common_words(count=20):
    from speeches.models import Speech

    r_punctuation = re.compile(r"[^\s\w0-9'’—-]", re.UNICODE)
    r_whitespace = re.compile(r'[\s—]+')
    STOPWORDS = frozenset([
		'00', '0', 'esas', 'quiero', 'haciendo', 'otro', 'otra', 'otras', 'toda', 'toditos',
		'aquí', 'sus', 'hace', 'con', 'creo', '0000', 'dos', 'estos', 'fue', 'ahí',
		'contra', 'de', 'durante', 'en', 'hacia', 'hasta', 'mediante', 'según', 'so', 'tras',
		'decir', 'parte', 'años', 'esos', 'les', 'unos', 'este', 'ser', 'sino', 'entonces',
		'hecho', 'ustedes', 'van', 'sea', 'cada', 'debe', 'manera', 'nos', 'ellos', 'sin',
		'las', 'esto', 'pero', 'eso', 'una', 'porque', 'hay', 'esta', 'están', 'donde',
		'más', 'son', 'todos', 'ese', 'estamos', 'hoy', 'como', 'han', 'tenemos', 'hemos',
		'momento', 'puede', 'señor', 'señora', 'haciendonos', 'día', 'a', 'ante', 'bajo', 'cabe',
		'no', 'No', 'el', 'Y', 'si', 'o', 'y', 'estas', 'debido', 'ya',
		'qué', 'todo', 'esa', 'desde', 'del', 'para', 'uno', 'por', 'que', 'los',
		'solo', 'dentro', 'podemos', 'algunos', 'estar', 'ahora', 'tema', 'mismo', 'sólo', 'temas',
		'tiene', 'muy', 'está', 'cuando', 'nosotros', 'doctor', 'hacer', 'tienen', 'sobre', 'vamos',
		'tres', 'así', 'ver', 'bien', 'cómo', 'entre', 'mucho', 'otros', 'todas', '000',
		'voy', 'sido', 'era', 'vez', 'unas', 'cosas', 'general', 'tanto', 'frente', 'muchas',
		'tener', 'tipo', 'mil', 'estoy', 'gran', 'san', 'tan', 'tengo', 'cual', 'dice',
		'mayor', 'allá', 'solamente', 'bueno', 'primeramente', 'pues', 'consiguiente', 'debido', 'cuenta', 'menos',
	])

    #speeches = Speech.objects.all()
    #speeches = Speech.objects.order_by('-id')[0]
    speeches = Speech.objects.order_by('-id')[0:10]

    word_counts = defaultdict(int)
    total_count = 0

    for speech in speeches:
        for word in r_whitespace.split(r_punctuation.sub(' ', normalize('NFC', strip_tags(speech.text).lower()) )):
            if word not in STOPWORDS and len(word) > 2:
                word_counts[word] += 1
                total_count += 1

    word_counts = {word: count for word, count in word_counts.items()}
    most_common_words = nlargest(90, word_counts.items(), key=itemgetter(1))#aqui se coloca el numero aproximado para mostrar
    return json.dumps(most_common_words)
