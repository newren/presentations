#!/usr/bin/env python3

import collections
import subprocess

def get_graph_and_depths():
  graph = {}
  depth = {}
  p = subprocess.Popen(['git', 'log', '--format=%H %P'],
                       stdout=subprocess.PIPE, universal_newlines=True)
  for line in p.stdout:
    commits = line.split()
    graph[commits[0]] = commits[1:]

  waiting = collections.defaultdict(set)
  ready = set()
  for commit, parents in graph.items():
    if parents:
      for parent in parents:
        waiting[parent].add(commit)
    else:
      ready.add(commit)

  while ready:
    commit = ready.pop()
    parents = graph[commit]
    depth[commit] = 1 + max((depth[p] for p in parents), default=0)
    for other in waiting[commit]:
      parents = graph[other]
      if all(p in depth for p in parents):
        ready.add(other)

  return graph, depth

graph, depth = get_graph_and_depths()
for commit, d in depth.items():
  print("%5d %s" % (d, commit))

'''
    - Minimum number of unique commits to either side
    - Total number of diverging commits (or divide by 2 to get average)
    - What is the longest sequence of non-merge commits merged? (Use for rebase)
'''  

class AncestryGraph(object):
  """
  A class that maintains a direct acycle graph of commits for the purpose of
  determining if one commit is the ancestor of another.
  """

  def __init__(self):
    self.cur_value = 0

    # A mapping from the external identifers given to us to the simple integers
    # we use in self.graph
    self.value = {}

    # A tuple of (depth, list-of-ancestors).  Values and keys in this graph are
    # all integers from the self.value dict.  The depth of a commit is one more
    # than the max depth of any of its ancestors.
    self.graph = {}

  def record_external_commits(self, external_commits):
    """
    Record in graph that each commit in external_commits exists, and is
    treated as a root commit with no parents.
    """
    for c in external_commits:
      if c not in self.value:
        self.cur_value += 1
        self.value[c] = self.cur_value
        self.graph[self.cur_value] = (1, [])

  def add_commit_and_parents(self, commit, parents):
    """
    Record in graph that commit has the given parents.  parents _MUST_ have
    been first recorded.  commit _MUST_ not have been recorded yet.
    """
    assert all(p in self.value for p in parents)
    assert commit not in self.value

    # Get values for commit and parents
    self.cur_value += 1
    self.value[commit] = self.cur_value
    graph_parents = [self.value[x] for x in parents]

    # Determine depth for commit, then insert the info into the graph
    depth = 1
    if parents:
      depth += max(self.graph[p][0] for p in graph_parents)
    self.graph[self.cur_value] = (depth, graph_parents)

  def is_ancestor(self, possible_ancestor, check):
    """
    Return whether possible_ancestor is an ancestor of check
    """
    a, b = self.value[possible_ancestor], self.value[check]
    a_depth = self.graph[a][0]
    ancestors = [b]
    visited = set()
    while ancestors:
      ancestor = ancestors.pop()
      if ancestor in visited:
        continue
      visited.add(ancestor)
      depth, more_ancestors = self.graph[ancestor]
      if ancestor == a:
        return True
      elif depth <= a_depth:
        continue
      ancestors.extend(more_ancestors)
    return False

