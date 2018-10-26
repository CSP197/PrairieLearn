import lxml.html
from html import escape
import chevron
import math
import prairielearn as pl
import random


def prepare(element_html, data):
    element = lxml.html.fragment_fromstring(element_html)
    required_attribs = ['answers-name']
    optional_attribs = ['weight', 'correct-answer', 'label', 'suffix', 'display', 'remove-leading-trailing', 'remove-spaces', 'placeholder']
    pl.check_attribs(element, required_attribs, optional_attribs)

    name = pl.get_string_attrib(element, 'answers-name')
    correct_answer = pl.get_string_attrib(element, 'correct-answer', None)

    if correct_answer is not None:
        if name in data['correct_answers']:
            raise Exception('duplicate correct_answers variable name: %s' % name)
        data['correct_answers'][name] = correct_answer


def render(element_html, data):
    element = lxml.html.fragment_fromstring(element_html)
    name = pl.get_string_attrib(element, 'answers-name')
    label = pl.get_string_attrib(element, 'label', None)
    suffix = pl.get_string_attrib(element, 'suffix', None)
    display = pl.get_string_attrib(element, 'display', 'inline')
    remove_leading_trailing = pl.get_boolean_attrib(element, 'remove-leading-trailing', True)
    remove_spaces = pl.get_boolean_attrib(element, 'remove-spaces', False)
    placeholder = pl.get_string_attrib(element, 'placeholder', None)

    if data['panel'] == 'question':
        editable = data['editable']
        raw_submitted_answer = data['raw_submitted_answers'].get(name, None)

        if remove_leading_trailing:
            if remove_spaces:
                space_hint = 'Leading, trailing spaces and whitespaces between text will be removed from your answer.'
            else:
                space_hint = 'Leading and trailing spaces will be removed from your answer.'
        else:
            if remove_spaces:
                space_hint = 'Whitespaces between text will be removed but leading and trailing spaces will be left as part of your answer.'
            else:
                space_hint = 'Leading and trailing spaces will be left as part of your answer.'

        # Get info strings
        info_params = {'format': True, 'add_hint_space': space_hint}
        with open('pl-string-input.mustache', 'r', encoding='utf-8') as f:
            template = f.read()
            info = chevron.render(template, info_params).strip()
            info_params.pop('format', None)

        html_params = {
            'question': True,
            'name': name,
            'label': label,
            'suffix': suffix,
            'remove-leading-trailing': remove_leading_trailing,
            'remove-spaces': remove_spaces,
            'editable': editable,
            'info': info,
            'placeholder': placeholder,
            'uuid': pl.get_uuid()
        }

        partial_score = data['partial_scores'].get(name, {'score': None})
        score = partial_score.get('score', None)
        if score is not None:
            try:
                score = float(score)
                if score >= 1:
                    html_params['correct'] = True
                elif score > 0:
                    html_params['partial'] = math.floor(score * 100)
                else:
                    html_params['incorrect'] = True
            except Exception:
                raise ValueError('invalid score' + score)

        if display == 'inline':
            html_params['inline'] = True
        elif display == 'block':
            html_params['block'] = True
        else:
            raise ValueError('method of display "%s" is not valid (must be "inline" or "block")' % display)
        if raw_submitted_answer is not None:
            html_params['raw_submitted_answer'] = escape(raw_submitted_answer)
        with open('pl-string-input.mustache', 'r', encoding='utf-8') as f:
            html = chevron.render(f, html_params).strip()

    elif data['panel'] == 'submission':
        parse_error = data['format_errors'].get(name, None)
        html_params = {
            'submission': True,
            'label': label,
            'parse_error': parse_error,
            'uuid': pl.get_uuid()
        }

        if parse_error is None:
            # Get submitted answer, raising an exception if it does not exist
            a_sub = data['submitted_answers'].get(name, None)
            if a_sub is None:
                raise Exception('submitted answer is None')

            # If answer is in a format generated by pl.to_json, convert it
            # back to a standard type (otherwise, do nothing)
            a_sub = pl.from_json(a_sub)

            html_params['suffix'] = suffix
            html_params['a_sub'] = a_sub
        else:
            raw_submitted_answer = data['raw_submitted_answers'].get(name, None)
            if raw_submitted_answer is not None:
                html_params['raw_submitted_answer'] = escape(raw_submitted_answer)

        partial_score = data['partial_scores'].get(name, {'score': None})
        score = partial_score.get('score', None)
        if score is not None:
            try:
                score = float(score)
                if score >= 1:
                    html_params['correct'] = True
                elif score > 0:
                    html_params['partial'] = math.floor(score * 100)
                else:
                    html_params['incorrect'] = True
            except Exception:
                raise ValueError('invalid score' + score)

        with open('pl-string-input.mustache', 'r', encoding='utf-8') as f:
            html = chevron.render(f, html_params).strip()
    elif data['panel'] == 'answer':
        a_tru = pl.from_json(data['correct_answers'].get(name, None))
        if a_tru is not None:
            html_params = {'answer': True, 'label': label, 'a_tru': a_tru, 'suffix': suffix}
            with open('pl-string-input.mustache', 'r', encoding='utf-8') as f:
                html = chevron.render(f, html_params).strip()
        else:
            html = ''
    else:
        raise Exception('Invalid panel type: %s' % data['panel'])

    return html


