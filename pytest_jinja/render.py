from jinja2 import Environment, FileSystemLoader
import os
import json
from datetime import datetime


def read_json(json_f):
    with open(json_f) as fh:
        data = json.load(fh)

    context = {
        'report_name'     : 'Race Test Report',
        'report_datetime' : datetime.\
                                fromtimestamp(data['created']).\
                                strftime("%Y-%m-%d %I:%M:%S"),
        'duration'        : data['duration'],
        'operating_system': data['environment']['Platform'],
        'python_version'  : data['environment']['Python'],
        'n_passed'        : data['summary']['passed'],
        'n_failed'        : data['summary']['failed'],
        'n_skipped'       : 0,  # TODO
        'n_errors'        : 0,  # TODO
        'n_xfail'         : 0,  # TODO
        'n_xpass'         : 0,  # TODO
        'n_total'         : data['summary']['total']
    }
    context['rel_total_pass'] = context['n_passed'] / (context['n_total'] - context['n_skipped'])

    tests = get_tests(data)
    sort_by_race = sort_tests(tests, 'random_seed')
    races = [create_race(key, val) for key, val in sort_by_race.items()]
    context['races'] = races
    context['n_races_passed'] = sum([1 for race in races if race['n_total_passed'] == race['n_total']])
    context['n_races_failed'] = sum([1 for race in races if race['n_total_passed'] != race['n_total']])
    return context


def create_race(name, tests):
    sort_by_model = sort_tests(tests, 'model')
    model_sets = [create_model_set(key, val) for key, val in sort_by_model.items()]
    d = {
        'name'             : name,
        'model_sets'       : model_sets,
        'n_model_sets'     : len(model_sets),
        'n_total'          : len(tests),
        'n_model_sets_pass': sum([1 for model_set in model_sets if model_set['n_passed'] == len(model_set['tests'])]),
        'n_model_sets_fail': sum([1 for model_set in model_sets if model_set['n_passed'] != len(model_set['tests'])]),
        'n_total_passed'   : sum([model_set['n_passed']  for model_set in model_sets]),
        'n_total_failed'   : sum([model_set['n_failed']  for model_set in model_sets]),
        'n_total_skipped'  : sum([model_set['n_skipped'] for model_set in model_sets]),
        'n_total_errors'   : sum([model_set['n_errors']  for model_set in model_sets]),
        'n_total_xfail'    : sum([model_set['n_xfail']   for model_set in model_sets]),
        'n_total_xpass'    : sum([model_set['n_xpass']   for model_set in model_sets])
    }
    d['rel_total_pass'] = d['n_total_passed'] / (d['n_total'] - d['n_total_skipped'])
    return d


def create_model_set(name, tests):
    d = {
        'name'     : name,
        'tests'    : tests,
        'n_passed' : sum([1 for test in tests if test['result'] == 'passed']),
        'n_failed' : sum([1 for test in tests if test['result'] == 'failed']),
        'n_skipped': sum([1 for test in tests if test['result'] == 'skipped']),
        'n_errors' : sum([1 for test in tests if test['result'] == 'error']),
        'n_xfail'  : sum([1 for test in tests if test['result'] == 'xfail']),
        'n_xpass'  : sum([1 for test in tests if test['result'] == 'xpass']),
        'n_total'  : len(tests)
    }
    d['rel_pass'] = d['n_passed'] / (d['n_total'] - d['n_skipped'])
    return d


def parse_test(test):
    d = {
        'nodeid'      : test['nodeid'],
        'result'      : test['outcome'],
        'random_seed' : test['metadata']['random_seed'],
        'model'       : test['metadata']['model'],
        'duration'    : round(test['setup']['duration'] + 
                              test['call']['duration'] + 
                              test['teardown']['duration'], 3)
    }
    try:
        d['log'] = test['call']['longrepr']
    except:
        d['log'] = 'No log found.'
    return d


def sort_tests(tests, criteria):
    groups = {}
    for test in tests:
        key = test[criteria]
        if key in groups.keys():
            groups[key].append(test)
        else:
            groups[key] = [test]
    return groups


def get_tests(data):
    return [parse_test(test) for test in data['tests']]


def get_passes(tests):
    return [test for test in tests if test['result'] == 'passed']


def get_fails(tests):
    return [test for test in tests if test['result'] == 'failed']   

if __name__ == '__main__':
    data = read_json('resources/report.json')
    env = Environment( loader = FileSystemLoader('templates') )
    template = env.get_template('table-row.html')

    out_f = 'rendered.html'
    with open(out_f, 'w') as fh:
        fh.write(template.render(data))