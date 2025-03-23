module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2, 
      'always', 
      ['feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore']
    ],
    'scope-enum': [
      2,
      'always',
      ['analyzer', 'visualizer', 'ui', 'utils', 'config', 'report', 'core', 'data', 'docs','parking-doc', 'test', 'worker',]
    ],
    'scope-empty': [2, 'never'],
    'subject-case': [2, 'never', ['start-case', 'pascal-case']],
    'subject-min-length': [2, 'always', 5],
    'body-max-line-length': [1, 'always', 100],
    'footer-leading-blank': [1, 'always']
  }
};