def parse(element_html, data):
    element = lxml.html.fragment_fromstring(element_html)
    name = pl.get_string_attrib(element, 'answers-name')

    # Get submitted answer or return parse_error if it does not exist
    a_sub = data['submitted_answers'].get(name, None)
    if a_sub is None:
        data['format_errors'][name] = 'No submitted answer.'
        data['submitted_answers'][name] = None
        return

    if not a_sub:
        data['format_errors'][name] = 'Invalid format. The submitted answer was left blank.'
        data['submitted_answers'][name] = None
    else:
        data['submitted_answers'][name] = pl.to_json(a_sub)


def grade(element_html, data):
    element = lxml.html.fragment_fromstring(element_html)
    name = pl.get_string_attrib(element, 'answers-name')

    # Get weight
    weight = pl.get_integer_attrib(element, 'weight', 1)

    # Get remove-spaces option
    remove_spaces = pl.get_boolean_attrib(element, 'remove-spaces', False)

    # Get remove-leading-trailing option
    remove_leading_trailing = pl.get_boolean_attrib(element, 'remove-leading-trailing', True)

    # Get true answer (if it does not exist, create no grade - leave it
    # up to the question code)
    a_tru = pl.from_json(data['correct_answers'].get(name, None))
    if a_tru is None:
        return

    # Get submitted answer (if it does not exist, score is zero)
    a_sub = data['submitted_answers'].get(name, None)
    if a_sub is None:
        data['partial_scores'][name] = {'score': 0, 'weight': weight}
        return
    # If submitted answer is in a format generated by pl.to_json, convert it
    # back to a standard type (otherwise, do nothing)
    a_sub = pl.from_json(a_sub)

    # Remove the leading and trailing characters
    if (remove_leading_trailing):
        a_sub = a_sub.strip()

    # Remove the blank spaces between characters
    if (remove_spaces):
        a_sub = a_sub.replace(' ', '')

    if a_tru == a_sub:
        data['partial_scores'][name] = {'score': 1, 'weight': weight}
    else:
        data['partial_scores'][name] = {'score': 0, 'weight': weight}


def test(element_html, data):
    element = lxml.html.fragment_fromstring(element_html)
    name = pl.get_string_attrib(element, 'answers-name')
    weight = pl.get_integer_attrib(element, 'weight', 1)

    # Get correct answer
    a_tru = data['correct_answers'][name]

    # If correct answer is in a format generated by pl.to_json, convert it
    # back to a standard type (otherwise, do nothing)
    a_tru = pl.from_json(a_tru)

    result = random.choices(['correct', 'incorrect', 'invalid'], [5, 5, 1])[0]

    if result == 'correct':
        data['raw_submitted_answers'][name] = a_tru
        data['partial_scores'][name] = {'score': 1, 'weight': weight}
    elif result == 'incorrect':
        data['raw_submitted_answers'][name] = a_tru + str((random.randint(1, 11) * random.choice([-1, 1])))
        data['partial_scores'][name] = {'score': 0, 'weight': weight}
    elif result == 'invalid':
        data['raw_submitted_answers'][name] = ''
        data['format_errors'][name] = 'invalid'
    else:
        raise Exception('invalid result: %s' % result)
