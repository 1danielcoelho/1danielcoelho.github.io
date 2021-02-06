# TODO
- Actually write some stuff
- Remove lorem ipsum stuff everywhere
- Remember that I can do this:
<p class="message">
  Hey there! This page is included as an example. Feel free to customize it for your own use upon downloading. Carry on!
</p>

# Fixes I've had to do to get this working
- Follow this answer to be able to use livereload: https://stackoverflow.com/a/65547010/2434460
- Had to add `github: [metadata]` to the _config.yml file to suppress that Github API metadata not found message
- Had to remove `relative_permalinks: true` from the _config.yml we get from Hyde
- Had to change "{{ site.baseurl }}public/css/syntax.css" css filepaths to just "/public/css/syntax.css", so that they're root relative and it doesn't try loading them from something like "about/public/css/syntax.css" instead