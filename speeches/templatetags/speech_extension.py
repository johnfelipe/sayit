# -*- coding: utf-8 -*-

from collections import defaultdict
from heapq import nlargest
from operator import itemgetter
from django import template
import re
from django.utils.html import strip_tags
import json
from unicodedata import normalize
from instances.views import InstanceViewMixin

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
def get_common_words(instance, count=20):
    from speeches.models import Speech

    r_punctuation = re.compile(r"[^\s\w0-9'’—-]", re.UNICODE)
    r_whitespace = re.compile(r'[\s—]+')
    STOPWORDS = frozenset([
		##'00', '0', 'esas', 'quiero', 'haciendo', 'otro', 'otra', 'otras', 'toda', 'toditos',
		##'aquí', 'sus', 'hace', 'con', 'creo', '0000', 'dos', 'estos', 'fue', 'ahí',
		##'contra', 'de', 'durante', 'en', 'hacia', 'hasta', 'mediante', 'según', 'so', 'tras',
		##'decir', 'parte', 'años', 'esos', 'les', 'unos', 'este', 'ser', 'sino', 'entonces',
		##'hecho', 'ustedes', 'van', 'sea', 'cada', 'debe', 'manera', 'nos', 'ellos', 'sin',
		##'las', 'esto', 'pero', 'eso', 'una', 'porque', 'hay', 'esta', 'están', 'donde',
		##'más', 'son', 'todos', 'ese', 'estamos', 'hoy', 'como', 'han', 'tenemos', 'hemos',
		##'momento', 'puede', 'señor', 'señora', 'haciendonos', 'día', 'a', 'ante', 'bajo', 'cabe',
		##'no', 'No', 'el', 'Y', 'si', 'o', 'y', 'estas', 'debido', 'ya',
		##'qué', 'todo', 'esa', 'desde', 'del', 'para', 'uno', 'por', 'que', 'los',
		##'solo', 'dentro', 'podemos', 'algunos', 'estar', 'ahora', 'tema', 'mismo', 'sólo', 'temas',
		##'tiene', 'muy', 'está', 'cuando', 'nosotros', 'doctor', 'hacer', 'tienen', 'sobre', 'vamos',
		##'tres', 'así', 'ver', 'bien', 'cómo', 'entre', 'mucho', 'otros', 'todas', '000',
		##'voy', 'sido', 'era', 'vez', 'unas', 'cosas', 'general', 'tanto', 'frente', 'muchas',
		##'tener', 'tipo', 'mil', 'estoy', 'gran', 'san', 'tan', 'tengo', 'cual', 'dice',
		##'mayor', 'allá', 'solamente', 'bueno', 'primeramente', 'pues', 'consiguiente', 'debido', 'cuenta', 'menos',

       # nltk.corpus.stopwords.words('english')
        u'i', 'ume', u'my', u'myself', u'we', u'our', u'ours', u'ourselves', u'you', u'your',
        u'yours', u'yourself', u'yourselves', u'he', u'him', u'his', u'himself', u'she', u'her',
        u'hers', u'herself', u'it', u'its', u'itself', u'they', u'them', u'their', u'theirs',
        u'themselves', u'what', u'which', u'who', u'whom', u'this', u'that', u'these', u'those',
        u'am', u'is', u'are', u'was', u'were', u'be', u'been', u'being', u'have', u'has', u'had',
        u'having', u'do', u'does', u'did', u'doing', u'a', u'an', u'the', u'and', u'but', u'if',
        u'or', u'because', u'as', u'until', u'while', u'of', u'at', u'by', u'for', 'with',
        'about', 'against', 'between', 'into', 'through', 'during', 'before', u'after',
        u'above', u'below', u'to', u'from', u'up', u'down', u'in', u'out', u'on', u'off', u'over',
        u'under', u'again', u'further', u'then', u'once', u'here', u'there', u'when', u'where',
        u'why', u'how', u'all', u'any', u'both', u'each', u'few', u'more', u'most', u'other',
        u'some', u'such', u'no', u'nor', 'unot', u'only', u'own', u'same', u'so', u'than', u'too',
        u'very', u's', u't', u'can', u'will', u'just', u'don', u'should', u'now',
        # @see https://github.com/rhymeswithcycle/openparliament/blob/master/parliament/text_analysis/frequencymodel.py
        u"it's", u"we're", u"we'll", u"they're", u"can't", u"won't", u"isn't", "don't", "he's",
        u"she's", u"i'm", u"aren't", "government", "house", "committee", "would", "speaker",
        "motion", "mr", u"mrs", u"ms", u"member", u"minister", u"canada", u"members", u"time",
        u"prime", u"one", u"parliament", u"us", u"bill", u"act", u"like", u"canadians", u"people",
        u"said", u"want", u"could", u"issue", u"today", u"hon", u"order", u"party", u"canadian",
        u"think", u"also", u"new", u"get", u"many", u"say", u"look", u"country", u"legislation",
        u"law", u"department", u"two", u"day", u"days", u"madam", u"must", u"that's", u"okay",
        u"thank", u"really", u"much", u"there's", u"yes", u"no",
        # HTML tags
        'sup',
        # Nova Scotia
        u"nova", u"scotia", u"scotians", u"province", u"honourable", u"premier",
        # artifacts
        u"\ufffd", u"n't",
        # spanish
        u'00', u'0', u'esas', u'quiero', u'haciendo', u'otro', u'otra', u'otras', u'toda', u'toditos',
        u'aquí', u'sus', u'hace', u'con', u'creo', u'0000', u'dos', u'estos', u'fue', u'ahí', u'contra',
        u'de', u'durante', u'en', u'hacia', u'hasta', u'mediante', u'según', u'so', u'tras', u'decir',
        u'parte', u'años', u'esos', u'les', u'unos', u'este', u'ser', u'sino', u'entonces', u'hecho',
        u'ustedes', u'usted', u'van', u'sea', u'cada', u'debe', u'manera', u'nos', u'ellos', u'sin', u'las',
        u'esto', u'pero', u'eso', u'una', u'porque', u'hay', u'esta', u'están', u'está', u'donde', u'más', u'son',
        'todos', 'ese', 'estamos', 'hoy', 'como', 'han', 'tenemos', 'hemos', 'momento', 'puede',
        u'señor', u'señora', u'haciendonos', u'día', u'a', u'ante', u'bajo', u'cabe', u'no', u'No', u'el',
        u'Y', u'si', u'o', u'y', u'estas', u'debido', u'ya', u'qué', u'todo', u'esa', u'desde', u'del', u'para',
        u'uno', u'por', u'que', u'los', u'solo', u'dentro', u'podemos', u'algunos', u'estar', u'ahora',
        u'tema', u'mismo', u'sólo', u'temas', u'tiene', u'muy', u'cuando', u'nosotros', u'doctor',
        u'hacer', u'tienen', u'sobre', u'vamos', u'tres', u'así', u'ver', u'bien', u'cómo', u'entre', u'mucho',
        u'otros', 'todas', '000', 'voy', 'sido', 'era', 'vez', 'unas', 'cosas', 'general', 'tanto',
        u'frente', u'muchas', u'tener', u'tipo', u'mil', u'estoy', u'gran', u'san', u'tan', u'tengo', u'cual',
        u'dice', u'mayor', u'allá', u'solamente', u'bueno', u'primeramente', u'pues', u'consiguiente',
        u'debido', u'cuenta', u'menos', u'también', u'palabra',
	])

    #speeches = Speech.objects.all()
    #speeches = Speech.objects.order_by('-id')[0]
    speeches = Speech.objects.for_instance(instance).order_by('-id')[0:10]

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
