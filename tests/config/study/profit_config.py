ntrain = 2
variables = {'u': 'Halton()',
             'v': 'Uniform(0.55, 0.6)',
             'w': 'ActiveLearning()',
             'r': 'Independent(0, 1, 0.1)',
             'f': {'kind': 'Output', 'range': 'r'},
             'g': 'Output(r)'}

files = {'param_files': ['mockup.in'],
         'input': 'input.txt',
         'output': 'output.txt'}
run = 'python3 ../mockup.py'
