# Fixes I've had to do to get this working
- Follow this answer to be able to use livereload: https://stackoverflow.com/a/65547010/2434460
- Had to add `github: [metadata]` to the _config.yml file to suppress that Github API metadata not found message
- Had to remove `relative_permalinks: true` from the _config.yml we get from Hyde