class RepoAnalyze(object):

  @staticmethod
  def setup_or_update_rename_history(stats, commit, oldname, newname):
    rename_commits = stats['rename_history'].get(oldname, set())
    rename_commits.add(commit)
    stats['rename_history'][oldname] = rename_commits

  @staticmethod
  def handle_renames(stats, commit, change_types, filenames):
    for index, change_type in enumerate(change_types):
      if change_type == ord(b'R'):
        oldname, newname = filenames[index], filenames[-1]
        RepoAnalyze.setup_equivalence_for_rename(stats, oldname, newname)
        RepoAnalyze.setup_or_update_rename_history(stats, commit,
                                                   oldname, newname)

  @staticmethod
  def handle_file(stats, graph, commit, modes, shas, filenames):
    mode, sha, filename = modes[-1], shas[-1], filenames[-1]

    # Figure out kind of deletions to undo for this file, and update lists
    # of all-names-by-sha and all-filenames
    delmode = 'tree_deletions'
    if mode != b'040000':
      delmode = 'file_deletions'
      stats['names'][sha].add(filename)
      stats['allnames'].add(filename)

    # If the file (or equivalence class of files) was recorded as deleted,
    # clearly it isn't anymore
    equiv = RepoAnalyze.equiv_class(stats, filename)
    for f in equiv:
      stats[delmode].pop(f, None)

    # If we get a modify/add for a path that was renamed, we may need to break
    # the equivalence class.  However, if the modify/add was on a branch that
    # doesn't have the rename in its history, we are still okay.
    need_to_break_equivalence = False
    if equiv[-1] != filename:
      for rename_commit in stats['rename_history'][filename]:
        if graph.is_ancestor(rename_commit, commit):
          need_to_break_equivalence = True

    if need_to_break_equivalence:
      for f in equiv:
        if f in stats['equivalence']:
          del stats['equivalence'][f]

  @staticmethod
  def analyze_commit(stats, graph, commit, parents, date, file_changes):
    graph.add_commit_and_parents(commit, parents)
    for change in file_changes:
      modes, shas, change_types, filenames = change
      if len(parents) == 1 and change_types.startswith(b'R'):
        change_types = b'R'  # remove the rename score; we don't care
      if modes[-1] == b'160000':
        continue
      elif modes[-1] == b'000000':
        # Track when files/directories are deleted
        for f in RepoAnalyze.equiv_class(stats, filenames[-1]):
          if any(x == b'040000' for x in modes[0:-1]):
            stats['tree_deletions'][f] = date
          else:
            stats['file_deletions'][f] = date
      elif change_types.strip(b'AMT') == b'':
        RepoAnalyze.handle_file(stats, graph, commit, modes, shas, filenames)
      elif modes[-1] == b'040000' and change_types.strip(b'RAM') == b'':
        RepoAnalyze.handle_file(stats, graph, commit, modes, shas, filenames)
      elif change_types.strip(b'RAM') == b'':
        RepoAnalyze.handle_file(stats, graph, commit, modes, shas, filenames)
        RepoAnalyze.handle_renames(stats, commit, change_types, filenames)
      else:
        raise SystemExit(_("Unhandled change type(s): %(change_type)s "
                           "(in commit %(commit)s)")
                         % ({'change_type': change_types, 'commit': commit})
                         ) # pragma: no cover

  @staticmethod
  def gather_data(args):
    unpacked_size, packed_size = GitUtils.get_blob_sizes()
    stats = {'names': collections.defaultdict(set),
             'allnames' : set(),
             'file_deletions': {},
             'tree_deletions': {},
             'equivalence': {},
             'rename_history': collections.defaultdict(set),
             'unpacked_size': unpacked_size,
             'packed_size': packed_size,
             'num_commits': 0}

    # Setup the rev-list/diff-tree process
    commit_parse_progress = ProgressWriter()
    num_commits = 0
    cmd = ('git rev-list --topo-order --reverse {}'.format(' '.join(args.refs)) +
           ' | git diff-tree --stdin --always --root --format=%H%n%P%n%cd' +
           ' --date=short -M -t -c --raw --combined-all-paths')
    dtp = subproc.Popen(cmd, shell=True, bufsize=-1, stdout=subprocess.PIPE)
    f = dtp.stdout
    line = f.readline()
    if not line:
      raise SystemExit(_("Nothing to analyze; repository is empty."))
    cont = bool(line)
    graph = AncestryGraph()
    while cont:
      commit = line.rstrip()
      parents = f.readline().split()
      date = f.readline().rstrip()

      # We expect a blank line next; if we get a non-blank line then
      # this commit modified no files and we need to move on to the next.
      # If there is no line, we've reached end-of-input.
      line = f.readline()
      if not line:
        cont = False
      line = line.rstrip()

      # If we haven't reached end of input, and we got a blank line meaning
      # a commit that has modified files, then get the file changes associated
      # with this commit.
      file_changes = []
      if cont and not line:
        cont = False
        for line in f:
          if not line.startswith(b':'):
            cont = True
            break
          n = 1+max(1, len(parents))
          assert line.startswith(b':'*(n-1))
          relevant = line[n-1:-1]
          splits = relevant.split(None, n)
          modes = splits[0:n]
          splits = splits[n].split(None, n)
          shas = splits[0:n]
          splits = splits[n].split(b'\t')
          change_types = splits[0]
          filenames = [PathQuoting.dequote(x) for x in splits[1:]]
          file_changes.append([modes, shas, change_types, filenames])

      # Analyze this commit and update progress
      RepoAnalyze.analyze_commit(stats, graph, commit, parents, date,
                                 file_changes)
      num_commits += 1
      commit_parse_progress.show(_("Processed %d commits") % num_commits)

    # Show the final commits processed message and record the number of commits
    commit_parse_progress.finish()
    stats['num_commits'] = num_commits

    # Close the output, ensure rev-list|diff-tree pipeline completed successfully
    dtp.stdout.close()
    if dtp.wait():
      raise SystemExit(_("Error: rev-list|diff-tree pipeline failed; see above.")) # pragma: no cover

    return stats
