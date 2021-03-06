"""This module contains runners for domain codes.

This is used to run domain code via Python functions or
local and distributed systems.
"""
import os
import sys
import subprocess
import multiprocessing as mp
from tqdm import tqdm

try:
    from profit import config, read_input
except ImportError:
    pass


class PythonFunction:
    def __init__(self, function):
        self.function = function

    def start(self):
        from numpy import array, savetxt
        nrun = config.eval_points.shape[1]

        # if present, use progress bar
        kruns = tqdm(range(nrun))

        cwd = os.getcwd()

        try:
            os.chdir(config.base_dir)
            output = [] # TODO: make this more efficient with preallocation based on shape
            for krun in kruns:
                res = self.function(config.eval_points[:, krun])
                output.append([krun, res])
            savetxt('output.txt', array(output))
        finally:
            os.chdir(cwd)


def spawn(args):
    cmd = args[0]
    fulldir = args[1]
    print(fulldir)
    print(cmd)
    return cmd, subprocess.call(cmd, cwd=fulldir,
                      stdout=open(os.path.join(fulldir,'stdout.txt'),'w'),
                      stderr=open(os.path.join(fulldir,'stderr.txt'),'w'))


class LocalCommand:
    def __init__(self, command, ntask=1, run_dir='run', base_dir='.'):
        self.command = ' '.join([os.path.abspath(os.path.join(base_dir, s))
                                 if s.startswith('.') else s for s in command.split()])
        self.ntask = min(ntask, mp.cpu_count())
        self.run_dir = run_dir

    def start(self, nruns):
        p = mp.Pool(self.ntask)
        print("Running on {} core(s). Available cores: {}".format(self.ntask, mp.cpu_count()))

        args = []
        for krun in range(nruns):
            fulldir = os.path.join(self.run_dir, str(krun).zfill(3))
            if os.path.isdir(fulldir):
                cmd = self.command.split()
                if cmd[0].endswith('.py'):
                    cmd.insert(0, sys.executable)
                args.append((cmd, fulldir))
        p.map(spawn, args)

    def start_single(self, single_run_dir):
        p = mp.Pool(self.ntask)
        cmd = self.command.split()
        if cmd[0].endswith('.py'):
            cmd.insert(0, sys.executable)
        p.map(spawn, [(cmd, single_run_dir)])


class Slurm:
    def __init__(self, config):
        self.eval_points = read_input(config['files']['input'])
        if config['runner_backend'] == 'slurm':
          from .backend.slurm import slurm_backend
          self.backend = slurm_backend()
          if 'slurm' in config:
            self.backend.write_slurm_scripts(num_experiments=self.eval_points.shape[1], slurm_config=config['slurm'],jobcommand=config['run'])
          else:
            print('''cannot write slurm scripts, please provide slurm details:
  runner_backend: slurm
  slurm:
      tasks_per_node: 36
      partition: compute
      time: 00:10:00
      account: xy123''')
        else:
          self.backend = None
    def start(self):
        if self.backend is not None:
          self.backend.call_run()


class Runner:
    def __init__(self, config):
        if config['run']:
            print(config['run'])
            return LocalCommand(config['run'])
